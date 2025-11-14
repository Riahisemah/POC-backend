from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models.Match import Match
from app.models.Profile import Profile
from app.models.Opportunity import Opportunity
from app.services.matching_service import MatchingService
from app import db
from pydantic import BaseModel, ValidationError
from typing import Optional
import traceback
import logging
logger = logging.getLogger(__name__)

matches_bp = Blueprint('matches', __name__)
matching_service = MatchingService()  # ← ULTRA INTELLIGENT !

class MatchCreateSchema(BaseModel):
    profile_id: int
    opportunity_id: int
    score: Optional[float]
    status: Optional[str]

class MatchUpdateSchema(BaseModel):
    score: Optional[float]
    status: Optional[str]

# ===============================================
# ROUTES CRUD CLASSIQUES (INCHANGÉES)
# ===============================================

@matches_bp.route('/', methods=['POST'])
#@jwt_required()
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
#@jwt_required()
def get_match(match_id):
    match = Match.query.get(match_id)
    if not match:
        return jsonify({"message": "Match not found"}), 404
    return jsonify(match.to_dict())

@matches_bp.route('/', methods=['GET'])
#@jwt_required()
def list_matches():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    query = Match.query

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
#@jwt_required()
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
#@jwt_required()
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

# ===============================================
# ROUTES ULTRA-INTELLIGENTES 🚀
# ===============================================

@matches_bp.route('/calculate/<int:opportunity_id>', methods=['POST'])
def calculate_matches_for_opportunity(opportunity_id):
    """
    🤖 Calcule les MEILLEURS MATCHES ULTRA-INTELLIGENTS pour une opportunité
    Compatible avec l'ancien service (même structure de retour)
    """
    try:
        # Vérifier opportunité
        opportunity = Opportunity.query.get(opportunity_id)
        if not opportunity:
            return jsonify({"message": "Opportunity not found"}), 404

        # Paramètres avancés
        limit = request.args.get('limit', 20, type=int)  # Plus de résultats par défaut
        min_score = request.args.get('min_score', 0, type=float)
        include_insights = request.args.get('insights', 'false').lower() == 'true'  # Bonus ML insights

        # 🤖 CALCUL ULTRA-INTELLIGENT
        matches = matching_service.calculate_matches_for_opportunity(opportunity_id, limit)

        # Formatage enrichi avec insights ML
        filtered_matches = []
        for match_data in matches:
            if match_data['score'] >= min_score:
                profile = match_data['profile']
                
                # Structure compatible avec l'ancien service
                match_response = {
                    'profile_id': profile.id,
                    'score': match_data['score'],
                    'profile': {
                        'id': profile.id,
                        'title': profile.title or '',
                        'experience_years': profile.experience_years or 0,
                        'sector': profile.sector or '',
                        'skills': profile.skills if isinstance(profile.skills, list) else [],
                        'location': profile.location or '',
                        'availability': profile.availability or 'unknown'
                    }
                }
                
                # 🎯 BONUS : Insights ML si demandé
                if include_insights:
                    try:
                        ml_insights = matching_service.get_ml_insights(profile, opportunity)
                        match_response['ml_insights'] = {
                            'skill_similarity': round(ml_insights['skill_similarity'], 1),
                            'semantic_similarity': round(ml_insights['semantic_similarity'], 1),
                            'confidence': round(ml_insights['confidence'] * 100, 1),
                            'top_entities': ml_insights['top_entities']
                        }
                    except:
                        pass  # Graceful fallback
                
                filtered_matches.append(match_response)

        # Réponse enrichie
        response = {
            'opportunity_id': opportunity_id,
            'matches': filtered_matches,
            'total_matches': len(filtered_matches),
            'ai_engine': 'UltraIntelligentMatchingService v2.0',
            'calculation_time': 'instant'  # Cache ML
        }
        
        # Statistiques intelligentes
        if filtered_matches:
            scores = [m['score'] for m in filtered_matches]
            response.update({
                'avg_score': round(sum(scores) / len(scores), 1),
                'top_score': max(scores),
                'confidence_range': f"{min(scores):.1f} - {max(scores):.1f}"
            })
        
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"UltraIntelligent Error: {str(e)}")
        traceback.print_exc()
        return jsonify({"message": f"AI Error: {str(e)}"}), 500

@matches_bp.route('/auto-match', methods=['POST'])
#@jwt_required()
def auto_match_all():
    """
    🤖 Auto-matching ULTRA-INTELLIGENT pour TOUTES les opportunités
    """
    try:
        # Paramètres avancés
        min_score = request.args.get('min_score', 60.0, type=float)  # Seuil plus élevé
        limit_per_opp = request.args.get('limit_per_opp', 15, type=int)
        save_to_db = request.args.get('save_to_db', 'true').lower() == 'true'
        
        # 🤖 Lancement du matching IA
        result = matching_service.auto_match_all_opportunities(min_score)
        
        response = {
            'message': '🚀 Auto-matching ULTRA-INTELLIGENT terminé !',
            'ai_engine': 'UltraIntelligentMatchingService',
            'result': result,
            'min_score': min_score,
            'quality_threshold': 'AI-powered semantic matching'
        }
        
        if save_to_db:
            response['database'] = 'Matches sauvegardés avec scores IA'
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Auto-match AI Error: {str(e)}")
        return jsonify({"message": f"AI Auto-matching failed: {str(e)}"}), 500

@matches_bp.route('/smart-match/<int:profile_id>/<int:opportunity_id>', methods=['GET'])
def smart_single_match(profile_id, opportunity_id):
    """
    🧠 Match ULTRA-INTELLIGENT pour un seul profil/opportunité
    NOUVEAU ENDPOINT pour tests rapides
    """
    try:
        profile = Profile.query.get(profile_id)
        opportunity = Opportunity.query.get(opportunity_id)
        
        if not profile or not opportunity:
            return jsonify({"message": "Profile or Opportunity not found"}), 404
        
        # 🤖 Calcul IA
        score = matching_service.calculate_match_score(profile, opportunity)
        
        # Bonus : Insights détaillés
        insights = matching_service.get_ml_insights(profile, opportunity)
        
        return jsonify({
            'profile_id': profile_id,
            'opportunity_id': opportunity_id,
            'ai_score': score,
            'ml_insights': {
                'skill_similarity': round(insights['skill_similarity'], 1),
                'semantic_similarity': round(insights['semantic_similarity'], 1),
                'confidence': f"{round(insights['confidence'] * 100, 1)}%",
                'recommendation': '🟢 EXCELLENT' if score >= 80 else '🟡 BON' if score >= 60 else '🟠 MOYEN'
            },
            'cache_status': 'hit' if f"p{profile_id}_o{opportunity_id}" in matching_service.profile_cache else 'miss'
        }), 200
        
    except Exception as e:
        return jsonify({"message": f"Smart match error: {str(e)}"}), 500

@matches_bp.route('/ai-insights/<int:profile_id>/<int:opportunity_id>', methods=['GET'])
def get_ai_insights(profile_id, opportunity_id):
    """
    🎯 Insights ML détaillés pour un match
    """
    try:
        profile = Profile.query.get(profile_id)
        opportunity = Opportunity.query.get(opportunity_id)
        
        if not profile or not opportunity:
            return jsonify({"message": "Not found"}), 404
        
        insights = matching_service.get_ml_insights(profile, opportunity)
        
        return jsonify({
            'profile_id': profile_id,
            'opportunity_id': opportunity_id,
            'ai_analysis': insights,
            'engine': 'spaCy + TF-IDF + Cosine Similarity'
        }), 200
        
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@matches_bp.route('/top-matches/<int:opportunity_id>', methods=['GET'])
def get_top_matches(opportunity_id):
    """
    🏆 Top 5 matches ULTRA-INTELLIGENTS (endpoint rapide)
    """
    try:
        opportunity = Opportunity.query.get(opportunity_id)
        if not opportunity:
            return jsonify({"message": "Opportunity not found"}), 404
        
        matches = matching_service.calculate_matches_for_opportunity(opportunity_id, limit=5)
        
        top_matches = []
        for match_data in matches:
            profile = match_data['profile']
            top_matches.append({
                'rank': len(top_matches) + 1,
                'profile_id': profile.id,
                'name': profile.data.get('personalInfo', {}).get('name', 'N/A') if profile.data else 'N/A',
                'score': match_data['score'],
                'title': profile.title or 'N/A',
                'ai_recommendation': '⭐' * int(match_data['score'] / 20)
            })
        
        return jsonify({
            'opportunity_id': opportunity_id,
            'top_matches': top_matches,
            'ai_engine': 'UltraIntelligent v2.0'
        }), 200
        
    except Exception as e:
        return jsonify({"message": str(e)}), 500

# ===============================================
# ENDPOINTS DE DEBUG / ADMIN
# ===============================================

@matches_bp.route('/service-status', methods=['GET'])
def service_status():
    """🚦 Statut du service IA"""
    return jsonify({
        'service': 'UltraIntelligentMatchingService',
        'status': '🟢 ACTIVE',
        'cache_size': len(matching_service.profile_cache),
        'spacy_loaded': nlp is not None,
        'features': [
            '🤖 ML Vectoriel (TF-IDF)',
            '🧠 spaCy NLP Français', 
            '📊 Cosine Similarity',
            '🗺️ Géolocalisation TN',
            '⚡ Cache intelligent'
        ]
    })

@matches_bp.route('/clear-cache', methods=['POST'])
#@jwt_required()
def clear_cache():
    """🧹 Vider le cache ML"""
    matching_service.profile_cache.clear()
    matching_service.opportunity_cache.clear()
    return jsonify({"message": "Cache vidé", "cache_size": 0}), 200