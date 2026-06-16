# M-Pesa STK Push Integration Guide

## Backend Endpoints

### 1. Initiate STK Push Payment
**Endpoint:** `POST /payments/stk-push`

**Request Body:**
```json
{
  "phone_number": "254712345678",  // Kenya format or international
  "amount": 1000,                   // Amount in KES
  "booking_id": 1,                  // Booking ID from database
  "user_id": 1,                     // User ID from database
  "account_reference": "LuxeHotel", // Optional - reference
  "transaction_description": "Hotel Booking Payment"  // Optional
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "STK Push sent successfully",
  "merchant_request_id": "15589-3954156-1",
  "checkout_request_id": "ws_CO_20200316191112233317",
  "customer_message": "Enter your M-Pesa PIN to complete this transaction."
}
```

**Response (Failure):**
```json
{
  "success": false,
  "message": "Error description",
  "merchant_request_id": null,
  "checkout_request_id": null,
  "customer_message": "Error message from M-Pesa"
}
```

---

### 2. Check Payment Status
**Endpoint:** `GET /payments/status/{checkout_request_id}`

Use the `checkout_request_id` from the STK push response to poll payment status.

**Response:**
```json
{
  "payment_id": 1,
  "status": "Completed",  // Or: "Initiated", "Pending", "Failed"
  "merchant_request_id": "15589-3954156-1",
  "checkout_request_id": "ws_CO_20200316191112233317"
}
```

---

## Frontend Implementation Example

### React/Vue Component Example

```javascript
// Step 1: Send STK Push Request
async function initiatePayment(phoneNumber, amount, bookingId, userId) {
  try {
    const response = await fetch('http://localhost:8000/payments/stk-push', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        phone_number: phoneNumber,
        amount: amount,
        booking_id: bookingId,
        user_id: userId,
      })
    });

    const data = await response.json();

    if (data.success) {
      console.log('STK Push sent:', data);
      return data.checkout_request_id;  // Save this for status polling
    } else {
      console.error('Payment failed:', data.message);
      return null;
    }
  } catch (error) {
    console.error('Error initiating payment:', error);
    return null;
  }
}

// Step 2: Poll Payment Status
async function pollPaymentStatus(checkoutRequestId, maxAttempts = 30) {
  let attempts = 0;
  const pollInterval = setInterval(async () => {
    attempts++;
    
    try {
      const response = await fetch(
        `http://localhost:8000/payments/status/${checkoutRequestId}`
      );
      const data = await response.json();

      console.log('Payment status:', data.status);

      if (data.status === 'Completed') {
        clearInterval(pollInterval);
        console.log('Payment successful!');
        // Update UI, redirect, etc.
        return true;
      } else if (data.status === 'Failed') {
        clearInterval(pollInterval);
        console.error('Payment failed');
        return false;
      }

      if (attempts >= maxAttempts) {
        clearInterval(pollInterval);
        console.log('Polling timeout');
        return null;
      }
    } catch (error) {
      console.error('Error checking status:', error);
    }
  }, 2000);  // Poll every 2 seconds
}

// Usage Example
async function handlePaymentClick() {
  const checkoutId = await initiatePayment(
    '254712345678',  // Customer phone
    5000,            // Amount
    1,               // Booking ID
    1                // User ID
  );

  if (checkoutId) {
    pollPaymentStatus(checkoutId);
  }
}
```

---

## Important Notes

### Phone Number Format
- **Accepted formats:**
  - `254712345678` (international E.164)
  - `0712345678` (local Kenya format - will be converted)
  - `+254712345678` (with plus sign)

### Testing
- Use **Sandbox/Staging** credentials from your `.env`
- Test phone numbers: `254708374149`, `254701203456`
- M-Pesa simulator: https://sandbox.safaricom.co.ke/

### Production Migration
1. Update M-Pesa endpoints from sandbox to production URLs
2. Update CONSUMER_KEY and CONSUMER_SECRET in `.env`
3. Update CALLBACK_URL to your production domain
4. Test thoroughly before going live

### Error Handling
- **Network errors:** Retry with exponential backoff
- **Invalid phone:** Validate format before sending
- **Timeout:** Set reasonable poll timeout (60 seconds)
- **User cancels:** Payment status will show "Failed"

---

## Database Schema

Payment records are stored with:
- `id`: Payment ID
- `user_id`: User who made payment
- `booking_id`: Associated booking
- `amount`: Payment amount (KES)
- `phone_number`: Customer's phone number
- `status`: Payment status (Initiated, Completed, Failed, Pending)
- `merchant_request_id`: M-Pesa reference
- `checkout_request_id`: M-Pesa checkout request ID
- `result_code`: M-Pesa result code
- `result_desc`: M-Pesa result description
- `created_at`: When payment was initiated
- `updated_at`: Last update timestamp

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No access token in response" | Check CONSUMER_KEY and CONSUMER_SECRET |
| "STK Push sent but no prompt on phone" | Verify phone number format (must be 254XXXXXXXXX) |
| "Callback not received" | Ensure CALLBACK_URL is publicly accessible (use ngrok for testing) |
| "CORS error" | Backend CORS is configured for localhost:5173/3000/5174 |
| "Payment stuck on Initiated" | Check if customer entered correct PIN or cancelled |

