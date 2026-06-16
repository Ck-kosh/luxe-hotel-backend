import sys
import os
from unittest.mock import MagicMock

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
)

ROUTERS_PATH = os.path.join(PROJECT_ROOT, "routers")


sys.modules['models'] = MagicMock()

sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, ROUTERS_PATH)

from services import router

from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

app.include_router(router)

client = TestClient(app)


def test_get_requests():
    response = client.get("/services/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "All service requests"
    }


def test_create_request():
    response = client.post("/services/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "New service request created"
    }


def test_room_service():
    response = client.get("/services/room-service")
    assert response.status_code == 200


def test_housekeeping():
    response = client.get("/services/housekeeping")
    assert response.status_code == 200


def test_amenities():
    response = client.get("/services/amenities")
    assert response.status_code == 200


def test_request_history():
    response = client.get(
        "/services/request-history"
    )
    assert response.status_code == 200


def test_get_single_request():
    response = client.get("/services/1")

    assert response.status_code == 200

    assert response.json() == {
        "id": 1,
        "message": "Request details"
    }


def test_update_request():
    response = client.put(
        "/services/1",
        json={
            "status": "Completed"
        }
    )

    assert response.status_code == 200

    assert response.json() == {
        "message":
            "Request updated successfully",
        "request_id": 1,
        "new_status": "Completed"
    }