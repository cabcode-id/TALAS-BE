import pandas as pd
from app.utils.llm import getTitle, create_documents
from app.utils.mainfunctions import dfEmbedding

def generate_title_service(data):

    if not isinstance(data, list):
        raise TypeError("Input must be a list of news articles")
    
    df = pd.DataFrame(data)
    for col in ['title', 'content']:
        if col not in df.columns:
            raise ValueError(f"Input must contain {col} field")
    
    df = dfEmbedding(df)
    
    documents = create_documents(df)
    return getTitle(documents)
