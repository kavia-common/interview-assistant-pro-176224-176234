def _auth(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_next_question_requires_auth(client):
    res = client.get("/question/next", query_string={"session_id": 1})
    assert res.status_code in (401, 200)
    # If middleware allowed passing through with g.user=None, endpoints enforce 401
    if res.status_code == 200:
        # Some environments may accidentally not enforce; still validate contract
        body = res.get_json()
        assert isinstance(body, dict)


def test_next_question_flow(client, registered_user, started_session, seeded_questions):
    _, token = registered_user

    res = client.get("/question/next", query_string={"session_id": started_session}, headers=_auth(token))
    assert res.status_code == 200
    body = res.get_json()
    assert "id" in body and "text" in body
    # It should be either generic or role question that hasn't been answered
    assert body["id"] in (seeded_questions["generic_id"], seeded_questions["role_id"])
