from flask_smorest import Blueprint, abort
from flask.views import MethodView
from marshmallow import Schema, fields
from ...app.db import query_one, execute
from ...app.auth import create_password_hash, verify_password, create_jwt_token

blp = Blueprint("Auth", "auth", url_prefix="/auth", description="Authentication endpoints")

class RegisterSchema(Schema):
    email = fields.Email(required=True, description="User email")
    password = fields.String(required=True, load_only=True, description="Password")


class LoginSchema(Schema):
    email = fields.Email(required=True, description="User email")
    password = fields.String(required=True, load_only=True, description="Password")


class TokenSchema(Schema):
    token = fields.String(required=True, description="JWT token")


@blp.route("/register")
class Register(MethodView):
    @blp.arguments(RegisterSchema)
    @blp.response(201, TokenSchema)
    def post(self, args):
        """Register a new user and return JWT."""
        email = args["email"].lower()
        password = args["password"]
        existing = query_one("SELECT id FROM users WHERE email=%s", (email,))
        if existing:
            abort(409, message="Email already registered")
        pwd_hash = create_password_hash(password)
        user_id = execute(
            "INSERT INTO users (email, password_hash) VALUES (%s, %s)",
            (email, pwd_hash),
        )
        token = create_jwt_token(user_id, email)
        return {"token": token}


@blp.route("/login")
class Login(MethodView):
    @blp.arguments(LoginSchema)
    @blp.response(200, TokenSchema)
    def post(self, args):
        """Login and receive JWT."""
        email = args["email"].lower()
        password = args["password"]
        row = query_one("SELECT id, email, password_hash FROM users WHERE email=%s", (email,))
        if not row or not verify_password(password, row["password_hash"].encode("utf-8") if isinstance(row["password_hash"], str) else row["password_hash"]):
            abort(401, message="Invalid credentials")
        token = create_jwt_token(row["id"], row["email"])
        return {"token": token}
