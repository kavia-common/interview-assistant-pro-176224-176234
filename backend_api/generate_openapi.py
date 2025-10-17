import json
import os
from app import create_app  # import your Flask app factory
from flask_smorest import Api

app = create_app()
api = next((ext for ext in app.extensions.values() if isinstance(ext, Api)), None)

with app.app_context():
    # flask-smorest stores the spec in api.spec
    openapi_spec = api.spec.to_dict() if api else {}

    output_dir = "interfaces"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "openapi.json")

    with open(output_path, "w") as f:
        json.dump(openapi_spec, f, indent=2)
