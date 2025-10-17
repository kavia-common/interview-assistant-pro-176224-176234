from app import create_app
import os

app = create_app()  # Swagger UI served at /docs

if __name__ == "__main__":
    port = int(os.getenv("PORT", "3001"))
    app.run(host="0.0.0.0", port=port)
