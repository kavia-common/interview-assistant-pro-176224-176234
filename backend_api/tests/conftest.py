import os
import contextlib
from typing import Dict, Generator, Tuple
import pytest

# Ensure tests run inside backend_api working dir for dotenv resolution
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)

# Import app and db after setting cwd so .env loads correctly
from app import create_app  # noqa
from app.db import query_one, query_all, execute  # noqa
from app.config import get_config  # noqa


@pytest.fixture(scope="session")
def app():
    """
    Create Flask app once per test session using the factory.
    It will initialize the DB pool with environment-provided settings.
    """
    # Ensure JWT secret for tests (can be overridden by env/.env)
    os.environ.setdefault("JWT_SECRET", "test-secret-change-me")
    application = create_app()
    return application


@pytest.fixture()
def client(app):
    """
    Flask test client with app context.
    """
    with app.test_client() as c:
        with app.app_context():
            yield c


@pytest.fixture()
def db_cleaner() -> Generator[None, None, None]:
    """
    DB cleanup fixture to ensure user-specific test records are removed
    after each test. We scope removal around the test user email to avoid
    touching unrelated data in a shared DB.

    We avoid wrapping in a single transaction since the app code commits in its helpers.
    Instead, we delete created resources explicitly on teardown.
    """
    yield
    # Best effort cleanup for any users created in tests and dependent rows.
    test_emails = [
        "test_user@example.com",
        "test_user2@example.com",
        "seed_user@example.com",
    ]
    # Delete by cascading relationships carefully
    for email in test_emails:
        user = query_one("SELECT id FROM users WHERE email=%s", (email,))
        if not user:
            continue
        uid = user["id"]
        # find sessions
        sessions = query_all("SELECT id FROM interview_sessions WHERE user_id=%s", (uid,))
        for s in sessions:
            sid = s["id"]
            # responses in session
            responses = query_all("SELECT id FROM responses WHERE session_id=%s", (sid,))
            for r in responses:
                # feedback rows for response
                execute("DELETE FROM feedback WHERE response_id=%s", (r["id"],))
            # responses
            execute("DELETE FROM responses WHERE session_id=%s", (sid,))
            # session
            execute("DELETE FROM interview_sessions WHERE id=%s", (sid,))
        # remove user
        execute("DELETE FROM users WHERE id=%s", (uid,))


def _auth_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def registered_user(client, db_cleaner) -> Tuple[int, str]:
    """
    Registers a fresh user and returns (user_id, jwt_token).
    If the email already exists (due to a previous run), perform login to get a token.
    """
    email = "test_user@example.com"
    password = "StrongPassw0rd!"
    # Try register
    resp = client.post("/auth/register", json={"email": email, "password": password})
    if resp.status_code == 201:
        token = resp.get_json()["token"]
    elif resp.status_code == 409:
        # Already exists -> login
        resp = client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200, f"Expected login 200, got {resp.status_code}, body={resp.get_data(as_text=True)}"
        token = resp.get_json()["token"]
    else:
        pytest.fail(f"Unexpected response during register: {resp.status_code}, body={resp.get_data(as_text=True)}")

    # Look up user id directly
    row = query_one("SELECT id FROM users WHERE email=%s", (email,))
    assert row and "id" in row
    return row["id"], token


@pytest.fixture()
def seeded_questions(db_cleaner) -> Generator[Dict[str, int], None, None]:
    """
    Ensure at least a generic and a role-specific question exist for tests.
    Yields a dict with question ids.
    """
    # Insert generic question (role NULL)
    q1_id = execute(
        "INSERT INTO questions (text, role, expected_keywords) VALUES (%s, %s, %s)",
        ("What is a REST API? Explain its core principles.", None, "http,stateless,resource"),
    )
    # Insert role-specific question
    q2_id = execute(
        "INSERT INTO questions (text, role, expected_keywords) VALUES (%s, %s, %s)",
        ("Explain ACID properties in databases.", "backend", "atomicity,consistency,isolation,durability"),
    )

    yield {"generic_id": q1_id, "role_id": q2_id}

    # Cleanup questions created if no other tests need them
    # Delete in reverse order to avoid FK issues if any (responses may reference these)
    with contextlib.suppress(Exception):
        execute("DELETE FROM questions WHERE id=%s", (q2_id,))
    with contextlib.suppress(Exception):
        execute("DELETE FROM questions WHERE id=%s", (q1_id,))


@pytest.fixture()
def started_session(client, registered_user) -> int:
    """
    Start an interview session for the user and return session_id.
    """
    _, token = registered_user
    resp = client.post("/interview/start", json={"role": "backend"}, headers=_auth_headers(token))
    assert resp.status_code == 201, f"Start session failed: {resp.status_code}, body={resp.get_data(as_text=True)}"
    return resp.get_json()["session_id"]


@pytest.fixture()
def answered_response(client, registered_user, started_session, seeded_questions) -> Dict[str, int]:
    """
    Submit an answer for the generic question to create a response and feedback.
    Returns dict with keys: response_id, session_id, question_id.
    """
    _, token = registered_user
    # Next question for session should be the role-specific or generic based on availability,
    # but we purposely answer the generic one by direct call to /interview/answer with known id.
    question_id = seeded_questions["generic_id"]
    payload = {
        "session_id": started_session,
        "question_id": question_id,
        "answer_text": "A REST API uses HTTP, is stateless, and treats server objects as resources."
    }
    resp = client.post("/interview/answer", json=payload, headers=_auth_headers(token))
    assert resp.status_code == 201, f"Answer failed: {resp.status_code}, body={resp.get_data(as_text=True)}"
    data = resp.get_json()
    assert "response_id" in data and "feedback" in data
    return {"response_id": data["response_id"], "session_id": started_session, "question_id": question_id}
