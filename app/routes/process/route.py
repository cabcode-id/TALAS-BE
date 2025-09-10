from flask import Blueprint, request, jsonify
import pandas as pd
import numpy as np
import networkx as nx
from sklearn.metrics.pairwise import cosine_similarity
from app.utils.mainfunctions import completeDf, getClusters
from app.utils.llm import (
    getTitle, create_documents, summarize_article, analyze_article
)
from app.utils.pycuan import main as pycuan_main

process_bp = Blueprint("process", __name__)
@process_bp.route('/', methods=['POST'])
def processAll():
    try:
        data = request.get_json()

        if not isinstance(data, list):
            return jsonify({"error": "Input must be a list of news articles"}), 400
        
        df = pd.DataFrame(data)

        for col in ['title', 'content']:
            if col not in df.columns:
                return jsonify({"error": f"Input must contain {col} field"}), 400

        df = completeDf(df) # Dapatkan embedding, bersihin content, hoax, bias, ideology
        
        # Step 1: Cluster the articles
        embeddings = np.array(df['embedding'].to_list(), dtype=np.float32)
        similarity_threshold = 0.9
        similarity_matrix = cosine_similarity(embeddings)

        G = nx.Graph()
        for i in range(len(similarity_matrix)):
            for j in range(i + 1, len(similarity_matrix)):
                if similarity_matrix[i, j] >= similarity_threshold:
                    G.add_edge(i, j)

        clusters = [list(component) for component in nx.connected_components(G)]
        cluster_indices = [-1] * len(df)

        # Assign a unique cluster index to each group
        current_cluster_index = 0
        for cluster in clusters:
            for idx in cluster:
                cluster_indices[idx] = current_cluster_index
            current_cluster_index += 1

        # For unclustered items, assign them unique indices starting from current_cluster_index
        for idx, cluster_index in enumerate(cluster_indices):
            if cluster_index == -1:
                cluster_indices[idx] = current_cluster_index
                current_cluster_index += 1
        
        # Assign cluster indices to the DataFrame
        df['cluster_index'] = cluster_indices

        # Step 2: Process each cluster and generate the results
        results = []
        for cluster_index in range(current_cluster_index):
            # Filter rows belonging to the current cluster
            cluster_df = df[df['cluster_index'] == cluster_index]

            modeCluster = getClusters(cluster_df)  # Assuming getClusters processes per cluster
            # modeCluster = 6

            # Create documents for the current cluster
            cluster_documents = create_documents(cluster_df)
            title = getTitle(cluster_documents)

            if modeCluster == 6:
                stock_symbol = 'FTT-USD'
                start_date = '2022-11-14'
                end_date = '2023-11-14'
                last_actual_day, last_actual_opening_price, forecast_date, first_forecast_opening_price, price_difference, percentage_change, final_sentiment, final_weight = pycuan_main(str(title), stock_symbol, start_date, end_date)
                cuan_result = {
                    "last_actual_day": str(last_actual_day),
                    "last_actual_opening_price": last_actual_opening_price,
                    "forecast_date": str(forecast_date),
                    "first_forecast_opening_price": first_forecast_opening_price,
                    "price_difference": price_difference,
                    "percentage_change": percentage_change,
                    "final_sentiment": final_sentiment,
                    "final_weight": final_weight
                }
            else:
                cuan_result = None

            all_summary = summarize_article(cluster_documents)
            analysis = analyze_article(cluster_documents, cuan_result)

            # Append the results for the current cluster
            cluster_result = {
                'all_summary': all_summary,
                # 'summary_conservative': summary_conservative,
                'analyze': analysis,
                'modeCluster': modeCluster,
                'title': title
            }
            results.append(cluster_result)

        # Step 3: Return the results as a list
        return jsonify(results), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400