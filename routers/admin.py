from fastapi import APIRouter
from pydantic import BaseModel
from database import get_db

router = APIRouter()

class StatusUpdate(BaseModel):
    status: str

@router.get("/bookings")
def get_all_bookings():
    conn = get_db()
    rows = conn.execute("SELECT * FROM bookings ORDER BY check_in DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.get("/services")
def get_all_requests():
    conn = get_db()
    rows = conn.execute("SELECT * FROM service_requests ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.patch("/services/{id}/status")
def update_request_status(id: int, update: StatusUpdate):
    conn = get_db()
    conn.execute("UPDATE service_requests SET status=? WHERE id=?", (update.status, id))
    conn.commit()
    conn.close()
    return {"message": f"Request {id} updated to {update.status}"}

@router.get("/stats")
def get_admin_stats():
    conn = get_db()
    cur = conn.cursor()

    total_bookings = cur.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
    pending_requests = cur.execute("SELECT COUNT(*) FROM service_requests WHERE status='pending'").fetchone()[0]

    cur.execute("SELECT SUM(total_quantity - available_quantity) FROM rooms")
    occupied_rooms = cur.fetchone()[0] or 0

    cur.execute("SELECT SUM(total_quantity) FROM rooms")
    total_rooms = cur.fetchone()[0] or 1

    occupancy = round((occupied_rooms / total_rooms) * 100, 1) if total_rooms > 0 else 0
    conn.close()

    return {
        "total_bookings": total_bookings,
        "occupancy": occupancy,
        "pending_requests": pending_requests
    }