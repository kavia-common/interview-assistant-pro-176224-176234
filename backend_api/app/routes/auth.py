from flask_smorest import Blueprint, abort
from flask.views import MethodView
from marshmallow import Schema, fields
from ..db import query_one, execute
from ..auth import create_password_hash, verify_password, create_jwt_token

# PUBLIC_INTERFACE
blp = Blueprint("Auth", "auth", url_prefix="/auth", description="Authentication endpoints")

class RegisterSchema(Schema):
    """Schema for user registration payload."""
    email = fields.Email(required=True, description="User email")
    password = fields.String(required=True, load_only=True, description="Password")


class LoginSchema(Schema):
    """Schema for user login payload."""
    email = fields.Email(required=True, description="User email")
    password = fields.String(required=True, load_only=True, description="Password")


class TokenSchema(Schema):
    """Schema for JWT token response."""
    token = fields.String(required=True, description="JWT token")


@blp.route("/register")
class Register(MethodView):
    """Register endpoint class for creating a user and returning a JWT."""
    @blp.arguments(RegisterSchema, location="json")
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
    """Login endpoint class for authenticating a user and returning a JWT."""
    @blp.arguments(LoginSchema, location="json")
    @blp.response(200, TokenSchema)
    def post(self, args):
        """Login and receive JWT."""
        email = args["email"].lower()
        password = args["password"]
        row = query_one("SELECT id, email, password_hash FROM users WHERE email=%s", (email,))
        # Ensure compatibility whether password_hash is stored as bytes or str
        stored_hash = row["password_hash"] if row else None
        if isinstance(stored_hash, str):
            try:
                stored_hash_bytes = stored_hash.encode("utf-8")
            except Exception:
                stored_hash_bytes = stored_hash  # fallback; verify_password handles exceptions
        else:
            stored_hash_bytes = stored_hash

        if not row or not verify_password(password, stored_hash_bytes):
            abort(401, message="Invalid credentials")
        token = create_jwt_token(row["id"], row["email"])
        return {"token": token}
