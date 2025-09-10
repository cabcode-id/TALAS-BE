from flask import Blueprint, request, jsonify
from app.services.analysis import cleaned_service 

cleaned_bp = Blueprint("cleaned", __name__)

@cleaned_bp.route('/', methods=['POST'])
def cleaned():
    try:
        input_data = request.json

        if 'content' not in input_data:
            return jsonify({"error": "Invalid input, 'content' field is required"}), 400

        content = input_data['content']

        cleaned = cleaned_service(content)
        
        return jsonify({"cleaned": cleaned}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400