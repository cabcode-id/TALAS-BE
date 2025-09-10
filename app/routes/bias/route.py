import os
from flask import Blueprint, request, jsonify
from app import db
from app.utils.mainfunctions import (
    predictBias,
)

bias_bp = Blueprint("bias", __name__)

@bias_bp.route('/', methods=['POST'])
def biasAPI():
    try:
        input_data = request.json
        if 'content' not in input_data:
            return jsonify({"error": "Invalid input, 'content' field is required"}), 400

        content = input_data['content']
        
        bias = predictBias(content)

        return jsonify({"bias": bias}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400