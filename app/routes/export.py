from flask import Blueprint, request, jsonify
from app.utils.export_generator import generate_export

export_bp = Blueprint('export', __name__)

@export_bp.route('/profile', methods=['POST'])
def export_profile():
    """Export profile to file."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    format_type = data.get('format', 'csv')  # Default to CSV
    if format_type not in ['csv', 'pdf']:
        return jsonify({"error": "Format must be csv or pdf"}), 400
    
    return generate_export(data, format_type)