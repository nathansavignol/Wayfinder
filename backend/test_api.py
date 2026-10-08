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
    timestamp = int(time.time() * 1000)
    user1_email = f"user1_{timestamp}@wayfinder.com"
    user2_email = f"user2_{timestamp}@wayfinder.com"
    password = "securePassword123"

    print("\n==========================================")
    print("RUNNING US8 & US9 (AUTHENTICATION) TESTS")
    print("==========================================")

    # US8 - Test 3: Invalid email / short password -> 400 Bad Request
    res_bad_email = client.post("/auth/register", json={"email": "not-an-email", "password": password})
    assert res_bad_email.status_code == 400
    res_short_pw = client.post("/auth/register", json={"email": "valid@email.com", "password": "123"})
    assert res_short_pw.status_code == 400
    print("US8 Test 3 PASSED: Invalid email or short password rejected with 400 Bad Request")

    # US8 - Test 1: Register User 1 -> 201 Created
    res_reg1 = client.post("/auth/register", json={"email": user1_email, "password": password})
    assert res_reg1.status_code == 201
    print("US8 Test 1 PASSED: User 1 registered with 201 Created")

    # US8 - Test 2: Duplicate registration -> 409 Conflict
    res_dup = client.post("/auth/register", json={"email": user1_email, "password": password})
    assert res_dup.status_code == 409
    print("US8 Test 2 PASSED: Duplicate registration returned 409 Conflict")

    # Register User 2
    res_reg2 = client.post("/auth/register", json={"email": user2_email, "password": password})
    assert res_reg2.status_code == 201

    # US9 - Test 2: Invalid credentials -> 401 Unauthorized
    res_bad_login = client.post("/auth/login", json={"email": user1_email, "password": "wrongPassword!"})
    assert res_bad_login.status_code == 401
    print("US9 Test 2 PASSED: Wrong password returned 401 Unauthorized")

    # US9 - Test 1: Valid login -> 200 OK + access token
    res_login1 = client.post("/auth/login", json={"email": user1_email, "password": password})
    assert res_login1.status_code == 200
    token1 = res_login1.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    res_login2 = client.post("/auth/login", json={"email": user2_email, "password": password})
    assert res_login2.status_code == 200
    token2 = res_login2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}
    print("US9 Test 1 PASSED: Valid logins returned JWT tokens")

    # US9 - Test 3: Unauthenticated GET /trips -> 401 Unauthorized
    res_no_auth = client.get("/trips")
    assert res_no_auth.status_code == 401
    print("US9 Test 3 PASSED: Unauthenticated request returned 401 Unauthorized")

    print("\n==========================================")
    print("RUNNING US5 & US6 (TRIPS CRUD & DB) TESTS")
    print("==========================================")

    # US5 - Test 1: Create trip for user 1 -> 201 Created
    res_trip = client.post("/trips", json={
        "title": "Roadtrip to Alps",
        "destination": "Chamonix, France",
        "start_date": "2026-11-01",
        "end_date": "2026-11-05",
        "budget": 1000.0,
        "status": "planned"
    }, headers=headers1)
    assert res_trip.status_code == 201
    trip_id = res_trip.json()["id"]
    print(f"US5 Test 1 PASSED: Created Trip with ID {trip_id}")

    # US5 - Test 2: Update trip -> 200 OK
    res_up_trip = client.put(f"/trips/{trip_id}", json={"title": "Alps Explorer"}, headers=headers1)
    assert res_up_trip.status_code == 200
    assert res_up_trip.json()["title"] == "Alps Explorer"
    print("US5 Test 2 PASSED: Updated trip title")

    # US5 - Test 4 & US6 Test 2: Missing title -> 400 Bad Request
    res_miss = client.post("/trips", json={"destination": "Nowhere"}, headers=headers1)
    assert res_miss.status_code == 400
    print("US5 Test 4 & US6 Test 2 PASSED: Missing mandatory field returned 400 Bad Request")

    # US5 - Test 5: Update invalid trip ID -> 404 Not Found
    res_inv_put = client.put("/trips/999999", json={"title": "Non-existent"}, headers=headers1)
    assert res_inv_put.status_code == 404
    print("US5 Test 5 PASSED: Invalid trip update returned 404 Not Found")

    # US6 - Test 1: Persistence check
    res_get_trip = client.get(f"/trips/{trip_id}", headers=headers1)
    assert res_get_trip.status_code == 200
    assert res_get_trip.json()["id"] == trip_id
    print("US6 Test 1 PASSED: Trip retrieved from database")

    print("\n==========================================")
    print("RUNNING US10 TO US15 (ACTIVITIES) TESTS")
    print("==========================================")

    # US10 - Test 1: Create activity linked to trip -> 201 Created
    act_payload = {
        "title": "Cable Car to Aiguille du Midi",
        "price": 75.0,
        "type": "sightseeing",
        "duration": 3.5,
        "location": "Chamonix Center",
        "notes": "Bring warm jacket"
    }
    res_act = client.post(f"/trips/{trip_id}/activities", json=act_payload, headers=headers1)
    assert res_act.status_code == 201
    act_data = res_act.json()
    assert act_data["trip_id"] == trip_id
    assert act_data["title"] == "Cable Car to Aiguille du Midi"
    act_id = act_data["id"]
    print(f"US10 Test 1 PASSED: Activity created with ID {act_id} linked to Trip {trip_id}")

    # US10 - Test 2: Add activity to non-existent trip -> 404 Not Found
    res_act_404 = client.post("/trips/999999/activities", json=act_payload, headers=headers1)
    assert res_act_404.status_code == 404
    print("US10 Test 2 PASSED: Adding activity to invalid trip ID returned 404 Not Found")

    # US10 - Test 3: Add activity to trip owned by another user -> 403 Forbidden
    res_act_403 = client.post(f"/trips/{trip_id}/activities", json=act_payload, headers=headers2)
    assert res_act_403.status_code == 403
    print("US10 Test 3 PASSED: Access blocked with 403 Forbidden for non-owner user")

    # US11 - Test 1: Positive numerical price field stored & retrieved accurately
    res_get_act = client.get(f"/trips/{trip_id}/activities/{act_id}", headers=headers1)
    assert res_get_act.status_code == 200
    assert res_get_act.json()["price"] == 75.0
    print("US11 Test 1 PASSED: Activity price 75.0 retrieved accurately")

    # US11 - Test 2: Negative numerical price rejected with 400 Bad Request
    res_neg_price = client.post(f"/trips/{trip_id}/activities", json={"title": "Test", "price": -50.0}, headers=headers1)
    assert res_neg_price.status_code == 400
    print("US11 Test 2 PASSED: Negative price rejected with 400 Bad Request")

    # US11 - Test 3: Non-numeric string as price rejected with 400 Bad Request
    res_str_price = client.post(f"/trips/{trip_id}/activities", json={"title": "Test", "price": "free"}, headers=headers1)
    assert res_str_price.status_code == 400
    print("US11 Test 3 PASSED: Non-numeric price rejected with 400 Bad Request")

    # US12 - Test 1: Filter activities by type
    # Create second activity with different type
    client.post(f"/trips/{trip_id}/activities", json={"title": "Fondue Dinner", "price": 40.0, "type": "food", "duration": 2.0}, headers=headers1)
    res_filter = client.get(f"/trips/{trip_id}/activities?type=sightseeing", headers=headers1)
    assert res_filter.status_code == 200
    assert len(res_filter.json()) == 1
    assert res_filter.json()[0]["type"] == "sightseeing"
    print("US12 Test 1 PASSED: Activity filtered by type 'sightseeing'")

    # US12 - Test 2: Filter by non-existent type returns 200 OK with empty array []
    res_filter_empty = client.get(f"/trips/{trip_id}/activities?type=non_existent_category", headers=headers1)
    assert res_filter_empty.status_code == 200
    assert res_filter_empty.json() == []
    print("US12 Test 2 PASSED: Non-existent category filter returned empty list []")

    # US12 - Test 3: PATCH with new valid category type & verify GET
    res_patch_type = client.patch(f"/trips/{trip_id}/activities/{act_id}", json={"type": "adventure"}, headers=headers1)
    assert res_patch_type.status_code == 200
    assert res_patch_type.json()["type"] == "adventure"
    print("US12 Test 3 PASSED: Category updated to 'adventure'")

    # US13 - Test 1: Valid duration stored & displayed
    assert res_act.json()["duration"] == 3.5
    print("US13 Test 1 PASSED: Valid duration 3.5 stored and displayed")

    # US13 - Test 2: Zero or negative duration rejected with 400 Bad Request
    res_zero_dur = client.post(f"/trips/{trip_id}/activities", json={"title": "Zero", "duration": 0}, headers=headers1)
    assert res_zero_dur.status_code == 400
    res_neg_dur = client.post(f"/trips/{trip_id}/activities", json={"title": "Neg", "duration": -2.0}, headers=headers1)
    assert res_neg_dur.status_code == 400
    print("US13 Test 2 PASSED: Zero and negative durations rejected with 400 Bad Request")

    # US13 - Test 3: PATCH modified duration saved in DB and returned
    res_patch_dur = client.patch(f"/trips/{trip_id}/activities/{act_id}", json={"duration": 4.0}, headers=headers1)
    assert res_patch_dur.status_code == 200
    assert res_patch_dur.json()["duration"] == 4.0
    print("US13 Test 3 PASSED: Modified duration 4.0 saved and returned")

    # US14 - Test 1: Location data stored & retrieved
    assert res_act.json()["location"] == "Chamonix Center"
    print("US14 Test 1 PASSED: Location 'Chamonix Center' retrieved accurately")

    # US14 - Test 2: Optional location defaults to null without error
    res_no_loc = client.post(f"/trips/{trip_id}/activities", json={"title": "Nap time", "duration": 1.0}, headers=headers1)
    assert res_no_loc.status_code == 201
    assert res_no_loc.json()["location"] is None
    print("US14 Test 2 PASSED: Missing location defaulted gracefully to null")

    # US15 - Test 1: Notes field text retrieved exactly
    assert res_act.json()["notes"] == "Bring warm jacket"
    print("US15 Test 1 PASSED: Notes retrieved exactly")

    # US15 - Test 2: Note exceeding maximum character limit rejected with 400 Bad Request
    res_huge_note = client.patch(f"/trips/{trip_id}/activities/{act_id}", json={"notes": "A" * 1001}, headers=headers1)
    assert res_huge_note.status_code == 400
    print("US15 Test 2 PASSED: Note exceeding character limit rejected with 400 Bad Request")

    # US15 - Test 3: Note with special characters stored without corruption
    special_text = "L'été & l'hiver : 100% café / thé, résumé @ Chamonix <3 !"
    res_spec_note = client.patch(f"/trips/{trip_id}/activities/{act_id}", json={"notes": special_text}, headers=headers1)
    assert res_spec_note.status_code == 200
    assert res_spec_note.json()["notes"] == special_text
    print("US15 Test 3 PASSED: Special characters in notes handled without corruption")

    print("\n==========================================")
    print("RUNNING US16 (BUDGET COMPARISON) TESTS")
    print("==========================================")

    # Current trip has: initial_budget = 1000.0, activities = 75.0 (cable car) + 40.0 (fondue) + 0.0 (nap) = 115.0
    # US16 - Test 1: Sum of activity costs alongside budget variance
    res_budget1 = client.get(f"/trips/{trip_id}/budget", headers=headers1)
    assert res_budget1.status_code == 200
    b_data1 = res_budget1.json()
    assert b_data1["initial_budget"] == 1000.0
    assert b_data1["total_cost"] == 115.0
    assert b_data1["remaining_balance"] == 885.0
    assert b_data1["is_over_budget"] is False
    print("US16 Test 1 PASSED: Calculated exact sum 115.0 and variance 885.0")

    # US16 - Test 2: New trip with zero activities -> total cost 0, remaining balance equal to initial budget
    res_empty_trip = client.post("/trips", json={"title": "Empty Trip", "budget": 500.0}, headers=headers1)
    empty_trip_id = res_empty_trip.json()["id"]
    res_budget2 = client.get(f"/trips/{empty_trip_id}/budget", headers=headers1)
    assert res_budget2.status_code == 200
    b_data2 = res_budget2.json()
    assert b_data2["total_cost"] == 0.0
    assert b_data2["remaining_balance"] == 500.0
    assert b_data2["is_over_budget"] is False
    print("US16 Test 2 PASSED: 0 activities trip returned total cost 0 and balance equal to budget")

    # US16 - Test 3: Total costs exceed budget -> is_over_budget: true
    # Add expensive helicopter tour (1200.0) to trip 1 (budget 1000.0, now total = 1315.0)
    client.post(f"/trips/{trip_id}/activities", json={"title": "Helicopter Mont Blanc", "price": 1200.0, "duration": 1.0}, headers=headers1)
    res_budget3 = client.get(f"/trips/{trip_id}/budget", headers=headers1)
    assert res_budget3.status_code == 200
    b_data3 = res_budget3.json()
    assert b_data3["total_cost"] == 1315.0
    assert b_data3["is_over_budget"] is True
    print("US16 Test 3 PASSED: Over budget condition correctly set is_over_budget: true")

    # US5 - Test 3 & 6: Cleanup deletion
    res_del = client.delete(f"/trips/{trip_id}", headers=headers1)
    assert res_del.status_code == 204
    res_del_check = client.get(f"/trips/{trip_id}", headers=headers1)
    assert res_del_check.status_code == 404
    print("US5 Test 3 & 6 PASSED: Deleted trip and verified 404 on subsequent GET")

    print("\n=======================================================")
    print("ALL ACCEPTANCE TESTS (US5, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16) PASSED! [OK]")
    print("=======================================================")

if __name__ == "__main__":
    test_full_acceptance_suite()
