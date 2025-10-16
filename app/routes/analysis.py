from flask import Blueprint, request, jsonify
from app.services.profile_analyzer import ProfileAnalyzer

analysis_bp = Blueprint('analysis', __name__)
analyzer = ProfileAnalyzer()

@analysis_bp.route('/analyze', methods=['POST'])
def analyze_profile():
    """Analyze a profile and provide insights"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No profile data provided"}), 400
    
    analysis = analyzer.analyze_profile(data)
    return jsonify(analysis)

@analysis_bp.route('/compare', methods=['POST'])
def compare_profiles():
    """Compare multiple profiles"""
    data = request.get_json()
    if not data or not isinstance(data, list) or len(data) < 2:
        return jsonify({"error": "Please provide at least 2 profiles to compare"}), 400
    
    comparisons = []
    for profile in data:
        analysis = analyzer.analyze_profile(profile)
        comparisons.append({
            "name": profile.get("name", "Unnamed"),
            "score": analysis["score"],
            "experience_level": analysis["experience_level"],
            "strengths": analysis["strengths"][:3],  # Top 3 strengths
            "skill_gaps": analysis["skill_gaps"][:3]  # Top 3 skill gaps
        })
    
    # Trier par score
    comparisons.sort(key=lambda x: x["score"], reverse=True)
    
    return jsonify({
        "comparisons": comparisons,
        "best_candidate": comparisons[0] if comparisons else None
    })