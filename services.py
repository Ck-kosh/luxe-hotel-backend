from fastapi import APIRouter

router = APIRouter(
    prefix="/services",
    tags=["Guest Services"],
)

@router.get("/")
def get_requests():
    return {"message": "All service requests"}

@router.post("/")
def create_request():
    return {"message": "New service request created"}

@router.get("/room-service")
def room_service():
    return {"message": "Room service"}

@router.get("/housekeeping")
def housekeeping():
    return {"message": "Housekeeping"}

@router.get("/amenities")
def amenities():
    return {"message": "amenities"}

