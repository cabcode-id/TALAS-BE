import pandas as pd
from app.utils.mainfunctions import preprocessText  

def cleaned_service(content):

    if isinstance(content, str):
        return preprocessText(content)

    elif isinstance(content, list):
        if not all(isinstance(item, str) for item in content):
            raise ValueError("All items in the 'content' list must be strings")
        
        df = pd.DataFrame({'content': content})
        df['cleaned'] = df['content'].swifter.apply(preprocessText)
        return df['cleaned'].tolist()

    else:
        raise TypeError("'content' must be either a string or a list of strings")
