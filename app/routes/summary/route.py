import pandas as pd
from flask import Blueprint, request, jsonify
from app.services.analysis import summarize_service


summary_bp = Blueprint("summary", __name__)

@summary_bp.route('/', methods=['POST'])
def summary():
    try:
        data = request.get_json()
        all_summary = summarize_service(data)
        return jsonify({'all_summary': all_summary}), 200

    except (TypeError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500