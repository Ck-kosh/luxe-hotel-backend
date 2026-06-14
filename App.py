from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import bookings, service_requests, auth_payment, admin
from database import init_db  # Import the init function

app = FastAPI(title="Luxe Hotel API", version="1.0.0")

# Create tables automatically when server starts
@app.on_event("startup")
def startup_event():
    init_db()
    print("✅ Database tables ready in bookings.db")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all 4 member routers
app.include_router(bookings.router, prefix="/bookings", tags=["1. Bookings - Member 1"])
app.include_router(service_requests.router, prefix="/service-requests", tags=["2. Services - Member 2"])
app.include_router(auth_payment.router, prefix="/auth", tags=["3. Auth/Payment - Member 3"])
app.include_router(admin.router, prefix="/admin", tags=["4. Admin - Member 4"])

@app.get("/")
def home():
    return {"message": "Luxe Hotel API running. Docs at /docs"}