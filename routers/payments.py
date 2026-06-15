from fastapi import APIRouter

router = APIRouter()

@router.post("/process")
def process_payment():
    """Process payment endpoint"""
    return {"message": "Payment processing endpoint"}

@router.get("/{payment_id}")
def get_payment(payment_id: int):
    """Get payment details endpoint"""
    return {"payment_id": payment_id, "message": "Payment details"}
