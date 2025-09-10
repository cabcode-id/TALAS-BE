from flask import Blueprint, request, jsonify
from app.services.analysis import analyze_service

analyze_bp = Blueprint('analyze', __name__)

@analyze_bp.route('/', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        analysis = analyze_service(data)
        return jsonify({'analyze': analysis}), 200

    except (TypeError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500