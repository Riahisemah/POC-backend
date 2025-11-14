import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)

    # Load environment variables
    load_dotenv()

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:@localhost:3306/neoleaders_db"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

    # Global CORS
    CORS(app, origins=[
        "https://p-oc.netlify.app",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "*"
    ], methods=["GET","POST","PUT","DELETE","OPTIONS","PATCH"],
       allow_headers=["Content-Type","Authorization","X-Requested-With","X-User-ID"],
       expose_headers=["Content-Range","X-Total-Count"],
       max_age=3600)

    # Init extensions
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
    from app.routes.community import community_bp

    app.register_blueprint(profiles_bp, url_prefix='/api/profiles')
    app.register_blueprint(export_bp, url_prefix='/api/export')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(opportunities_bp, url_prefix='/api/opportunities')
    app.register_blueprint(matches_bp, url_prefix='/api/matches')
    app.register_blueprint(messages_bp, url_prefix='/api/messages')
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
    app.register_blueprint(community_bp, url_prefix='/api/community')

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not Found"}), 404

    @app.errorhandler(500)
    def internal(error):
        return jsonify({"error": "Internal Server Error"}), 500

    return app
