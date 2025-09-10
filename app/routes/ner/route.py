from flask import Blueprint, request, jsonify
import pandas as pd
from app.utils.ner import main as ner_main

ner_bp = Blueprint("ner", __name__)

@ner_bp.route('/', methods=['POST'])
def ner():
    try:
        data = request.get_json()

        df = pd.DataFrame(data)

        if 'content' not in df.columns:
            return jsonify({"error": "Each dictionary must contain a 'content' field"}), 400

        text_list = df['content'].tolist()

        predictions = ner_main(text_list)

        return jsonify(predictions), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400