import asyncio
import base64
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import routers.main as main
from fastapi import HTTPException


class AsyncRequest:
    def __init__(self, payload):
        self._payload = payload

    async def json(self):
        return self._payload


class TestMain(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        main.engine = self.engine
        main.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        main.Base.metadata.create_all(bind=self.engine)

    def test_generate_password(self):
        expected = base64.b64encode("12345secret20260101120000".encode()).decode("utf-8")
        actual = main.generate_password("12345", "secret", "20260101120000")
        self.assertEqual(actual, expected)

    def test_create_booking_success(self):
        session = main.SessionLocal()
        room = main.Room(
            name="Test Room",
            bedrooms=1,
            internet=True,
            price=100.0,
            total_quantity=2,
            available_quantity=2,
        )
        session.add(room)
        session.commit()
        session.refresh(room)
        session.close()

        booking_data = main.BookingCreate(items=[main.BookingItemCreate(room_id=room.id, quantity=1)])
        db = main.SessionLocal()
        booking = main.create_booking(booking_data, db=db)
        self.assertEqual(booking.total_price, 100.0)
        self.assertEqual(booking.status, "pending")

        room_after = db.query(main.Room).filter(main.Room.id == room.id).first()
        self.assertEqual(room_after.available_quantity, 1)
        db.close()

    def test_create_booking_room_unavailable(self):
        booking_data = main.BookingCreate(items=[main.BookingItemCreate(room_id=999, quantity=1)])
        with self.assertRaises(HTTPException) as ctx:
            main.create_booking(booking_data, db=main.SessionLocal())
        self.assertEqual(ctx.exception.status_code, 400)

    @patch("routers.main.requests.get")
    @patch("routers.main.requests.post")
    def test_initiate_payment_updates_booking(self, post_mock, get_mock):
        get_mock.return_value.json = lambda: {"access_token": "token123"}
        get_mock.return_value.raise_for_status = lambda: None

        post_mock.return_value.json = lambda: {
            "CheckoutRequestID": "checkout123",
            "ResponseCode": "0",
            "MerchantRequestID": "merchant123",
        }
        post_mock.return_value.raise_for_status = lambda: None

        db = main.SessionLocal()
        booking = main.Booking(total_price=200.0, status="pending")
        db.add(booking)
        db.commit()
        db.refresh(booking)

        payment_req = main.PaymentRequest(booking_id=booking.id, phone_number="254700000000")
        response = main.initiate_payment(payment_req, db=db)
        self.assertEqual(response["CheckoutRequestID"], "checkout123")

        updated = db.query(main.Booking).filter(main.Booking.id == booking.id).first()
        self.assertEqual(updated.checkout_request_id, "checkout123")
        db.close()

    def test_mpesa_callback_updates_status(self):
        db = main.SessionLocal()
        booking = main.Booking(total_price=300.0, status="pending", checkout_request_id="cb123")
        db.add(booking)
        db.commit()
        db.refresh(booking)

        payload = {
            "Body": {
                "stkCallback": {
                    "CheckoutRequestID": "cb123",
                    "ResultCode": 0,
                }
            }
        }

        response = asyncio.run(main.mpesa_callback(AsyncRequest(payload), db=db))
        self.assertEqual(response, {"ResultCode": 0, "ResultDesc": "Accepted"})

        updated = db.query(main.Booking).filter(main.Booking.id == booking.id).first()
        self.assertEqual(updated.status, "paid")
        db.close()
