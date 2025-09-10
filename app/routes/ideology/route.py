from flask import Blueprint, request, jsonify
from app.utils.mainfunctions import (
    predictIdeology
)

ideology_bp = Blueprint("ideology", __name__)

@ideology_bp.route('/', methods=['POST'])
def ideologyAPI():
    try:
        input_data = request.json
        if 'content' not in input_data:
            return jsonify({"error": "Invalid input, 'content' field is required"}), 400

        content = input_data['content']
        
        ideology = predictIdeology(content)

        return jsonify({"ideology": ideology}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400