from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models.Opportunity import Opportunity
from app import db
from pydantic import BaseModel, ValidationError
from typing import Optional, List

opportunities_bp = Blueprint('opportunities', __name__)

class OpportunityCreateSchema(BaseModel):
    opportunityId: Optional[str] = None
    title: str
    description: str
    company: Optional[str] = ""
    location: Optional[str] = ""
    type: Optional[str] = ""
    required_skills: Optional[List[str]] = []
    preferred_skills: Optional[List[str]] = []
    experience_level: Optional[str] = ""
    education_level: Optional[str] = ""
    salary_range: Optional[dict] = {}
    remote_option: Optional[bool] = False
    industry: Optional[str] = ""
    language_requirements: Optional[List[str]] = []
    work_schedule: Optional[str] = ""
    keywords: Optional[List[str]] = []
    benefits: Optional[List[str]] = []
    rating: Optional[float] = 0.0
    source: Optional[str] = ""
    sector: str
    urgency_level: str
    created_by: int
    expiry_date: Optional[str] = None

class OpportunityUpdateSchema(BaseModel):
    opportunityId: Optional[str] = None
    title: Optional[str]
    description: Optional[str]
    company: Optional[str] = ""
    location: Optional[str] = ""
    type: Optional[str] = ""
    required_skills: Optional[List[str]] = []
    preferred_skills: Optional[List[str]] = []
    experience_level: Optional[str] = ""
    education_level: Optional[str] = ""
    salary_range: Optional[dict] = {}
    remote_option: Optional[bool] = False
    industry: Optional[str] = ""
    language_requirements: Optional[List[str]] = []
    work_schedule: Optional[str] = ""
    keywords: Optional[List[str]] = []
    benefits: Optional[List[str]] = []
    rating: Optional[float] = 0.0
    source: Optional[str] = ""
    sector: Optional[str] = ""
    urgency_level: Optional[str] = ""
    expiry_date: Optional[str] = None

@opportunities_bp.route('/', methods=['POST'])
def create_opportunity():
    try:
        data = request.get_json()
        opp_data = OpportunityCreateSchema(**data)
        new_opp = Opportunity(
            opportunityId=opp_data.opportunityId,
            title=opp_data.title,
            description=opp_data.description,
            company=opp_data.company,
            location=opp_data.location,
            type=opp_data.type,
            required_skills=opp_data.required_skills,
            preferred_skills=opp_data.preferred_skills,
            experience_level=opp_data.experience_level,
            education_level=opp_data.education_level,
            salary_range=opp_data.salary_range,
            remote_option=opp_data.remote_option,
            industry=opp_data.industry,
            language_requirements=opp_data.language_requirements,
            work_schedule=opp_data.work_schedule,
            keywords=opp_data.keywords,
            benefits=opp_data.benefits,
            rating=opp_data.rating,
            source=opp_data.source,
            sector=opp_data.sector,
            urgency_level=opp_data.urgency_level,
            created_by=opp_data.created_by,
            expiry_date=opp_data.expiry_date
        )
        db.session.add(new_opp)
        db.session.commit()
        return jsonify(new_opp.to_dict()), 201
    except ValidationError as e:
        return jsonify({"message": e.errors()}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@opportunities_bp.route('/<int:opp_id>', methods=['GET'])
@jwt_required()
def get_opportunity(opp_id):
    opp = Opportunity.query.get(opp_id)
    if not opp:
        return jsonify({"message": "Opportunity not found"}), 404
    return jsonify(opp.to_dict())
@opportunities_bp.route('', methods=['GET'])
def list_opportunities():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    query = Opportunity.query

    # Filtering example: sector
    sector = request.args.get('sector')
    if sector:
        query = query.filter_by(sector=sector)

    # Search example: title contains
    search = request.args.get('search')
    if search:
        query = query.filter(Opportunity.title.ilike(f"%{search}%"))

    opps_paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    opps = [opp.to_dict() for opp in opps_paginated.items]
    return jsonify({
        "opportunities": opps,
        "total": opps_paginated.total,
        "page": opps_paginated.page,
        "pages": opps_paginated.pages
    })

@opportunities_bp.route('/<int:opp_id>', methods=['PUT'])
def update_opportunity(opp_id):
    opp = Opportunity.query.get(opp_id)
    if not opp:
        return jsonify({"message": "Opportunity not found"}), 404
    try:
        data = request.get_json()
        opp_data = OpportunityUpdateSchema(**data)
        for key, value in opp_data.dict(exclude_unset=True).items():
            setattr(opp, key, value)
        db.session.commit()
        return jsonify(opp.to_dict())
    except ValidationError as e:
        return jsonify({"message": e.errors()}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@opportunities_bp.route('/<int:opp_id>', methods=['DELETE'])
def delete_opportunity(opp_id):
    opp = Opportunity.query.get(opp_id)
    if not opp:
        return jsonify({"message": "Opportunity not found"}), 404
    try:
        db.session.delete(opp)
        db.session.commit()
        return jsonify({"message": "Opportunity deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500
