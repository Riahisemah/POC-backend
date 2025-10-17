from flask import Flask, jsonify ,request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv

import os

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    
    # Load environment variables
    load_dotenv()
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:TLXOIOGAkHNgdDmlUxNQcAPMCMNFyJdV@switchback.proxy.rlwy.net:33388/railway"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    
    # Configuration CORS COMPLÈTE
    CORS(app,
         origins=["http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:3000", "https://p-oc.netlify.app"],
         supports_credentials=True,
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
         allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Access-Control-Allow-Origin"],
         expose_headers=["Content-Range", "X-Total-Count"],
         max_age=3600)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Register blueprints
    from app.routes.profiles import profiles_bp
    from app.routes.export import export_bp
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.opportunities import opportunities_bp
    from app.routes.matches import matches_bp
    from app.routes.messages import messages_bp
    from app.routes.analysis import analysis_bp

    # Apply CORS to each blueprint to ensure credentials are supported
    CORS(profiles_bp, supports_credentials=True, origins=["http://localhost:8080", "https://p-oc.netlify.app"])
    CORS(export_bp, supports_credentials=True, origins=["http://localhost:8080", "https://p-oc.netlify.app"])
    CORS(auth_bp, supports_credentials=True, origins=["http://localhost:8080", "https://p-oc.netlify.app"])
    CORS(users_bp, supports_credentials=True, origins=["http://localhost:8080", "https://p-oc.netlify.app"])
    CORS(opportunities_bp, supports_credentials=True, origins=["http://localhost:8080", "https://p-oc.netlify.app"])
    CORS(matches_bp, supports_credentials=True, origins=["http://localhost:8080", "https://p-oc.netlify.app"])
    CORS(messages_bp, supports_credentials=True, origins=["http://localhost:8080", "https://p-oc.netlify.app"])
    CORS(analysis_bp, supports_credentials=True, origins=["http://localhost:8080", "https://p-oc.netlify.app"])

    app.register_blueprint(profiles_bp, url_prefix='/api/profiles')
    app.register_blueprint(export_bp, url_prefix='/api/export')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(opportunities_bp, url_prefix='/api/opportunities')
    app.register_blueprint(matches_bp, url_prefix='/api/matches')
    app.register_blueprint(messages_bp, url_prefix='/api/messages')
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
    
    # Gestion manuelle des requêtes OPTIONS pour toutes les routes
    @app.before_request
    def handle_preflight():
        from flask import request
        if request.method == "OPTIONS":
            response = jsonify({"status": "success"})
            origin = request.headers.get('Origin')
            if origin in ["http://localhost:8080", "https://p-oc.netlify.app"]:
                response.headers.add("Access-Control-Allow-Origin", origin)
            response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
            response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
            response.headers.add("Access-Control-Allow-Credentials", "true")
            response.headers.add("Access-Control-Max-Age", "3600")
            return response

    @app.after_request
    def after_request(response):
        origin = request.headers.get('Origin')
        if origin in ["http://localhost:8080", "https://p-oc.netlify.app"]:
            response.headers.add("Access-Control-Allow-Origin", origin)
        response.headers.add("Access-Control-Allow-Credentials", "true")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        return response

    # Global error handlers to return JSON error details
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad Request", "message": str(error)}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not Found", "message": str(error)}), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({"error": "Internal Server Error", "message": str(error)}), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        return jsonify({"error": "Internal Server Error", "message": str(error)}), 500

    return app
