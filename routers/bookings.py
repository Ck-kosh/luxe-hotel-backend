from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sqlite3

router = APIRouter()

class BookingUpdate(BaseModel):
    status: str

def get_db():
    conn = sqlite3.connect('hotel.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_name TEXT NOT NULL,
            room_number TEXT NOT NULL,
            check_in TEXT,
            check_out TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')
    if conn.execute('SELECT COUNT(*) FROM bookings').fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO bookings (guest_name, room_number, check_in, check_out, status) VALUES (?,?,?,?,?)",
            [('Elias KOsh', 'Deluxe 201', '2026-04-15', '2026-04-18', 'confirmed'),
             ('Fidelis Njenga', 'Suite 305', '2026-04-16', '2026-04-20', 'pending')]
        )
    conn.commit()
    conn.close()

@router.get("/")
def get_bookings():
    conn = get_db()
    rows = conn.execute("SELECT * FROM bookings").fetchall()
    conn.close()
    return [dict(row) for row in rows]

@router.patch("/{booking_id}")
def update_booking(booking_id: int, update: BookingUpdate):
    conn = get_db()
    cur = conn.execute("UPDATE bookings SET status=? WHERE id=?", (update.status, booking_id))
    conn.commit()

    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Booking not found")
    conn.close()
    return {"success": True, "id": booking_id, "status": update.status}