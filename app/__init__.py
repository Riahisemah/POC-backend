from flask import Flask, jsonify, request
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
    
    # ✅ CONFIGURATION CORS LA PLUS PERMISSIVE
    CORS(app, 
         resources={r"/api/*": {
             "origins": "*",  # ✅ Accepte toutes les origines
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
             "allow_headers": ["*"],  # ✅ Accepte tous les headers
             "expose_headers": ["*"],  # ✅ Expose tous les headers
             "supports_credentials": True,  # ✅ Autorise les credentials
             "max_age": 3600
         }})

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

    # ✅ APPLICATION CORS PERMISSIVE À CHAQUE BLUEPRINT
    blueprints = [
        profiles_bp, export_bp, auth_bp, users_bp, 
        opportunities_bp, matches_bp, messages_bp, analysis_bp
    ]
    
    for bp in blueprints:
        CORS(bp, 
             origins="*",
             methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
             allow_headers=["*"],
             expose_headers=["*"],
             supports_credentials=True)

    app.register_blueprint(profiles_bp, url_prefix='/api/profiles')
    app.register_blueprint(export_bp, url_prefix='/api/export')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(opportunities_bp, url_prefix='/api/opportunities')
    app.register_blueprint(matches_bp, url_prefix='/api/matches')
    app.register_blueprint(messages_bp, url_prefix='/api/messages')
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
    
    # ✅ GESTION OPTIONS SIMPLIFIÉE ET PERMISSIVE
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = jsonify({"status": "success"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Headers", "*")
            response.headers.add("Access-Control-Allow-Methods", "*")
            response.headers.add("Access-Control-Allow-Credentials", "true")
            response.headers.add("Access-Control-Max-Age", "3600")
            return response

    # ✅ HEADERS CORS POUR TOUTES LES RÉPONSES
    @app.after_request
    def after_request(response):
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        response.headers.add("Access-Control-Expose-Headers", "*")
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