from sqlalchemy import Column, Integer, String
from database import Base

class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id = Column(Integer, primary_key=True, index=True)
    guest_name = Column(String)
    service_type = Column(String)
    description = Column(String)
    status = Column(String, default="Pending")