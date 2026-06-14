from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3

app = FastAPI()

# CORS - lets your React frontend talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://192.168.1.108:5173", "*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
conn = sqlite3.connect("bookings.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guest_name TEXT,
    room_number INTEGER,
    check_in TEXT,
    check_out TEXT
)
""")
conn.commit()

# Model for validation
class Booking(BaseModel):
    guest_name: str
    room_number: int
    check_in: str
    check_out: str

class BookingUpdate(BaseModel):
    guest_name: str | None = None
    room_number: int | None = None
    check_in: str | None = None
    check_out: str | None = None

# Routes
@app.get("/")
def home():
    return {"message": "Hotel API running. Go to /docs to test"}

@app.get("/bookings")
def get_bookings():
    cursor.execute("SELECT id, name, room, check_in FROM bookings")
    rows = cursor.fetchall()
    return [{"id": r[0], "guest_name": r[1], "room_number": r[2], "check_in": r[3]} for r in rows]

@app.post("/bookings")
def create_booking(booking: Booking):
    cursor.execute(
        "INSERT INTO bookings (guest_name, room_number, check_in, check_out) VALUES (?,?,?)",
        (booking.guest_name, booking.room_number, booking.check_in, booking.check_out)
    )
    conn.commit()
    return {"id": cursor.lastrowid, **booking.dict()}

@app.patch("/bookings/{booking_id}")
def update_booking(booking_id: int, booking: BookingUpdate):
    # Build dynamic update
    fields = {k: v for k, v in booking.dict().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    query = f"UPDATE bookings SET {', '.join([f'{k}=?' for k in fields.keys()])} WHERE id=?"
    cursor.execute(query, list(fields.values()) + [booking_id])
    conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"message": "Booking updated"}

@app.delete("/bookings/{booking_id}")
def delete_booking(booking_id: int):
    cursor.execute("DELETE FROM bookings WHERE id=?", (booking_id,))
    conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"message": "Booking deleted"}