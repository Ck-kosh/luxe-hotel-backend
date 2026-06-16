from fastapi.testclient import TestClient
from APP import app

client = TestClient(app)


def test_get_requests():
    response = client.get("/services/services/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "All service requests"
    }


def test_create_request():
    response = client.post("/services/services/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "New service request created"
    }


def test_room_service():
    response = client.get(
        "/services/services/room-service"
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Room service"
    }


def test_housekeeping():
    response = client.get(
        "/services/services/housekeeping"
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Housekeeping"
    }


def test_amenities():
    response = client.get(
        "/services/services/amenities"
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Amenities"
    }


def test_request_history():
    response = client.get(
        "/services/services/request-history"
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Request History"
    }


def test_get_single_request():
    response = client.get(
        "/services/services/1"
    )

    assert response.status_code == 200

    assert response.json() == {
        "id": 1,
        "message": "Request details"
    }


def test_update_request():
    response = client.put(
        "/services/services/1",
        json={
            "status": "Completed"
        }
    )

    assert response.status_code == 200

    assert response.json() == {
        "message": "Request updated successfully",
        "request_id": 1,
        "new_status": "Completed"
    }