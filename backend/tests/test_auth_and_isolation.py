def test_user_registration_login_and_password_change_verification(client):
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "alice@example.com",
            "full_name": "Alice Renter",
            "password": "securepassword123",
            "default_jurisdiction": "US-NY-NYC",
        },
    )
    assert reg_resp.status_code == 201
    data = reg_resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "alice@example.com"
    assert data["user"]["is_admin"] is False
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Attempting to change password without current_password must fail with 400
    bad_pw_change = client.patch(
        "/api/v1/auth/me",
        headers=headers,
        json={"new_password": "newsecurepassword456"},
    )
    assert bad_pw_change.status_code == 400
    assert "Current password is required" in bad_pw_change.json()["detail"]

    # Attempting to change password with wrong current_password must fail with 400
    wrong_pw_change = client.patch(
        "/api/v1/auth/me",
        headers=headers,
        json={
            "current_password": "wrongpassword999",
            "new_password": "newsecurepassword456",
        },
    )
    assert wrong_pw_change.status_code == 400
    assert "incorrect" in wrong_pw_change.json()["detail"]

    # Valid password change with correct current_password succeeds
    good_pw_change = client.patch(
        "/api/v1/auth/me",
        headers=headers,
        json={
            "current_password": "securepassword123",
            "new_password": "newsecurepassword456",
        },
    )
    assert good_pw_change.status_code == 200

    # Login with new password succeeds
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "newsecurepassword456"},
    )
    assert login_resp.status_code == 200


def test_cross_user_complaint_isolation_and_admin_only_ingestion(client):
    # Register standard User A
    resp_a = client.post(
        "/api/v1/auth/register",
        json={
            "email": "usera@example.com",
            "full_name": "User A",
            "password": "passwordA123",
            "default_jurisdiction": "US-NY-NYC",
        },
    )
    headers_a = {"Authorization": f"Bearer {resp_a.json()['access_token']}"}

    # Register standard User B
    resp_b = client.post(
        "/api/v1/auth/register",
        json={
            "email": "userb@example.com",
            "full_name": "User B",
            "password": "passwordB123",
            "default_jurisdiction": "US-CA",
        },
    )
    headers_b = {"Authorization": f"Bearer {resp_b.json()['access_token']}"}

    # User A creates a complaint
    comp_resp = client.post(
        "/api/v1/complaints",
        headers=headers_a,
        json={
            "title": "No heat in apartment since November",
            "jurisdiction": "US-NY-NYC",
            "category": "Heat & Hot Water",
            "description": "Inside temperature has been 52 degrees Fahrenheit at night and radiator is freezing cold.",
            "property_address": "123 Main St Apt 4B",
            "landlord_name": "Acme Realty",
            "prior_notice_given": True,
            "urgency_level": "high",
        },
    )
    assert comp_resp.status_code == 201
    complaint_id = comp_resp.json()["id"]

    # User B attempts to read or delete User A's complaint -> Must return 403 Forbidden
    assert (
        client.get(f"/api/v1/complaints/{complaint_id}", headers=headers_b).status_code
        == 403
    )
    assert (
        client.delete(
            f"/api/v1/complaints/{complaint_id}", headers=headers_b
        ).status_code
        == 403
    )

    # Non-admin User A attempts to ingest a shared legal source -> Must return 403 Forbidden
    ingest_payload = {
        "jurisdiction": "US-WA-SEA",
        "title": "Seattle Rental Housing Code Sample",
        "citation_prefix": "SMC",
        "is_active": True,
        "raw_text": "§ 22.206.080: Minimum Heating Standards\nEvery rental housing unit must maintain 68 degrees Fahrenheit.",
    }
    non_admin_ingest = client.post(
        "/api/v1/sources/ingest", headers=headers_a, json=ingest_payload
    )
    assert non_admin_ingest.status_code == 403

    # Register designated Admin User (matches settings.ADMIN_EMAIL = admin@example.com)
    resp_admin = client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@example.com",
            "full_name": "System Admin",
            "password": "adminpassword123",
            "default_jurisdiction": "US-NY-NYC",
        },
    )
    assert resp_admin.json()["user"]["is_admin"] is True
    headers_admin = {
        "Authorization": f"Bearer {resp_admin.json()['access_token']}"
    }

    admin_ingest = client.post(
        "/api/v1/sources/ingest", headers=headers_admin, json=ingest_payload
    )
    assert admin_ingest.status_code == 201
    assert len(admin_ingest.json()["chunks"]) == 1
