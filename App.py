from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel

app = FastAPI()

# 1. Database setup
DATABASE_URL = "sqlite:///./bookings.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Database table model
class BookingDB(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    room = Column(String)
    check_in = Column(String)

Base.metadata.create_all(bind=engine)

# 3. Pydantic model for API
class BookingCreate(BaseModel):
    name: str
    room: str
    check_in: str

# 4. Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 5. GET all bookings - now reads from DB
@app.get("/bookings")
def get_bookings(db: Session = Depends(get_db)):
    return db.query(BookingDB).all()

# 6. POST new booking - now saves to DB
@app.post("/bookings")
def create_booking(booking: BookingCreate, db: Session = Depends(get_db)):
    db_booking = BookingDB(**booking.dict())
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking



# PATCH = update booking
@app.patch("/bookings/{booking_id}")
def update_booking(booking_id: int, booking: BookingCreate, db: Session = Depends(get_db)):
    db_booking = db.query(BookingDB).filter(BookingDB.id == booking_id).first()
    if not db_booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    db_booking.name = booking.name
    db_booking.room = booking.room
    db_booking.check_in = booking.check_in
    db.commit()
    db.refresh(db_booking)
    return db_booking

# DELETE = cancel booking  
@app.delete("/bookings/{booking_id}")
def delete_booking(booking_id: int, db: Session = Depends(get_db)):
    db_booking = db.query(BookingDB).filter(BookingDB.id == booking_id).first()
    if not db_booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    db.delete(db_booking)
    db.commit()
    return {"message": f"Booking {booking_id} deleted"}