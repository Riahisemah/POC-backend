from flask import Blueprint, request, jsonify
import logging
from flask_jwt_extended import jwt_required
from app.services.pdf_extractor import PDFExtractor
from app.services.linkedin_extractor import extract_linkedin_scrapingbee
from app.models.Profile import Profile
from app import db
from pydantic import BaseModel, ValidationError
from typing import Optional
import re
import jwt
import os
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

profiles_bp = Blueprint('profiles', __name__)

class ProfileCreateSchema(BaseModel):
    title: Optional[str]
    experience_years: Optional[int]
    sector: Optional[str]
    skills: Optional[list]
    availability: Optional[str]
    location: Optional[str]

class ProfileUpdateSchema(BaseModel):
    title: Optional[str]
    experience_years: Optional[int]
    sector: Optional[str]
    skills: Optional[list]
    availability: Optional[str]
    location: Optional[str]
@profiles_bp.route('/upload-cv', methods=['POST'])
def upload_cv():
    """Upload and parse CV PDF from base64 data."""
    try:
        data = request.get_json()
        
        if not data or 'pdf_data' not in data:
            return jsonify({"error": "No PDF data provided"}), 400
        
        pdf_base64 = data['pdf_data']
        
        # Nettoyer le prefix si présent
        if pdf_base64.startswith('data:application/pdf;base64,'):
            pdf_base64 = pdf_base64.replace('data:application/pdf;base64,', '')
        
        # Créer extracteur instance et traiter le PDF
        extractor = PDFExtractor()
        profile = extractor.extract_pdf_info(pdf_base64)
        
    
        return jsonify(profile)
    
    except Exception as e:
        print(f"Error processing CV: {str(e)}")
        return jsonify({"error": "Failed to process CV file"}), 500
@profiles_bp.route('/linkedin-url', methods=['POST'])
def linkedin_url():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        data = request.get_json()
        raw_url = data.get('linkedinUrl', '').strip()
        
        if not raw_url:
            return jsonify({"error": "No URL provided"}), 400
        print(f"Raw URL received: {raw_url}")
        profile = extract_linkedin_scrapingbee(raw_url)
        if "error" in profile:
            return jsonify({
                "error": "Profile extraction failed",
                "details": profile["error"],
                "cleaned_url": raw_url,
                "alternative": "Try CV upload: /api/profiles/upload-cv"
            }), 400
        
        return jsonify(profile)

    except Exception as e:
        return jsonify({"error": "Server error"}), 500

@profiles_bp.route('/', methods=['POST'])
def create_profile():
    try:
        data = request.get_json()
        profile_data = ProfileCreateSchema(**data)
        new_profile = Profile(
            user_id=data.get('user_id'),  # Assuming user_id is passed
            title=profile_data.title,
            experience_years=profile_data.experience_years,
            sector=profile_data.sector,
            skills=profile_data.skills,
            availability=profile_data.availability,
            location=profile_data.location
        )
        db.session.add(new_profile)
        db.session.commit()
        return jsonify(new_profile.to_dict()), 201
    except ValidationError as e:
        return jsonify({"message": e.errors()}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@profiles_bp.route('/<int:profile_id>', methods=['GET'])
def get_profile(profile_id):
    profile = Profile.query.get(profile_id)
    if not profile:
        return jsonify({"message": "Profile not found"}), 404
    return jsonify(profile.to_dict())
@profiles_bp.route('/', methods=['GET'])

@profiles_bp.route('', methods=['GET'])
def list_profiles():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    query = Profile.query

    # Filtering example: sector
    sector = request.args.get('sector')
    if sector:
        query = query.filter_by(sector=sector)

    profiles_paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    profiles = [profile.to_dict() for profile in profiles_paginated.items]
    return jsonify({
        "profiles": profiles,
        "total": profiles_paginated.total,
        "page": profiles_paginated.page,
        "pages": profiles_paginated.pages
    })

@profiles_bp.route('/<int:profile_id>', methods=['PUT'])
def update_profile(profile_id):
    profile = Profile.query.get(profile_id)
    if not profile:
        return jsonify({"message": "Profile not found"}), 404
    try:
        data = request.get_json()
        profile_data = ProfileUpdateSchema(**data)
        for key, value in profile_data.dict(exclude_unset=True).items():
            setattr(profile, key, value)
        db.session.commit()
        return jsonify(profile.to_dict())
    except ValidationError as e:
        return jsonify({"message": e.errors()}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@profiles_bp.route('/<int:profile_id>', methods=['DELETE'])
def delete_profile(profile_id):
    profile = Profile.query.get(profile_id)
    if not profile:
        return jsonify({"message": "Profile not found"}), 404
    try:
        db.session.delete(profile)
        db.session.commit()
        return jsonify({"message": "Profile deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@profiles_bp.route('/current', methods=['GET'])
def get_current_user_profile():
    """Get current user's profile."""
    try:
        # Try to get user_id from JWT token if available
        user_id = None
        try:
            from flask_jwt_extended import get_jwt_identity

        except:
            # If no JWT, try to get from Authorization header
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.replace('Bearer ', '')
                try:
                    # Decode JWT manually using PyJWT
                    jwt_secret = os.getenv('JWT_SECRET_KEY', 'my-super-secret-jwt-key-12345')
                    decoded = jwt.decode(token, jwt_secret, algorithms=['HS256'])
                    user_id = decoded.get('sub')
                except:
                    pass
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        from app.models.User import User
        profile = Profile.query.filter_by(user_id=user_id).first()
        if not profile:
            # If no profile exists, return user data as profile
            user = User.query.get(user_id)
            if not user:
                return jsonify({"message": "User not found"}), 404
            # Create a profile-like response from user data
            user_profile = {
                "id": None,  # No profile ID yet
                "user_id": user.id,
                "title": None,
                "experience_years": None,
                "sector": None,
                "skills": None,
                "availability": None,
                "location": None,
                "data": {
                    "personalInfo": {
                        "title": None,
                        "name": f"{user.first_name} {user.last_name}",
                        "email": user.email,
                        "phone": user.phone,
                        "location": None,
                        "linkedin": user.linkedin_url
                    },
                    "summary": "",
                    "experience": [],
                    "education": [],
                    "skills": [],
                    "languages": [],
                    "certifications": []
                },
                "updated_at": user.created_at.isoformat() if user.created_at else None,
            }
            return jsonify(user_profile)
        return jsonify(profile.to_dict())
    except Exception as e:
        logger.error(f"Error getting current user profile: {str(e)}")
        return jsonify({"error": "Failed to get profile"}), 500

@profiles_bp.route('/save', methods=['POST'])
def save_profile():
    """Save or update profile data for authenticated user."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Récupérer l'user_id depuis les données ou le token JWT
        user_id = data.get('user_id')
        
        # Si user_id n'est pas dans les données, essayer de le récupérer du token JWT
        if not user_id:
            # Méthode 1: Depuis le token JWT (si vous utilisez flask_jwt_extended)
            try:
                from flask_jwt_extended import get_jwt_identity
                user_id = get_jwt_identity()
            except:
                pass
        
        # Si toujours pas d'user_id, retourner une erreur
        if not user_id:
            return jsonify({"error": "User ID required"}), 400

        # Vérifier si un profile_id est fourni pour la mise à jour
        profile_id = data.get('profile_id')
        
        if profile_id:
            # Mise à jour d'un profil existant
            profile = Profile.query.filter_by(id=profile_id, user_id=user_id).first()
            if not profile:
                return jsonify({"error": "Profile not found"}), 404
        else:
            # Création d'un nouveau profil
            profile = Profile(user_id=user_id)
            db.session.add(profile)

        # Mettre à jour les champs du profil
        profile.data = data
        
        # Mettre à jour les champs résumés si présents dans les données
        if data.get('personalInfo', {}).get('title'):
            profile.title = data['personalInfo']['title']
        elif data.get('current_title'):
            profile.title = data['current_title']
            
        if data.get('sumOfExperienceYears'):
            try:
                # Extraire le nombre d'années depuis la chaîne (ex: "16 ans" -> 16)
                years_str = data['sumOfExperienceYears']
                years_match = re.search(r'\d+', years_str)
                if years_match:
                    profile.experience_years = int(years_match.group())
            except (ValueError, TypeError):
                pass
        elif data.get('years_experience'):
            try:
                profile.experience_years = int(data['years_experience'])
            except (ValueError, TypeError):
                pass
                
        if data.get('sector'):
            profile.sector = data['sector']
            
        if data.get('skills'):
            profile.skills = data['skills']
            
        if data.get('personalInfo', {}).get('location'):
            profile.location = data['personalInfo']['location']
        elif data.get('location'):
            profile.location = data['location']

        # Champ pour le nom du profil (optionnel)
        if data.get('profile_name'):
            profile.profile_name = data['profile_name']

        db.session.commit()
        
        return jsonify({
            "message": "Profile saved successfully", 
            "profile": profile.to_dict(),
            "profile_id": profile.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving profile: {str(e)}")
        return jsonify({"error": "Failed to save profile"}), 500