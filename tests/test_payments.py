import asyncio
import os
import sys
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import routers.payments as payments


class AsyncDummyResponse:
    def __init__(self, json_data):
        self._json_data = json_data

    def json(self):
        return self._json_data

    def raise_for_status(self):
        return None


class TestPayments(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.prev_cwd = os.getcwd()
        os.chdir(self.tempdir.name)
        conn = sqlite3.connect("bookings.db")
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                booking_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                phone_number TEXT NOT NULL,
                status TEXT DEFAULT 'Pending',
                merchant_request_id TEXT,
                checkout_request_id TEXT,
                result_code TEXT,
                result_desc TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        conn.close()

    def tearDown(self):
        os.chdir(self.prev_cwd)
        self.tempdir.cleanup()

    def test_generate_password(self):
        actual = payments.generate_password("12345", "secret", "20260101120000")
        self.assertEqual(actual, "MTIzNDVzZWNyZXQyMDI2MDEwMTEyMDAwMA==")

    def test_get_timestamp_format(self):
        timestamp = payments.get_timestamp()
        self.assertEqual(len(timestamp), 14)
        self.assertTrue(timestamp.isdigit())

    @patch("routers.payments.requests.get")
    def test_get_access_token_success(self, get_mock):
        get_mock.return_value.json = lambda: {"access_token": "abc123"}
        get_mock.return_value.raise_for_status = lambda: None

        token = payments.get_access_token()
        self.assertEqual(token, "abc123")

    @patch("routers.payments.get_access_token")
    @patch("routers.payments.requests.post")
    def test_initiate_stk_push_success(self, post_mock, access_token_mock):
        access_token_mock.return_value = "token123"
        post_mock.return_value = AsyncDummyResponse(
            {
                "ResponseCode": "0",
                "MerchantRequestID": "mr123",
                "CheckoutRequestID": "cr123",
                "CustomerMessage": "Success",
            }
        )

        request = payments.STKPushRequest(
            phone_number="0712345678",
            amount=100,
            booking_id=1,
            user_id=42,
        )

        response = asyncio.run(payments.initiate_stk_push(request))
        self.assertTrue(response.success)
        self.assertEqual(response.checkout_request_id, "cr123")
        conn = sqlite3.connect("bookings.db")
        cursor = conn.cursor()
        cursor.execute("SELECT status, checkout_request_id FROM payments WHERE checkout_request_id = ?", ("cr123",))
        row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "Initiated")
        self.assertEqual(row[1], "cr123")

    def test_mpesa_callback_updates_payment(self):
        conn = sqlite3.connect("bookings.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO payments (user_id, booking_id, amount, phone_number, status, merchant_request_id, checkout_request_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (1, 2, 100.0, "254700000000", "Initiated", "mr123", "cr123"),
        )
        conn.commit()
        conn.close()

        payload = {
            "stkCallback": {
                "MerchantRequestID": "mr123",
                "CheckoutRequestID": "cr123",
                "ResultCode": 0,
                "ResultDesc": "The service request is processed successfully.",
                "CallbackMetadata": {"Item": []},
            }
        }

        response = asyncio.run(payments.mpesa_callback(payments.MPesaCallbackRequest(Body=payload)))
        self.assertEqual(response["ResultCode"], 0)

        conn = sqlite3.connect("bookings.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM payments WHERE checkout_request_id = ?", ("cr123",))
        row = cursor.fetchone()
        conn.close()
        self.assertEqual(row["status"], "Completed")

    def test_check_payment_status_not_found(self):
        with self.assertRaises(Exception) as ctx:
            asyncio.run(payments.check_payment_status("missing_id"))
        self.assertTrue("Payment not found" in str(ctx.exception))
