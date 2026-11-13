from app.services.ai_provider import ai_provider


def _get_auth_headers(client, email="tenant@example.com"):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Test Tenant",
            "password": "strongpassword123",
            "default_jurisdiction": "US-NY-NYC",
        },
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_rag_analysis_retrieves_citations_and_generates_letter(client):
    headers = _get_auth_headers(client, "heat_tenant@example.com")

    comp_resp = client.post(
        "/api/v1/complaints",
        headers=headers,
        json={
            "title": "Apartment has no heat and freezing radiator",
            "jurisdiction": "US-NY-NYC",
            "category": "Heat & Hot Water",
            "description": "Our apartment heating system is broken. Inside temperature drops to 50 degrees Fahrenheit when it is 40 degrees outside.",
            "property_address": "450 Broadway Apt 2A, New York, NY",
            "landlord_name": "Metro Holdings LLC",
            "issue_start_date": "2026-10-15",
            "prior_notice_given": False,
            "urgency_level": "emergency",
        },
    )
    assert comp_resp.status_code == 201
    cid = comp_resp.json()["id"]

    analysis_resp = client.post(
        f"/api/v1/complaints/{cid}/analyze", headers=headers
    )
    assert analysis_resp.status_code == 201
    analysis = analysis_resp.json()

    assert analysis["abstained"] is False
    assert len(analysis["verified_citations"]) >= 1
    section_codes = [c["section_code"] for c in analysis["verified_citations"]]
    assert "§ 27-2029" in section_codes

    # Generate letter from grounded analysis
    letter_resp = client.post(
        "/api/v1/letters/generate",
        headers=headers,
        json={
            "complaint_id": cid,
            "response_deadline_days": 7,
        },
    )
    assert letter_resp.status_code == 201
    letter = letter_resp.json()
    assert "§ 27-2029" in letter["content"]
    assert "Metro Holdings LLC" in letter["content"]
    assert "complete the requested repairs no later than" in letter["content"]


def test_letter_send_requires_confirmation_and_reports_each_channel(client, monkeypatch):
    headers = _get_auth_headers(client, "notice_tenant@example.com")
    complaint = client.post(
        "/api/v1/complaints",
        headers=headers,
        json={
            "title": "Geyser is not working",
            "jurisdiction": "IN-KA-BLR",
            "category": "Plumbing",
            "description": "The geyser has stopped heating water for several days.",
            "property_address": "12 Example Road, Bengaluru",
            "landlord_name": "Property Manager",
            "urgency_level": "medium",
        },
    ).json()
    client.post(f"/api/v1/complaints/{complaint['id']}/analyze", headers=headers)
    letter = client.post(
        "/api/v1/letters/generate",
        headers=headers,
        json={"complaint_id": complaint["id"], "response_deadline_days": 5},
    ).json()

    from app.routers import letters as letters_router
    from app.services.delivery_service import DeliveryError

    monkeypatch.setattr(
        letters_router, "send_letter_email", lambda recipient, draft: None
    )

    def fail_sms(recipient, draft):
        raise DeliveryError("SMS delivery is not configured.")

    monkeypatch.setattr(letters_router, "send_letter_sms", fail_sms)
    response = client.post(
        f"/api/v1/letters/{letter['id']}/send",
        headers=headers,
        json={
            "recipient_email": "landlord@example.com",
            "recipient_phone": "+14155550123",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "email": {"sent": True, "error": None},
        "sms": {"sent": False, "error": "SMS delivery is not configured."},
    }


def test_letter_send_rejects_invalid_phone_number(client):
    headers = _get_auth_headers(client, "invalid_phone_tenant@example.com")
    response = client.post(
        "/api/v1/letters/1/send",
        headers=headers,
        json={
            "recipient_email": "landlord@example.com",
            "recipient_phone": "555-0100",
        },
    )
    assert response.status_code == 422


def test_superseded_statute_warning_and_exclusion_from_letter(client):
    headers = _get_auth_headers(client, "mold_tenant@example.com")

    comp_resp = client.post(
        "/api/v1/complaints",
        headers=headers,
        json={
            "title": "Chronic dampness, roof leak, and indoor mold hazard",
            "jurisdiction": "US-NY-NYC",
            "category": "Water Leaks & Mold",
            "description": "Water leaks and chronic dampness from roof seepage have caused indoor mold hazards on the walls and defective moisture barriers.",
            "prior_notice_given": True,
            "urgency_level": "high",
        },
    )
    cid = comp_resp.json()["id"]

    analysis = client.post(
        f"/api/v1/complaints/{cid}/analyze", headers=headers
    ).json()
    assert analysis["abstained"] is False

    # Verify both active (§ 27-2017.3) and superseded (§ 27-2005) mold provisions are retrieved
    sections = {c["section_code"]: c for c in analysis["verified_citations"]}
    assert "§ 27-2017.3" in sections
    assert "§ 27-2005 (1998 Prior Rule)" in sections
    assert sections["§ 27-2005 (1998 Prior Rule)"]["is_active"] is False

    # Verify explicit superseded warning is injected into limitations_and_warnings
    warnings_text = " ".join(analysis["limitations_and_warnings"])
    assert "historical/superseded" in warnings_text
    assert "NYC Local Law 55" in warnings_text

    # Verify generated demand letter cites active § 27-2017.3 but excludes superseded § 27-2005
    letter = client.post(
        "/api/v1/letters/generate",
        headers=headers,
        json={"complaint_id": cid, "response_deadline_days": 14},
    ).json()
    assert any("27-2017.3" in c for c in letter["citations_used"])
    assert not any("27-2005" in c for c in letter["citations_used"])


def test_hallucinated_chunk_ids_are_stripped_and_all_invalid_abstains(
    client, monkeypatch
):
    headers = _get_auth_headers(client, "guardrail_tenant@example.com")

    comp_resp = client.post(
        "/api/v1/complaints",
        headers=headers,
        json={
            "title": "Hot water shut off in bathroom sink and shower",
            "jurisdiction": "US-NY-NYC",
            "category": "Heat & Hot Water",
            "description": "No hot water in shower or bath sink for three days; water temperature is below 70 degrees.",
            "prior_notice_given": True,
            "urgency_level": "high",
        },
    )
    cid = comp_resp.json()["id"]

    # Case 1: Provider returns 1 valid retrieved chunk_id plus 2 fabricated chunk_ids (99991, 88882)
    def _mock_partial_hallucination(
        complaint_description,
        jurisdiction,
        prior_notice_given,
        issue_start_date,
        retrieved_chunks,
    ):
        valid_id = retrieved_chunks[0]["chunk_id"]
        return {
            "summary_explanation": "Hot water must be maintained at 120 degrees Fahrenheit.",
            "key_rights": ["Right to 120F hot water"],
            "missing_evidence": [],
            "limitations_and_warnings": [],
            "recommended_next_steps": ["Send written notice"],
            "cited_chunk_ids": [valid_id, 99991, 88882],
        }

    monkeypatch.setattr(
        ai_provider, "generate_grounded_analysis", _mock_partial_hallucination
    )
    res1 = client.post(
        f"/api/v1/complaints/{cid}/analyze", headers=headers
    ).json()
    assert res1["abstained"] is False
    assert res1["stripped_hallucinations_count"] == 2
    assert len(res1["verified_citations"]) == 1

    # Case 2: Provider returns ONLY fabricated chunk_ids -> Must trigger Safe Abstention (not fallback)
    def _mock_total_hallucination(*args, **kwargs):
        return {
            "summary_explanation": "Invented summary with bogus citations.",
            "key_rights": [],
            "missing_evidence": [],
            "limitations_and_warnings": [],
            "recommended_next_steps": [],
            "cited_chunk_ids": [777777, 888888],
        }

    monkeypatch.setattr(
        ai_provider, "generate_grounded_analysis", _mock_total_hallucination
    )
    res2 = client.post(
        f"/api/v1/complaints/{cid}/analyze", headers=headers
    ).json()
    assert res2["abstained"] is True
    assert res2["stripped_hallucinations_count"] == 2
    assert res2["verified_citations"] == []


def test_rag_safe_abstention_when_jurisdiction_has_no_sources(client):
    headers = _get_auth_headers(client, "mars_tenant@example.com")

    comp_resp = client.post(
        "/api/v1/complaints",
        headers=headers,
        json={
            "title": "Roof leak in unindexed jurisdiction",
            "jurisdiction": "UNINDEXED-STATE-99",
            "category": "Water Leak & Mold",
            "description": "Heavy water leaking from ceiling every time it rains, causing dampness.",
            "prior_notice_given": True,
            "urgency_level": "high",
        },
    )
    cid = comp_resp.json()["id"]

    analysis = client.post(
        f"/api/v1/complaints/{cid}/analyze", headers=headers
    ).json()
    assert analysis["abstained"] is True
    assert analysis["verified_citations"] == []
