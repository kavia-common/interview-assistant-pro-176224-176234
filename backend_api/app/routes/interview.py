from flask_smorest import Blueprint, abort
from flask.views import MethodView
from marshmallow import Schema, fields
from flask import g
from ...app.db import execute, query_one
from ...app.services.nlp import score_answer

blp = Blueprint("Interview", "interview", url_prefix="/interview", description="Interview flow management")

class StartSchema(Schema):
    role = fields.String(required=False, description="Role or topic for interview")

class StartResponseSchema(Schema):
    session_id = fields.Integer(required=True)

class AnswerSchema(Schema):
    session_id = fields.Integer(required=True)
    question_id = fields.Integer(required=True)
    answer_text = fields.String(required=True)

class FeedbackSchema(Schema):
    response_id = fields.Integer(required=True)
    feedback = fields.Dict(required=True)

class StatusQuerySchema(Schema):
    session_id = fields.Integer(required=True)

class StatusResponseSchema(Schema):
    session_id = fields.Integer(required=True)
    status = fields.String(required=True)

def _require_user():
    if not getattr(g, "user", None):
        abort(401, message="Unauthorized")


@blp.route("/start")
class StartInterview(MethodView):
    @blp.arguments(StartSchema)
    @blp.response(201, StartResponseSchema)
    def post(self, args):
        """Start an interview session for the authenticated user."""
        _require_user()
        role = (args.get("role") or "").strip()
        session_id = execute(
            "INSERT INTO interview_sessions (user_id, role, status) VALUES (%s, %s, %s)",
            (g.user["id"], role, "in_progress"),
        )
        return {"session_id": session_id}


@blp.route("/answer")
class SubmitAnswer(MethodView):
    @blp.arguments(AnswerSchema)
    @blp.response(201, FeedbackSchema)
    def post(self, args):
        """Submit an answer; store response and computed feedback."""
        _require_user()
        session_id = args["session_id"]
        question_id = args["question_id"]
        answer_text = args["answer_text"]

        # Fetch expected keywords from question table if available
        q = query_one("SELECT id, expected_keywords FROM questions WHERE id=%s", (question_id,))
        expected = q["expected_keywords"] if q and q.get("expected_keywords") else ""

        # Insert response
        response_id = execute(
            "INSERT INTO responses (session_id, question_id, user_id, answer_text) VALUES (%s, %s, %s, %s)",
            (session_id, question_id, g.user["id"], answer_text),
        )

        # Score & store feedback
        scores = score_answer(answer_text, expected_keywords=expected)
        execute(
            "INSERT INTO feedback (response_id, communication, correctness, completeness, overall, suggestions) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (response_id, scores["communication"], scores["correctness"], scores["completeness"], scores["overall"], "; ".join(scores["suggestions"])),
        )

        # Optionally update session status
        sess = query_one("SELECT status FROM interview_sessions WHERE id=%s AND user_id=%s", (session_id, g.user["id"]))
        if sess and sess["status"] == "in_progress":
            # keep in progress; client will complete later
            pass

        return {"response_id": response_id, "feedback": scores}


@blp.route("/status")
class SessionStatus(MethodView):
    @blp.arguments(StatusQuerySchema, location="query")
    @blp.response(200, StatusResponseSchema)
    def get(self, args):
        """Get interview session status."""
        _require_user()
        session_id = args["session_id"]
        sess = query_one("SELECT id, status FROM interview_sessions WHERE id=%s AND user_id=%s", (session_id, g.user["id"]))
        if not sess:
            abort(404, message="Session not found")
        return {"session_id": session_id, "status": sess["status"]}
