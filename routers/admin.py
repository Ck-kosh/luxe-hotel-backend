from fastapi import APIRouter
from database import get_db

router = APIRouter()

@router.get("/bookings")
def get_all_bookings():
    conn = get_db()
    rows = conn.execute("SELECT * FROM bookings ORDER BY check_in DESC").fetchall()
    return [dict(r) for r in rows]

@router.get("/service-requests")
def get_all_requests():
    conn = get_db()
    rows = conn.execute("SELECT * FROM service_requests ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]

@router.patch("/service-requests/{id}/status")
def update_request_status(id: int, status: str):
    conn = get_db()
    conn.execute("UPDATE service_requests SET status=? WHERE id=?", (status, id))
    conn.commit()
    return {"message": f"Request {id} updated to {status}"}

@router.get("/contact-messages")
def get_contact_messages():
    conn = get_db()
    rows = conn.execute("SELECT * FROM contact_messages ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]

@router.get("/reports")
def get_reports():
    conn = get_db()
    total_bookings = conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
    pending_requests = conn.execute("SELECT COUNT(*) FROM service_requests WHERE status='Pending'").fetchone()[0]
    return {
        "total_bookings": total_bookings,
        "pending_service_requests": pending_requests
    }