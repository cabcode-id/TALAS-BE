from flask import Blueprint, request, jsonify
import pandas as pd
from app.services.analysis import embedding_service


embedding_bp = Blueprint('embedding', __name__)
@embedding_bp.route('/', methods=['POST'])
def get_embedding():
    try:
        data = request.get_json()    
        embed = embedding_service(data)
        
        return jsonify({"embedding": embed}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400