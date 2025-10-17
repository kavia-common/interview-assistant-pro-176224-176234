def test_health_root(client):
    res = client.get("/")
    assert res.status_code == 200
    body = res.get_json()
    assert isinstance(body, dict)
    assert body.get("message") == "Healthy"


def test_ping(client):
    res = client.get("/_ping")
    assert res.status_code == 200
    body = res.get_json()
    assert body.get("status") == "ok"
    assert "time" in body


def test_register_and_login_flow(client, db_cleaner):
    email = "test_user2@example.com"
    password = "AnotherPass123!"
    # Register
    r = client.post("/auth/register", json={"email": email, "password": password})
    assert r.status_code in (201, 409)  # 409 if race/previous run
    # Login (always should work after register)
    l = client.post("/auth/login", json={"email": email, "password": password})
    assert l.status_code == 200
    token = l.get_json()["token"]
    assert isinstance(token, str) and len(token) > 10


def test_login_invalid_credentials(client, db_cleaner):
    # Never registered email
    resp = client.post("/auth/login", json={"email": "unknown@example.com", "password": "bad"})
    assert resp.status_code == 401
