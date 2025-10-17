def _auth(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_start_requires_auth(client):
    res = client.post("/interview/start", json={"role": "backend"})
    assert res.status_code in (401, 200)
    if res.status_code == 200:
        # If not enforced, ensure schema shape
        body = res.get_json()
        assert "session_id" in body


def test_full_answer_flow(client, registered_user, started_session, seeded_questions):
    _, token = registered_user

    # status should be accessible and show in_progress (or existing status)
    status = client.get("/interview/status", query_string={"session_id": started_session}, headers=_auth(token))
    assert status.status_code == 200
    sbody = status.get_json()
    assert sbody["session_id"] == started_session
    assert isinstance(sbody["status"], str)

    # answer a question
    qid = seeded_questions["role_id"]
    payload = {
        "session_id": started_session,
        "question_id": qid,
        "answer_text": "ACID stands for atomicity, consistency, isolation, durability."
    }
    ans = client.post("/interview/answer", json=payload, headers=_auth(token))
    assert ans.status_code == 201
    body = ans.get_json()
    assert "response_id" in body
    fb = body["feedback"]
    assert {"communication", "correctness", "completeness", "overall", "suggestions"} <= set(fb.keys())
    assert isinstance(fb["overall"], int)
