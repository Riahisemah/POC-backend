import os
from app import create_app
from flask_cors import CORS

# Création de l'application Flask
app = create_app()

# ⚡ CORS global pour toutes les routes /api/*
CORS(app, origins=["https://p-oc.netlify.app","http://p-oc.netlify.app", "http://localhost:8080", "http://localhost:3000",  "*"])

# ✅ Point d'entrée pour Railway
if __name__ == "__main__":
    # Railway fournit automatiquement le port
    port = int(os.environ.get("PORT", 5000))
    # Écoute toutes les interfaces réseau
    app.run(host="0.0.0.0", port=port, debug=True)
