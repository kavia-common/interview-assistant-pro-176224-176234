def _auth(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_feedback_by_response_and_session(client, registered_user, answered_response):
    _, token = registered_user
    response_id = answered_response["response_id"]
    session_id = answered_response["session_id"]

    # By response
    fr = client.get(f"/feedback/{response_id}", headers=_auth(token))
    assert fr.status_code == 200
    data = fr.get_json()
    assert "items" in data
    assert len(data["items"]) >= 1
    item = data["items"][0]
    assert {"response_id", "communication", "correctness", "completeness", "overall", "suggestions"} <= set(item.keys())

    # By session
    fs = client.get(f"/feedback/session/{session_id}", headers=_auth(token))
    assert fs.status_code == 200
    sdata = fs.get_json()
    assert "items" in sdata
    assert isinstance(sdata["items"], list)


def test_report_endpoints(client, registered_user, answered_response):
    _, token = registered_user
    session_id = answered_response["session_id"]

    # Session aggregate
    r = client.get(f"/report/session/{session_id}", headers=_auth(token))
    assert r.status_code == 200
    rb = r.get_json()
    assert rb["session_id"] == session_id
    assert {"avg_overall", "avg_communication", "avg_correctness", "avg_completeness", "count"} <= set(rb.keys())

    # My history
    h = client.get("/report/my", headers=_auth(token))
    assert h.status_code == 200
    hb = h.get_json()
    assert "items" in hb
    assert isinstance(hb["items"], list)
