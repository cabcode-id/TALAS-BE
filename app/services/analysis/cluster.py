import os
import numpy as np
import pandas as pd
from app.utils.mainfunctions import loadClusterModel ,  dfEmbedding, getClusters
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings

def predict_cluster(content: str) -> int:

    os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')

    Settings.embed_model = OpenAIEmbedding(model="text-embedding-ada-002")
    embedding = Settings.embed_model.get_text_embedding(content)
    embedding = np.array(embedding, dtype=np.float32).reshape(1, -1)

    kmeans = loadClusterModel()
    cluster = kmeans.predict(embedding)[0]

    return int(cluster)


def mode_cluster(data):

    if not isinstance(data, list):
        raise TypeError("Input must be a list of news articles")

    df = pd.DataFrame(data)
    for col in ['title', 'content', 'embedding']:
        if col not in df.columns:
            raise ValueError(f"Input must contain {col} field")
    df = dfEmbedding(df)

