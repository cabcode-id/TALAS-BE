import pandas as pd
from app.utils.mainfunctions import dfEmbedding

def embedding_service(data):
    if isinstance(data, dict):  
        data = [data]
    elif not isinstance(data, list):
        raise TypeError("Input must be a list of news articles or a single article")
    
    df = pd.DataFrame(data)
    
    if 'content' not in df.columns:
        raise ValueError("Input must contain 'content' field")
    
    df = dfEmbedding(df)
    
    return df['embedding'].tolist()                                                                                                          