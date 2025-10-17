import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import Flask
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # ✅ Configuration CORS — simplifiée et 100 % compatible
    CORS(app, 
         origins=["http://localhost:8080", "http://localhost:3000", "*"],
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

    # ✅ Connexion MySQL (avec driver explicite pour éviter les erreurs)
    app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:TLXOIOGAkHNgdDmlUxNQcAPMCMNFyJdV@switchback.proxy.rlwy.net:33388/railway"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)

    # ⚠️ Importer les modèles ici pour que Flask-Migrate les détecte
    from app import models

    # Exemple de route de test pour valider CORS
    @app.route("/api/test", methods=["GET", "OPTIONS"])
    def test():
        return {"message": "CORS OK ✅"}

    return app
