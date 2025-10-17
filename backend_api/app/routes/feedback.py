from flask_smorest import Blueprint, abort
from flask.views import MethodView
from marshmallow import Schema, fields
from flask import g
from ..db import query_all

blp = Blueprint("Feedback", "feedback", url_prefix="/feedback", description="Feedback retrieval")

class FeedbackItemSchema(Schema):
    response_id = fields.Integer(required=True)
    communication = fields.Integer(required=True)
    correctness = fields.Integer(required=True)
    completeness = fields.Integer(required=True)
    overall = fields.Integer(required=True)
    suggestions = fields.String(required=True)

class FeedbackListSchema(Schema):
    items = fields.List(fields.Nested(FeedbackItemSchema))

def _require_user():
    if not getattr(g, "user", None):
        abort(401, message="Unauthorized")


@blp.route("/<int:response_id>")
class FeedbackByResponse(MethodView):
    @blp.response(200, FeedbackListSchema)
    def get(self, response_id: int):
        """Get feedback for a given response id."""
        _require_user()
        rows = query_all(
            "SELECT response_id, communication, correctness, completeness, overall, suggestions FROM feedback WHERE response_id=%s",
            (response_id,),
        )
        return {"items": rows}


@blp.route("/session/<int:session_id>")
class FeedbackBySession(MethodView):
    @blp.response(200, FeedbackListSchema)
    def get(self, session_id: int):
        """Get all feedback items for a session."""
        _require_user()
        rows = query_all(
            """
            SELECT f.response_id, f.communication, f.correctness, f.completeness, f.overall, f.suggestions
            FROM feedback f
            JOIN responses r ON r.id = f.response_id
            WHERE r.session_id = %s AND r.user_id = %s
            ORDER BY f.response_id ASC
            """,
            (session_id, g.user["id"]),
        )
        return {"items": rows}
