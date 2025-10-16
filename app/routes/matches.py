from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models.Match import Match
from app import db
from pydantic import BaseModel, ValidationError
from typing import Optional

matches_bp = Blueprint('matches', __name__)

class MatchCreateSchema(BaseModel):
    profile_id: int
    opportunity_id: int
    score: Optional[float]
    status: Optional[str]

class MatchUpdateSchema(BaseModel):
    score: Optional[float]
    status: Optional[str]

@matches_bp.route('/', methods=['POST'])
@jwt_required()
def create_match():
    try:
        data = request.get_json()
        match_data = MatchCreateSchema(**data)
        new_match = Match(
            profile_id=match_data.profile_id,
            opportunity_id=match_data.opportunity_id,
            score=match_data.score,
            status=match_data.status or "pending"
        )
        db.session.add(new_match)
        db.session.commit()
        return jsonify(new_match.to_dict()), 201
    except ValidationError as e:
        return jsonify({"message": e.errors()}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@matches_bp.route('/<int:match_id>', methods=['GET'])
@jwt_required()
def get_match(match_id):
    match = Match.query.get(match_id)
    if not match:
        return jsonify({"message": "Match not found"}), 404
    return jsonify(match.to_dict())

@matches_bp.route('/', methods=['GET'])
@jwt_required()
def list_matches():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    query = Match.query

    # Filtering example: status
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)

    matches_paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    matches = [match.to_dict() for match in matches_paginated.items]
    return jsonify({
        "matches": matches,
        "total": matches_paginated.total,
        "page": matches_paginated.page,
        "pages": matches_paginated.pages
    })

@matches_bp.route('/<int:match_id>', methods=['PUT'])
@jwt_required()
def update_match(match_id):
    match = Match.query.get(match_id)
    if not match:
        return jsonify({"message": "Match not found"}), 404
    try:
        data = request.get_json()
        match_data = MatchUpdateSchema(**data)
        for key, value in match_data.dict(exclude_unset=True).items():
            setattr(match, key, value)
        db.session.commit()
        return jsonify(match.to_dict())
    except ValidationError as e:
        return jsonify({"message": e.errors()}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@matches_bp.route('/<int:match_id>', methods=['DELETE'])
@jwt_required()
def delete_match(match_id):
    match = Match.query.get(match_id)
    if not match:
        return jsonify({"message": "Match not found"}), 404
    try:
        db.session.delete(match)
        db.session.commit()
        return jsonify({"message": "Match deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500
