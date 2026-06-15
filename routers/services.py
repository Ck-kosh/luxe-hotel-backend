from fastapi import APIRouter
from pydantic import BaseModel
from routers.service_request import ServiceRequest
from routers.service_schema import ServiceCreate

router = APIRouter(
    prefix="/services",
    tags=["Guest Services"],
)

class UpdateRequest(BaseModel):
    status: str

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
    return {"message": "Amenities"}

@router.get("/request-history")
def request_history():
    return {"message": "Request History"}

@router.get("/{request_id}")
def get_request(request_id: int):
    return {
        "id": request_id,
        "message": "Request details"
    }
    
@router.put("/{request_id}")
def update_request(
    request_id: int,
    request: UpdateRequest
):
    return {
        "message": "Request updated successfully",
        "request_id": request_id,
        "new_status": request.status
    }
