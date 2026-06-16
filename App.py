from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import bookings, services, auth, payments, admin
from contextlib import asynccontextmanager
from database import init_db  

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
    # allow all origins during local development (adjust in production)
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bookings.router, prefix="/bookings")
app.include_router(services.router, prefix="/services")
app.include_router(auth.router, prefix="/auth")
app.include_router(payments.router, prefix="/payments")
app.include_router(admin.router, prefix="/admin")
