import os
from app.factory import create_app
from flask_cors import CORS

app = create_app()

CORS(app, origins=[
    "https://p-oc.netlify.app",
    "http://p-oc.netlify.app",
    "http://localhost:8080",
    "http://localhost:3000",
    "*"
])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
