from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_db

router = APIRouter(prefix="/bookings", tags=["bookings"])


class BookingCreate(BaseModel):
    guest_name: str
    email: str
    phone: str
    room_number: int
    check_in: str  # "2026-06-25"
    check_out: str
    guests: int = 1

class BookingResponse(BookingCreate):
    id: int
    status: str

    class Config:
        orm_mode = True

@router.post("/", response_model=BookingResponse)
def create_booking(booking: BookingCreate, db = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO bookings (guest_name, email, phone, room_number, check_in, check_out, guests, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            booking.guest_name,
            booking.email,
            booking.phone,
            booking.room_number,
            booking.check_in,
            booking.check_out,
            booking.guests,
            "pending",
        ),
    )
    db.commit()
    booking_id = cursor.lastrowid
    row = db.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    db.close()
    return dict(row)

@router.get("/", response_model=list[BookingResponse])
def get_bookings(db = Depends(get_db)):
    rows = db.execute("SELECT * FROM bookings ORDER BY check_in DESC").fetchall()
    db.close()
    return [dict(r) for r in rows]

@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: int, db = Depends(get_db)):
    row = db.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    db.close()
    if not row:
        raise HTTPException(status_code=404, detail="Booking not found")
    return dict(row)

@router.patch("/{booking_id}")
def update_booking(booking_id: int, status: str, db = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("UPDATE bookings SET status = ? WHERE id = ?", (status, booking_id))
    db.commit()
    db.close()
    return {"message": "Booking updated"}
