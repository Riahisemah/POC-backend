from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.User import User
from app import db
from pydantic import BaseModel, EmailStr
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

class RegisterSchema(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    phone: str = None
    linkedin_url: str = None

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        schema = RegisterSchema(**data)
        if User.query.filter_by(email=schema.email).first():
            return jsonify({"message": "User already exists"}), 400
        hashed_password = generate_password_hash(schema.password)
        new_user = User(
            first_name=schema.first_name,
            last_name=schema.last_name,
            email=schema.email,
            password=hashed_password,
            phone=schema.phone,
            linkedin_url=schema.linkedin_url
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User created successfully", "user": new_user.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        schema = LoginSchema(**data)
        user = User.query.filter_by(email=schema.email).first()
        if not user or not check_password_hash(user.password, schema.password):
            return jsonify({"message": "Invalid credentials"}), 401
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user.to_dict()
        }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 400

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    try:
        current_user = get_jwt_identity()
        access_token = create_access_token(identity=current_user)
        return jsonify({"access_token": access_token}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 400

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    try:
        # In a real app, you might want to blacklist the token
        return jsonify({"message": "Logged out successfully"}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 400
