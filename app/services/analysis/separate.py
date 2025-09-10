import pandas as pd
import numpy as np
import networkx as nx
from app.utils.mainfunctions import dfEmbedding
from sklearn.metrics.pairwise import cosine_similarity

def separate_service(data, similarity_threshold=0.9):

    if not isinstance(data, list):
        raise TypeError("Input must be a list of news articles")
    
    df = pd.DataFrame(data)

    for col in ['title', 'content', 'embedding']:
        if col not in df.columns:
            raise ValueError(f"Input must contain {col} field")
    

    df = dfEmbedding(df)
    embeddings = np.array(df['embedding'].to_list(), dtype=np.float32)


    similarity_matrix = cosine_similarity(embeddings)


    G = nx.Graph()
    for i in range(len(similarity_matrix)):
        for j in range(i + 1, len(similarity_matrix)):
            if similarity_matrix[i, j] >= similarity_threshold:
                G.add_edge(i, j)
 
    clusters = [list(component) for component in nx.connected_components(G)]
    cluster_indices = [-1] * len(df)

    current_cluster_index = 0
    for cluster in clusters:
        for idx in cluster:
            cluster_indices[idx] = current_cluster_index
        current_cluster_index += 1


    for idx, cluster_index in enumerate(cluster_indices):
        if cluster_index == -1:
            cluster_indices[idx] = current_cluster_index
            current_cluster_index += 1

    return cluster_indices
