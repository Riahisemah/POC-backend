from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models.User import User
from app import db
from pydantic import BaseModel, EmailStr, ValidationError
from typing import Optional

users_bp = Blueprint('users', __name__)

class UserCreateSchema(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    phone: Optional[str]
    linkedin_url: Optional[str]
    role: Optional[str]

class UserUpdateSchema(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    linkedin_url: Optional[str]
    role: Optional[str]

@users_bp.route('/', methods=['POST'])
@jwt_required()
def create_user():
    try:
        data = request.get_json()
        user_data = UserCreateSchema(**data)
        if User.query.filter_by(email=user_data.email).first():
            return jsonify({"message": "User with this email already exists"}), 400
        from werkzeug.security import generate_password_hash
        new_user = User(
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            password=generate_password_hash(user_data.password),
            phone=user_data.phone,
            linkedin_url=user_data.linkedin_url,
            role=user_data.role or "member"
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify(new_user.to_dict()), 201
    except ValidationError as e:
        return jsonify({"message": e.errors()}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    return jsonify(user.to_dict())

@users_bp.route('/', methods=['GET'])
@jwt_required()
def list_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    query = User.query

    # Filtering example: filter by role
    role = request.args.get('role')
    if role:
        query = query.filter_by(role=role)

    users_paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    users = [user.to_dict() for user in users_paginated.items]
    return jsonify({
        "users": users,
        "total": users_paginated.total,
        "page": users_paginated.page,
        "pages": users_paginated.pages
    })

@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    try:
        data = request.get_json()
        user_data = UserUpdateSchema(**data)
        for key, value in user_data.dict(exclude_unset=True).items():
            setattr(user, key, value)
        db.session.commit()
        return jsonify(user.to_dict())
    except ValidationError as e:
        return jsonify({"message": e.errors()}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500
