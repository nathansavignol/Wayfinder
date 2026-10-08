import os
import sys

# Ensure backend directory is in path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_us5_and_us6_acceptance_tests():
    print("\n--- Running US5 & US6 Acceptance Tests ---")

    # US5 - Test 1: POST /trips with valid payload -> 201 Created
    create_payload = {
        "title": "Summer in Kyoto",
        "destination": "Kyoto, Japan",
        "start_date": "2026-08-01",
        "end_date": "2026-08-10",
        "budget": 2000.0,
        "status": "planned",
        "notes": "Book temples"
    }
    res_create = client.post("/trips", json=create_payload)
    assert res_create.status_code == 201, f"Expected 201, got {res_create.status_code}"
    data_created = res_create.json()
    assert "id" in data_created
    assert data_created["title"] == "Summer in Kyoto"
    trip_id = data_created["id"]
    print(f"US5 Test 1 PASSED: Created trip with ID {trip_id}")

    # US5 - Test 2: PUT /trips/{id} with updated fields -> 200 OK
    update_payload = {"title": "Summer in Kyoto & Osaka", "budget": 2500.0}
    res_update = client.put(f"/trips/{trip_id}", json=update_payload)
    assert res_update.status_code == 200, f"Expected 200, got {res_update.status_code}"
    assert res_update.json()["title"] == "Summer in Kyoto & Osaka"
    assert res_update.json()["budget"] == 2500.0
    print("US5 Test 2 PASSED: Updated trip fields correctly")

    # US5 - Test 4: POST /trips with missing required fields -> 400 Bad Request
    res_missing = client.post("/trips", json={"destination": "Nowhere without title"})
    assert res_missing.status_code == 400, f"Expected 400, got {res_missing.status_code}"
    print("US5 Test 4 & US6 Test 2 PASSED: Missing mandatory fields returned 400 Bad Request")

    # US5 - Test 5: PUT /trips/{invalid_id} -> 404 Not Found
    res_invalid_put = client.put("/trips/999999", json={"title": "Ghost Trip"})
    assert res_invalid_put.status_code == 404, f"Expected 404, got {res_invalid_put.status_code}"
    print("US5 Test 5 PASSED: Invalid ID update returned 404 Not Found")

    # US6 - Test 1: Verify persistence (GET /trips/{id})
    res_get = client.get(f"/trips/{trip_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == trip_id
    print("US6 Test 1 PASSED: Trip retrieved successfully from persistent database")

    # US5 - Test 3: DELETE /trips/{id} -> 204 No Content
    res_delete = client.delete(f"/trips/{trip_id}")
    assert res_delete.status_code == 204, f"Expected 204, got {res_delete.status_code}"
    print("US5 Test 3 PASSED: Deleted trip resource returned 204 No Content")

    # US5 - Test 6: GET /trips/{id} after deletion -> 404 Not Found
    res_get_deleted = client.get(f"/trips/{trip_id}")
    assert res_get_deleted.status_code == 404, f"Expected 404, got {res_get_deleted.status_code}"
    print("US5 Test 6 PASSED: GET after deletion returned 404 Not Found")

    print("\nALL US5 & US6 ACCEPTANCE TESTS PASSED SUCCESSFULLY! [OK]")

if __name__ == "__main__":
    test_us5_and_us6_acceptance_tests()
