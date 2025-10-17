from flask_smorest import Blueprint
from flask.views import MethodView

blp = Blueprint("Health Check", "health", url_prefix="/", description="Health check route")


@blp.route("/")
class HealthCheck(MethodView):
    """Health check endpoint at root path."""
    def get(self):
        """Simple health check endpoint."""
        return {"message": "Healthy"}
