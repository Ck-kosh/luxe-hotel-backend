from sqlalchemy.orm import Session
from main import SessionLocal, Room, engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

def seed():
    db = SessionLocal()
    
    # Check if we already have rooms
    if db.query(Room).count() > 0:
        print("Database already seeded.")
        return

    sample_rooms = [
        Room(name="Deluxe Ocean View", bedrooms=1, internet=True, price=15000.0, total_quantity=5, available_quantity=5),
        Room(name="Family Suite", bedrooms=2, internet=True, price=25000.0, total_quantity=3, available_quantity=3),
        Room(name="Standard Room", bedrooms=1, internet=False, price=8000.0, total_quantity=10, available_quantity=10),
        Room(name="Penthouse", bedrooms=3, internet=True, price=50000.0, total_quantity=1, available_quantity=1),
    ]

    db.add_all(sample_rooms)
    db.commit()
    print("Database seeded successfully with sample rooms.")
    db.close()

if __name__ == "__main__":
    seed()