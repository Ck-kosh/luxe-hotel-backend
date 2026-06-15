import sqlite3
from database import DB_NAME, init_db

# Ensure tables exist
init_db()

def seed():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Check if we already have rooms
    c.execute("SELECT COUNT(*) FROM rooms")
    if c.fetchone()[0] > 0:
        print("Database already seeded.")
        conn.close()
        return

    sample_rooms = [
        ("Deluxe Ocean View", 1, True, 15000.0, 5, 5),
        ("Family Suite", 2, True, 25000.0, 3, 3),
        ("Standard Room", 1, False, 8000.0, 10, 10),
        ("Penthouse", 3, True, 50000.0, 1, 1),
    ]

    c.executemany(
        "INSERT INTO rooms (name, bedrooms, internet, price, total_quantity, available_quantity) VALUES (?, ?, ?, ?, ?, ?)",
        sample_rooms
    )
    conn.commit()
    print("Database seeded successfully with sample rooms.")
    conn.close()

if __name__ == "__main__":
    seed()