# Backend API Tests

This directory contains pytest-based tests for the Flask backend.

What is covered:
- Auth: register, login, invalid login
- Health checks: "/" and "/_ping"
- Interview: start, answer, status
- Question: next question
- Feedback: by response and by session
- Report: aggregate and user history
- JWT flow: protected endpoints require Authorization header

Prerequisites:
- A running MySQL instance accessible with environment variables:
  - DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
- The database must have the tables used by the app:
  users, interview_sessions, questions, responses, feedback
  with appropriate columns as referenced in code.

Environment:
- The app loads env via python-dotenv.
- Set JWT_SECRET in environment (tests default to "test-secret-change-me" if not set).

Run tests:
1. cd backend_api
2. Ensure virtualenv with requirements installed (pip install -r requirements.txt)
3. Run:
   pytest -q

Isolation & Cleanup:
- Tests create a dedicated test user and minimal seed questions.
- Cleanup removes test-created users/sessions/responses/feedback and the questions from the DB.
