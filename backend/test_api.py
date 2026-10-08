import os
import sys
import time

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_full_acceptance_suite():
    print("\n==========================================")
    print("RUNNING US8 & US9 (AUTHENTICATION) TESTS")
    print("==========================================")

    test_email = f"tester_{int(time.time() * 1000)}@wayfinder.com"
    test_password = "securePassword123"

    # US8 - Test 3: POST /auth/register with invalid email format or short password -> 400 Bad Request
    res_bad_email = client.post("/auth/register", json={"email": "not-an-email", "password": test_password})
    assert res_bad_email.status_code == 400, f"Expected 400, got {res_bad_email.status_code}"
    res_short_pw = client.post("/auth/register", json={"email": "valid@email.com", "password": "123"})
    assert res_short_pw.status_code == 400, f"Expected 400, got {res_short_pw.status_code}"
    print("US8 Test 3 PASSED: Invalid email or short password rejected with 400 Bad Request")

    # US8 - Test 1: POST /auth/register with valid credentials -> 201 Created
    res_reg = client.post("/auth/register", json={"email": test_email, "password": test_password})
    assert res_reg.status_code == 201, f"Expected 201, got {res_reg.status_code}"
    assert "id" in res_reg.json()
    print("US8 Test 1 PASSED: User successfully registered with 201 Created")

    # US8 - Test 2: POST /auth/register using already registered email -> 409 Conflict
    res_conflict = client.post("/auth/register", json={"email": test_email, "password": test_password})
    assert res_conflict.status_code == 409, f"Expected 409, got {res_conflict.status_code}"
    print("US8 Test 2 PASSED: Duplicate registration rejected with 409 Conflict")

    # US9 - Test 2: POST /auth/login with incorrect credentials -> 401 Unauthorized
    res_bad_login = client.post("/auth/login", json={"email": test_email, "password": "wrongPassword!"})
    assert res_bad_login.status_code == 401, f"Expected 401, got {res_bad_login.status_code}"
    print("US9 Test 2 PASSED: Wrong password rejected with 401 Unauthorized")

    # US9 - Test 1: POST /auth/login with correct credentials -> 200 OK + access token
    res_login = client.post("/auth/login", json={"email": test_email, "password": test_password})
    assert res_login.status_code == 200, f"Expected 200, got {res_login.status_code}"
    token_data = res_login.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    access_token = token_data["access_token"]
    print("US9 Test 1 PASSED: Login returned 200 OK with valid access token")

    # US9 - Test 3: GET /trips without JWT token in Authorization header -> 401 Unauthorized
    res_no_auth = client.get("/trips")
    assert res_no_auth.status_code == 401, f"Expected 401, got {res_no_auth.status_code}"
    print("US9 Test 3 PASSED: GET /trips blocked with 401 Unauthorized when missing token")

    print("\n==========================================")
    print("RUNNING US5 & US6 (TRIPS CRUD & DB) TESTS")
    print("==========================================")

    auth_headers = {"Authorization": f"Bearer {access_token}"}

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
    res_create = client.post("/trips", json=create_payload, headers=auth_headers)
    assert res_create.status_code == 201, f"Expected 201, got {res_create.status_code}"
    data_created = res_create.json()
    assert "id" in data_created
    assert data_created["title"] == "Summer in Kyoto"
    trip_id = data_created["id"]
    print(f"US5 Test 1 PASSED: Created trip with ID {trip_id}")

    # US5 - Test 2: PUT /trips/{id} with updated fields -> 200 OK
    update_payload = {"title": "Summer in Kyoto & Osaka", "budget": 2500.0}
    res_update = client.put(f"/trips/{trip_id}", json=update_payload, headers=auth_headers)
    assert res_update.status_code == 200, f"Expected 200, got {res_update.status_code}"
    assert res_update.json()["title"] == "Summer in Kyoto & Osaka"
    assert res_update.json()["budget"] == 2500.0
    print("US5 Test 2 PASSED: Updated trip fields correctly")

    # US5 - Test 4: POST /trips with missing required fields -> 400 Bad Request
    res_missing = client.post("/trips", json={"destination": "Nowhere without title"}, headers=auth_headers)
    assert res_missing.status_code == 400, f"Expected 400, got {res_missing.status_code}"
    print("US5 Test 4 & US6 Test 2 PASSED: Missing mandatory fields returned 400 Bad Request")

    # US5 - Test 5: PUT /trips/{invalid_id} -> 404 Not Found
    res_invalid_put = client.put("/trips/999999", json={"title": "Ghost Trip"}, headers=auth_headers)
    assert res_invalid_put.status_code == 404, f"Expected 404, got {res_invalid_put.status_code}"
    print("US5 Test 5 PASSED: Invalid ID update returned 404 Not Found")

    # US6 - Test 1: Verify persistence (GET /trips/{id})
    res_get = client.get(f"/trips/{trip_id}", headers=auth_headers)
    assert res_get.status_code == 200
    assert res_get.json()["id"] == trip_id
    print("US6 Test 1 PASSED: Trip retrieved successfully from persistent database")

    # US5 - Test 3: DELETE /trips/{id} -> 204 No Content
    res_delete = client.delete(f"/trips/{trip_id}", headers=auth_headers)
    assert res_delete.status_code == 204, f"Expected 204, got {res_delete.status_code}"
    print("US5 Test 3 PASSED: Deleted trip resource returned 204 No Content")

    # US5 - Test 6: GET /trips/{id} after deletion -> 404 Not Found
    res_get_deleted = client.get(f"/trips/{trip_id}", headers=auth_headers)
    assert res_get_deleted.status_code == 404, f"Expected 404, got {res_get_deleted.status_code}"
    print("US5 Test 6 PASSED: GET after deletion returned 404 Not Found")

    print("\nALL US5, US6, US8, AND US9 ACCEPTANCE TESTS PASSED! [OK]")

if __name__ == "__main__":
    test_full_acceptance_suite()
