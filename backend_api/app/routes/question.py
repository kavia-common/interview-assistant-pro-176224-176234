from flask_smorest import Blueprint, abort
from flask.views import MethodView
from marshmallow import Schema, fields
from flask import g
from ..db import query_one, query_all

blp = Blueprint("Question", "question", url_prefix="/question", description="Question retrieval")

class NextQuestionQuery(Schema):
    session_id = fields.Integer(required=True, description="Session id")

class QuestionSchema(Schema):
    id = fields.Integer(required=True)
    text = fields.String(required=True)

def _require_user():
    if not getattr(g, "user", None):
        abort(401, message="Unauthorized")


@blp.route("/next")
class NextQuestion(MethodView):
    @blp.arguments(NextQuestionQuery, location="query")
    @blp.response(200, QuestionSchema)
    def get(self, args):
        """Return next unanswered question for session based on role/topic."""
        _require_user()
        session_id = args["session_id"]
        sess = query_one("SELECT id, role FROM interview_sessions WHERE id=%s AND user_id=%s", (session_id, g.user["id"]))
        if not sess:
            abort(404, message="Session not found")

        # Find next question not yet answered in this session
        rows = query_all(
            """
            SELECT q.id, q.text
            FROM questions q
            WHERE (q.role IS NULL OR q.role = %s)
              AND q.id NOT IN (SELECT question_id FROM responses WHERE session_id = %s)
            ORDER BY q.id ASC
            LIMIT 1
            """,
            (sess["role"], session_id),
        )
        if not rows:
            # No more questions; optionally mark session complete
            return {"id": -1, "text": "No more questions. You can end the session."}
        q = rows[0]
        return {"id": q["id"], "text": q["text"]}
