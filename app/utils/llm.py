import pandas as pd
from llama_index.core import Settings, Document, VectorStoreIndex, SummaryIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
Settings.llm = OpenAI(model='gpt-4o-mini')
Settings.embed_model = OpenAIEmbedding(model="text-embedding-ada-002")

def getTitle(documents):
    query_engine = VectorStoreIndex.from_documents(documents).as_query_engine(llm=Settings.llm)
    titleQuery = """
    From the following articles, generate a single article title that summarizes the content of all articles.
    Be as factual, neutral, and objective as possible.
    Do not use prior knowledge.
    Include the important subjects in the title if there are any. 
    Use Indonesian language.
    """
    response = query_engine.query(titleQuery)
    return response.response

def create_documents(df):
    documents = []
    for index, row in df.iterrows():
        metadata = {'title': row['title']}

        if 'bias' in row and not pd.isnull(row['bias']):
            metadata['bias'] = row['bias']

        if 'hoax' in row and not pd.isnull(row['hoax']):
            metadata['hoax'] = row['hoax']

        if 'ideology' in row and not pd.isnull(row['ideology']):
            # metadata['ideology'] = 'liberalism' if row['ideology'] == 1 else 'conservative'
            metadata['ideology'] = row['ideology']

        document = Document(
            text=row['content'],
            doc_id=str(index),
            metadata=metadata,
            embedding=row['embedding']
        )
        documents.append(document)
    return documents


def create_summary(documents):
    if(documents == []):
        return "No articles written in this perspective."
    
    summarizeQuery = """
    Create a short, detailed, and factual summary of the articles.
    Include important informations from the articles. 
    Use the framework of a good paragraph that answers the what, when, who, where, which, and how inside the summary.
    
    metadata related to each article: 
    likelihood to be read from a narrow point of view (0: not biased/neutral, 1: biased), 
    likelihood of this article to be re-written into missleading hoaxes (0: is factual, 1: has more likely to be a hoax), 
    and whether it's writing style ideology (a bit provocative like a liberal (the closer the value to 1) or trying to maintain what is already exist like a conservative (the closer the value to 0))

    which are all detected using machine learning models are also included.
    
    Include both ideologies to the summary.
    Do NOT discuss about the article's hoax, bias, or political view. 
    Do NOT rely on previous knowledge.
    Use Indonesian language. 
    """

    summary_index = SummaryIndex.from_documents(documents, use_async=True)
    summary_query_engine = summary_index.as_query_engine(llm=Settings.llm, response_mode='tree_summarize')
    summary = summary_query_engine.query(summarizeQuery)
    return summary.response

def create_analysis(query_engine, cuan_result):
    compareQuery = """
    I have a collection of articles classified as either liberal or conservative. These articles all discuss the same event but from differing perspectives.
    Your task is to analyze a given query and generate a response summarizing how articles from each perspective address the topic. 
    
    Ensure the response follows this structure:
    Dari sisi Liberal: [Summarize key points using the language and tone of liberal articles (ideology value closer to 1). If no liberal perspective exists, return "there are no liberal perspectives."]
    Dari sisi Konservatif: [Summarize key points using the language and tone of conservative articles (ideology value closer to 0). If no conservative perspective exists, return "there are no conservative perspectives."]
    
    Follow these guidelines:
    Derive all information directly from the provided articles—do not rely on prior knowledge or external context.
    Keep summaries concise, factual, and reflective of the language and tone used in the articles. Avoid being too wordy.
    Highlight notable phrases or specific terminology unique to each perspective to showcase differences in framing or emphasis.
    Only include sections for perspectives present in the articles. If only one perspective is available, summarize that side alone.
    Format responses as concise paragraphs. Do not include editorial commentary, personal interpretation, or merge perspectives into one.
    Use Indonesian language.
    """
    
    cuanQuery = ""
    if cuan_result is not None:
        cuanQuery = """
        Create a finance analysis with these information. The articles have also been classified as finance related. These are the results from the finance analysis model:
        Last actual day: {last_actual_day}
        Last actual opening price: {last_actual_opening_price}
        Forecast date: {forecast_date}
        First forecast opening price: {first_forecast_opening_price}
        Difference between last actual day's price and first forecast date's price: {price_difference}
        Percentage change of price: {percentage_change}
        Final sentiment: {final_sentiment}
        Final weight: {final_weight}

        Ensure the response is concise and factual. Use Indonesian Language.
        """.format(**cuan_result)

    response = query_engine.query(compareQuery)

    # Initialize cuanResponse with an empty string to avoid errors
    cuanResponse = ""
    if cuanQuery:
        cuanResponse = query_engine.query(cuanQuery)
        cuanResponse = cuanResponse.response

    return response.response + cuanResponse  # Avoid accessing response2 if it's not set

def summarize_article(documents):
    all_docs = [document for document in documents]
    all_summary = create_summary(all_docs)

    return all_summary
    
def analyze_article(documents, cuan_result=None):
    query_engine = VectorStoreIndex.from_documents(documents).as_query_engine(llm=Settings.llm)

    analysis = create_analysis(query_engine, cuan_result)

    return analysis