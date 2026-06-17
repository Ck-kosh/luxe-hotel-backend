import os
import sys
import sqlite3
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database
from fastapi import HTTPException
from routers import bookings


class TestBookings(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.prev_cwd = os.getcwd()
        os.chdir(self.tempdir.name)
        database.DB_NAME = "bookings.db"
        database.init_db()

    def tearDown(self):
        os.chdir(self.prev_cwd)
        self.tempdir.cleanup()

    def test_create_and_get_booking(self):
        booking_data = bookings.BookingCreate(
            guest_name="Alice",
            email="alice@example.com",
            phone="254700000000",
            room_number=101,
            check_in="2026-06-25",
            check_out="2026-06-27",
            guests=2,
        )

        result = bookings.create_booking(booking_data, db=database.get_db())
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["guest_name"], "Alice")
        self.assertEqual(result["room_number"], 101)
        self.assertEqual(result["guests"], 2)

        fetched = bookings.get_booking(result["id"], db=database.get_db())
        self.assertEqual(fetched["id"], result["id"])
        self.assertEqual(fetched["email"], "alice@example.com")

        bookings_list = bookings.get_bookings(db=database.get_db())
        self.assertEqual(len(bookings_list), 1)
        self.assertEqual(bookings_list[0]["guest_name"], "Alice")

    def test_get_booking_not_found(self):
        with self.assertRaises(HTTPException) as ctx:
            bookings.get_booking(999, db=database.get_db())
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "Booking not found")

    def test_update_booking(self):
        booking_data = bookings.BookingCreate(
            guest_name="Bob",
            email="bob@example.com",
            phone="254700000001",
            room_number=102,
            check_in="2026-07-01",
            check_out="2026-07-05",
        )

        created = bookings.create_booking(booking_data, db=database.get_db())
        self.assertEqual(created["status"], "pending")

        response = bookings.update_booking(created["id"], "confirmed", db=database.get_db())
        self.assertEqual(response, {"message": "Booking updated"})

        updated = bookings.get_booking(created["id"], db=database.get_db())
        self.assertEqual(updated["status"], "confirmed")
