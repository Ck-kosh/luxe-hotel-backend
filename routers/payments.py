from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import requests
import base64
from datetime import datetime
import sqlite3
import os
from dotenv import load_dotenv
import logging

load_dotenv()

router = APIRouter()

# M-Pesa configuration
MPESA_CONSUMER_KEY = os.getenv("CONSUMER_KEY")
MPESA_CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
MPESA_BUSINESS_SHORTCODE = os.getenv("BUSINESS_SHORTCODE")
MPESA_PASSKEY = os.getenv("PASSKEY")
MPESA_CALLBACK_URL = os.getenv("CALLBACK_URL")

# M-Pesa endpoints
MPESA_OAUTH_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
MPESA_STK_PUSH_URL = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
MPESA_CHECK_STATUS_URL = "https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query"

logger = logging.getLogger(__name__)

# Request/Response Models
class STKPushRequest(BaseModel):
    phone_number: str
    amount: int
    booking_id: int
    user_id: int
    account_reference: str = "LuxeHotel"
    transaction_description: str = "Hotel Booking Payment"

class STKPushResponse(BaseModel):
    success: bool
    message: str
    merchant_request_id: str = None
    checkout_request_id: str = None
    customer_message: str = None

class PaymentStatusResponse(BaseModel):
    payment_id: int
    status: str
    merchant_request_id: str = None
    checkout_request_id: str = None

class MPesaCallbackRequest(BaseModel):
    Body: dict

# Helper function to get M-Pesa access token
def get_access_token():
    """Get M-Pesa API access token"""
    try:
        auth_string = f"{MPESA_CONSUMER_KEY}:{MPESA_CONSUMER_SECRET}"
        auth_bytes = auth_string.encode('utf-8')
        auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
        
        headers = {
            "Authorization": f"Basic {auth_base64}"
        }
        
        response = requests.get(MPESA_OAUTH_URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        token = response.json().get('access_token')
        if not token:
            raise Exception("No access token in response")
        return token
    except Exception as e:
        logger.error(f"Error getting M-Pesa access token: {str(e)}")
        raise

# Helper function to generate timestamp
def get_timestamp():
    """Generate M-Pesa timestamp"""
    return datetime.now().strftime("%Y%m%d%H%M%S")

# Helper function to generate password
def generate_password(business_code, passkey, timestamp):
    """Generate M-Pesa password"""
    data_string = f"{business_code}{passkey}{timestamp}"
    encoded = base64.b64encode(data_string.encode('utf-8')).decode('utf-8')
    return encoded

# STK Push endpoint
@router.post("/stk-push", response_model=STKPushResponse)
async def initiate_stk_push(request: STKPushRequest):
    """
    Initiate M-Pesa STK Push for payment
    Frontend expects: {success: bool, message: str, merchant_request_id, checkout_request_id, customer_message}
    """
    try:
        # Validate phone number (E.164 format expected)
        phone = request.phone_number.lstrip('+')
        if not phone.startswith('254'):
            phone = '254' + phone.lstrip('0')
        
        # Get access token
        access_token = get_access_token()
        
        # Generate timestamp and password
        timestamp = get_timestamp()
        password = generate_password(MPESA_BUSINESS_SHORTCODE, MPESA_PASSKEY, timestamp)
        
        # Prepare STK Push request body
        payload = {
            "BusinessShortCode": MPESA_BUSINESS_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": request.amount,
            "PartyA": phone,
            "PartyB": MPESA_BUSINESS_SHORTCODE,
            "PhoneNumber": phone,
            "CallBackURL": MPESA_CALLBACK_URL,
            "AccountReference": request.account_reference,
            "TransactionDesc": request.transaction_description
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Call M-Pesa API
        response = requests.post(
            MPESA_STK_PUSH_URL,
            json=payload,
            headers=headers,
            timeout=10
        )
        # Log Daraja response for debugging
        try:
            logger.info(f"Daraja response status: {response.status_code}")
            logger.info(f"Daraja response text: {response.text}")
        except Exception:
            pass
        response.raise_for_status()
        
        mpesa_response = response.json()
        
        # Save payment record to database
        conn = sqlite3.connect('bookings.db')
        c = conn.cursor()
        
        merchant_request_id = mpesa_response.get('MerchantRequestID', '')
        checkout_request_id = mpesa_response.get('CheckoutRequestID', '')
        
        c.execute("""
            INSERT INTO payments (user_id, booking_id, amount, phone_number, status, merchant_request_id, checkout_request_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (request.user_id, request.booking_id, request.amount, phone, 'Initiated', merchant_request_id, checkout_request_id))
        
        conn.commit()
        conn.close()
        
        # Return response for frontend
        if mpesa_response.get('ResponseCode') == '0':
            return STKPushResponse(
                success=True,
                message="STK Push sent successfully",
                merchant_request_id=merchant_request_id,
                checkout_request_id=checkout_request_id,
                customer_message=mpesa_response.get('CustomerMessage', '')
            )
        else:
            return STKPushResponse(
                success=False,
                message=mpesa_response.get('ResponseDescription', 'Failed to send STK Push'),
                customer_message=mpesa_response.get('CustomerMessage', '')
            )
    
    except Exception as e:
        logger.error(f"STK Push error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to initiate payment: {str(e)}"
        )

# M-Pesa Callback endpoint
@router.post("/callback")
async def mpesa_callback(request: MPesaCallbackRequest):
    """
    Handle M-Pesa callback after payment
    """
    try:
        body = request.Body
        stk_callback = body.get('stkCallback', {})
        
        merchant_request_id = stk_callback.get('MerchantRequestID')
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        result_code = stk_callback.get('ResultCode')
        result_description = stk_callback.get('ResultDesc', '')
        
        # Get callback items for additional details
        callback_items = stk_callback.get('CallbackMetadata', {}).get('Item', [])
        
        conn = sqlite3.connect('bookings.db')
        c = conn.cursor()
        
        # Update payment status
        if result_code == 0:  # Success
            status_value = 'Completed'
        else:
            status_value = 'Failed'
        
        c.execute("""
            UPDATE payments 
            SET status = ?, result_code = ?, result_desc = ?, updated_at = ?
            WHERE checkout_request_id = ?
        """, (status_value, result_code, result_description, datetime.now().isoformat(), checkout_request_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Payment callback processed: {checkout_request_id} - Status: {status_value}")
        
        return {"ResultCode": 0, "ResultDesc": "Callback processed successfully"}
    
    except Exception as e:
        logger.error(f"Callback processing error: {str(e)}")
        return {"ResultCode": 1, "ResultDesc": f"Error: {str(e)}"}

# Check payment status endpoint
@router.get("/status/{checkout_request_id}", response_model=PaymentStatusResponse)
async def check_payment_status(checkout_request_id: str):
    """
    Check payment status - Call this from frontend to poll payment status
    """
    try:
        conn = sqlite3.connect('bookings.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("""
            SELECT id, status, merchant_request_id, checkout_request_id 
            FROM payments 
            WHERE checkout_request_id = ?
        """, (checkout_request_id,))
        
        payment = c.fetchone()
        conn.close()
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        return PaymentStatusResponse(
            payment_id=payment['id'],
            status=payment['status'],
            merchant_request_id=payment['merchant_request_id'],
            checkout_request_id=payment['checkout_request_id']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking payment status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.post("/process")
def process_payment():
    """Legacy endpoint - use /stk-push instead"""
    return {"message": "Use /stk-push endpoint for payments"}

@router.get("/{payment_id}")
def get_payment(payment_id: int):
    """Get payment details endpoint"""
    try:
        conn = sqlite3.connect('bookings.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
        payment = c.fetchone()
        conn.close()
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        return dict(payment)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
