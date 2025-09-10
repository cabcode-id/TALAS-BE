
from flask import Blueprint, request, jsonify
from app.services.analysis import separate_service

separate_bp = Blueprint("separate", __name__)

@separate_bp.route('/', methods=['POST'])
def separate_route():
    try:
        data = request.get_json()
        cluster_indices = separate_service(data)
        return jsonify({"separate": cluster_indices}), 200

    except (TypeError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
