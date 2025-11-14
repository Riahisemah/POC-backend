import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import Flask, jsonify, request
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # ✅ CONFIGURATION CORS ULTRA-PERMISSIVE
    CORS(app,
         origins="*",  # ✅ Accepte toutes les origines
         allow_headers="*",  # ✅ Accepte tous les headers
         methods="*",  # ✅ Accepte toutes les méthodes
         expose_headers="*")  # ✅ Expose tous les headers

    # ✅ Connexion MySQL
    app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:@localhost:3306/neoleaders_db"

   # app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:TLXOIOGAkHNgdDmlUxNQcAPMCMNFyJdV@switchback.proxy.rlwy.net:33388/railway"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)

    # ⚠️ Importer les modèles ici pour que Flask-Migrate les détecte
    from app import models

    # ✅ GESTION OPTIONS POUR TOUTES LES ROUTES
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = jsonify({"status": "success", "message": "CORS Preflight OK"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Headers", "*")
            response.headers.add("Access-Control-Allow-Methods", "*")
            response.headers.add("Access-Control-Max-Age", "3600")
            return response

    # ✅ HEADERS CORS POUR TOUTES LES RÉPONSES
    @app.after_request
    def after_request(response):
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        response.headers.add("Access-Control-Expose-Headers", "*")
        return response

    # Route de test pour valider CORS
    @app.route("/api/test", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    def test():
        return {"message": "CORS OK ✅ - Tout est autorisé!"}

    # Route de test avec credentials
    @app.route("/api/test-auth", methods=["GET", "OPTIONS"])
    def test_auth():
        return {"message": "CORS avec auth OK ✅", "user": "authenticated"}

    return app