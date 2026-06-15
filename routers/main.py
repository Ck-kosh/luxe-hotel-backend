import requests
import base64
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship

# --- Database Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./hotel.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- SQLAlchemy Models ---
class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    bedrooms = Column(Integer, nullable=True)
    internet = Column(Boolean, default=False)
    price = Column(Float)
    total_quantity = Column(Integer, default=1)
    available_quantity = Column(Integer, default=1)

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    total_price = Column(Float)
    status = Column(String, default="pending") # pending, confirmed, paid, failed
    checkout_request_id = Column(String, nullable=True) # To track M-Pesa transaction
    items = relationship("BookingItem", back_populates="booking")

class BookingItem(Base):
    __tablename__ = "booking_items"
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"))
    room_id = Column(Integer, ForeignKey("rooms.id"))
    quantity = Column(Integer)
    price_per_night = Column(Float)
    booking = relationship("Booking", back_populates="items")
    room = relationship("Room")

Base.metadata.create_all(bind=engine)

# --- Pydantic Schemas ---
class RoomResponse(BaseModel):
    id: int
    name: str
    bedrooms: Optional[int]
    internet: bool
    price: float
    available_quantity: int
    class Config:
        from_attributes = True

class BookingItemCreate(BaseModel):
    room_id: int
    quantity: int

class BookingCreate(BaseModel):
    items: List[BookingItemCreate]

class BookingResponse(BaseModel):
    id: int
    total_price: float
    status: str
    class Config:
        from_attributes = True

class PaymentRequest(BaseModel):
    booking_id: int
    phone_number: str # Format: 2547XXXXXXXX

# --- Daraja Configuration ---
CONSUMER_KEY = "HXGGFfsfUMMm72MknK3XGRgg93s92Apb2aJuGeAdBF2tek9T"
CONSUMER_SECRET = "FDTGnmuBkvtsp2ejTaGeM4c0q2aEpb94eBNxD50h1BMKy8fCvXc7u67HxGhuEvYz"
BUSINESS_SHORTCODE = "174379"
PASSKEY = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
CALLBACK_URL = "https://your-ngrok-url.ngrok-free.app/mpesa/callback" # UPDATE THIS

# --- FastAPI App ---
app = FastAPI(title="Hotel Booking & M-Pesa API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Helper Functions ---
def get_access_token():
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    r = requests.get(api_url, auth=(CONSUMER_KEY, CONSUMER_SECRET))
    return r.json()['access_token']

def generate_password(shortcode, passkey, timestamp):
    data_to_encode = shortcode + passkey + timestamp
    return base64.b64encode(data_to_encode.encode()).decode('utf-8')

# --- APIs ---
@app.get("/rooms/", response_model=List[RoomResponse])
def get_rooms(db: Session = Depends(get_db)):
    return db.query(Room).all()

@app.post("/bookings/", response_model=BookingResponse)
def create_booking(booking_data: BookingCreate, db: Session = Depends(get_db)):
    total_price = 0
    items_to_add = []
    
    for item in booking_data.items:
        room = db.query(Room).filter(Room.id == item.room_id).first()
        if not room or room.available_quantity < item.quantity:
            raise HTTPException(status_code=400, detail=f"Room {item.room_id} unavailable")
        
        total_price += room.price * item.quantity
        items_to_add.append(item)

    db_booking = Booking(total_price=total_price, status="pending")
    db.add(db_booking)
    db.flush()

    for item in items_to_add:
        room = db.query(Room).filter(Room.id == item.room_id).first()
        room.available_quantity -= item.quantity
        db.add(BookingItem(booking_id=db_booking.id, room_id=item.room_id, quantity=item.quantity, price_per_night=room.price))

    db.commit()
    db.refresh(db_booking)
    return db_booking

@app.post("/pay/")
def initiate_payment(payment_req: PaymentRequest, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == payment_req.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    access_token = get_access_token()
    api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": f"Bearer {access_token}"}
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = generate_password(BUSINESS_SHORTCODE, PASSKEY, timestamp)

    payload = {
        "BusinessShortCode": BUSINESS_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(booking.total_price),
        "PartyA": payment_req.phone_number,
        "PartyB": BUSINESS_SHORTCODE,
        "PhoneNumber": payment_req.phone_number,
        "CallBackURL": CALLBACK_URL,
        "AccountReference": f"Booking_{booking.id}",
        "TransactionDesc": "Hotel Booking Payment"
    }

    response = requests.post(api_url, json=payload, headers=headers)
    res_data = response.json()
    
    if "CheckoutRequestID" in res_data:
        booking.checkout_request_id = res_data["CheckoutRequestID"]
        db.commit()
        
    return res_data

@app.post("/mpesa/callback")
async def mpesa_callback(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    stk_callback = data['Body']['stkCallback']
    checkout_id = stk_callback['CheckoutRequestID']
    result_code = stk_callback['ResultCode']
    
    booking = db.query(Booking).filter(Booking.checkout_request_id == checkout_id).first()
    if booking:
        booking.status = "paid" if result_code == 0 else "failed"
        db.commit()
        
    return {"ResultCode": 0, "ResultDesc": "Accepted"}