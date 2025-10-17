import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import Flask
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # Enable CORS
    CORS(app, 
         resources={
             r"/api/*": {
                 "origins": ["http://localhost:8080", "http://localhost:3000", "*"],
                 "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS","*"],
                 "allow_headers": ["Content-Type", "Authorization", "X-Requested-With","*"],
                 "supports_credentials": True,
                 "max_age": 3600
             }
         })

    # Connexion MySQL
    app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root:TLXOIOGAkHNgdDmlUxNQcAPMCMNFyJdV@switchback.proxy.rlwy.net:33388/railway"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)

    # ⚠️ importer les modèles ici pour que Flask-Migrate les détecte
    from app import models
    return app
