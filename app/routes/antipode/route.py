from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
from app.utils.mainfunctions import dfEmbedding, topSimilarArticles
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings

Settings.embed_model = OpenAIEmbedding(model="text-embedding-ada-002")

antipode_bp = Blueprint('antipode', __name__)

@antipode_bp.route('/', methods=['POST'])
def antipode():
    try:
        data = request.get_json()

        # Input harus {'article': {'title': '...', 'content': '...'}, 'df': [{'title': '...', 'content': '...'}, ...]}
        if 'article' not in data or 'df' not in data:
            return jsonify({"error": "Request must contain 'article' and 'df' fields"}), 400

        # Extract article and dataframe
        article = data['article']
        df_data = data['df']

        # Validate the article
        if not isinstance(article, dict) or 'content' not in article:
            return jsonify({"error": "Article must be a dictionary with 'content' fields"}), 400

        # Validate the DataFrame input
        if not isinstance(df_data, list):
            return jsonify({"error": "df must be a list of news articles"}), 400

        df = pd.DataFrame(df_data)

        # Ensure the DataFrame contains the required fields
        for col in ['title', 'content']:
            if col not in df.columns:
                return jsonify({"error": f"df must contain {col} field"}), 400

        # Compute embedding for the article
        if 'embedding' not in article or not isinstance(article['embedding'], (list, np.ndarray)):
            article['embedding'] = Settings.embed_model.get_text_embedding(article['content'])

        # Dapatkan embedding dari df jika belum ada.
        df = dfEmbedding(df)

        # Calculate antipode embedding for the input article
        antipode_embedding = -np.array(article['embedding'])

        # Cari 2 artikel dalam df yang paling mirip dengan antipoda
        recommendations = topSimilarArticles(antipode_embedding, df, 2)
        return jsonify(recommendations['title'].tolist()), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400