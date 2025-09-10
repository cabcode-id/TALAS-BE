from flask import Blueprint, request, jsonify
from app.services.analysis import generate_title_service

title_bp = Blueprint('title', __name__)
@title_bp.route('/', methods=['POST'])
def title():
    try:
        data = request.get_json()
        title = generate_title_service(data)
        return jsonify({'title': title}), 200

    except (TypeError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500