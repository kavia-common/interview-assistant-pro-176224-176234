from flask_smorest import Blueprint, abort
from flask.views import MethodView
from marshmallow import Schema, fields
from flask import g
from ...app.db import query_one, query_all

blp = Blueprint("Report", "report", url_prefix="/report", description="Reports and history")

class SessionReportSchema(Schema):
    session_id = fields.Integer(required=True)
    avg_overall = fields.Float(required=True)
    avg_communication = fields.Float(required=True)
    avg_correctness = fields.Float(required=True)
    avg_completeness = fields.Float(required=True)
    count = fields.Integer(required=True)

class HistoryItemSchema(Schema):
    session_id = fields.Integer(required=True)
    role = fields.String(required=False)
    status = fields.String(required=False)
    avg_overall = fields.Float(required=False)
    created_at = fields.DateTime(required=False)

class HistoryListSchema(Schema):
    items = fields.List(fields.Nested(HistoryItemSchema))


def _require_user():
    if not getattr(g, "user", None):
        abort(401, message="Unauthorized")


@blp.route("/session/<int:session_id>")
class SessionReport(MethodView):
    @blp.response(200, SessionReportSchema)
    def get(self, session_id: int):
        """Aggregate scores for a session."""
        _require_user()
        agg = query_one(
            """
            SELECT 
                AVG(f.overall) AS avg_overall,
                AVG(f.communication) AS avg_communication,
                AVG(f.correctness) AS avg_correctness,
                AVG(f.completeness) AS avg_completeness,
                COUNT(*) AS cnt
            FROM feedback f
            JOIN responses r ON r.id = f.response_id
            WHERE r.session_id=%s AND r.user_id=%s
            """,
            (session_id, g.user["id"]),
        )
        if not agg or agg["cnt"] is None:
            return {
                "session_id": session_id,
                "avg_overall": 0.0,
                "avg_communication": 0.0,
                "avg_correctness": 0.0,
                "avg_completeness": 0.0,
                "count": 0,
            }
        return {
            "session_id": session_id,
            "avg_overall": float(agg["avg_overall"] or 0),
            "avg_communication": float(agg["avg_communication"] or 0),
            "avg_correctness": float(agg["avg_correctness"] or 0),
            "avg_completeness": float(agg["avg_completeness"] or 0),
            "count": int(agg["cnt"] or 0),
        }


@blp.route("/my")
class MyHistory(MethodView):
    @blp.response(200, HistoryListSchema)
    def get(self):
        """Return user's session history with simple aggregates."""
        _require_user()
        rows = query_all(
            """
            SELECT s.id as session_id, s.role, s.status, s.created_at,
                   (SELECT AVG(f2.overall)
                    FROM feedback f2
                    JOIN responses r2 ON r2.id = f2.response_id
                    WHERE r2.session_id = s.id) as avg_overall
            FROM interview_sessions s
            WHERE s.user_id=%s
            ORDER BY s.created_at DESC
            """,
            (g.user["id"],),
        )
        return {"items": rows}
