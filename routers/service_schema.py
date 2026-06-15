from pydantic import BaseModel

class ServiceCreate(BaseModel):
    guest_name: str
    service_type: str
    description: str

class ServiceUpdate(BaseModel):
    status: str