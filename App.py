from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import bookings, services, auth_payment, admin
from database import init_db  # Import the init function

app = FastAPI(title="Luxe Hotel API", version="1.0.0")

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("✅ Database tables ready in bookings.db")
    yield

app = FastAPI(title="Luxe Hotel API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all 4 member routers
app.include_router(bookings.router, prefix="/bookings")
app.include_router(services.router, prefix="/services")
app.include_router(auth_payment.router, prefix="/auth")
app.include_router(admin.router, prefix="/admin")

@app.get("/")
def home():
    return {"message": "Luxe Hotel API running. Docs at /docs"}