import os
from flask import Blueprint, request, jsonify
from app.services.analysis import predict_cluster as predict_cluster_service   , mode_cluster as get_mode_cluster



cluster_bp = Blueprint("cluster", __name__)

@cluster_bp.route('/', methods=['POST'])
def predict_cluster():
    try:
        input_data = request.json
        if 'content' not in input_data:
            return jsonify({"error": "Invalid input, 'content' field is required"}), 400

        content = input_data['content']

        cluster = predict_cluster_service(content)

        return jsonify({"cluster": cluster}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
@cluster_bp.route('/mode', methods=['POST'])
def modeCluster():
    try:
        data = request.get_json()
        mode_cluster = get_mode_cluster(data)
        return jsonify({'modeCluster': mode_cluster}), 200

    except (TypeError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    
@cluster_bp.route('/list', methods=["GET"])
def get_clusters():
    clusters = {
        "0": "Korupsi",
        "1": "Pemerintahan",
        "2": "Kejahatan",
        "3": "Transportasi",
        "4": "Bisnis",
        "5": "Agama", 
        "6": "Finance",
        "7": "Politik"
    }
    
    return jsonify({
        "success": True,
        "clusters": clusters
    }), 200