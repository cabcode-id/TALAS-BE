import pandas as pd
from app.utils.llm import create_documents, analyze_article
from app.utils.mainfunctions import completeDf

def analyze_service(data):

    if not isinstance(data, list):
        raise TypeError("Input must be a list of news articles")
    
    df = pd.DataFrame(data)
    for col in ['title', 'content', 'embedding']:
        if col not in df.columns:
            raise ValueError(f"Input must contain {col} field")

    df = completeDf(df)
    
    documents = create_documents(df)
    analysis = analyze_article(documents)
    return analysis
