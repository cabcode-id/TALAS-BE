from flask import Blueprint, request, jsonify
from app.utils.mainfunctions import (
    predictHoax
)

hoax_bp = Blueprint("hoax", __name__)

@hoax_bp.route('/', methods=['POST'])
def hoaxAPI():
    try:
        input_data = request.json
        if 'content' not in input_data:
            return jsonify({"error": "Invalid input, 'content' field is required"}), 400

        content = input_data['content']
        
        bias = predictHoax(content)

        return jsonify({"hoax": bias}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400