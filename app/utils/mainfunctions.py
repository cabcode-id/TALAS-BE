import os
import sys
import re
import pickle

import numpy as np
import pandas as pd
import swifter
import tensorflow as tf
from keras.preprocessing.sequence import pad_sequences
from tensorflow.keras import preprocessing
from sklearn.metrics.pairwise import cosine_similarity

from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

# Configure Llama Index settings
Settings.llm = OpenAI(model='gpt-4o-mini')
Settings.embed_model = OpenAIEmbedding(model="text-embedding-ada-002")

# Fix TensorFlow preprocessing module reference
sys.modules['keras.src.preprocessing'] = preprocessing

def loadModel(model_path, model_name):
    script_dir = os.path.dirname(os.path.abspath(__file__))  
    abs_model_path = os.path.join(script_dir, model_path)  

    with open(os.path.join(abs_model_path, f"{model_name}_tokenizer.pkl"), 'rb') as f:
        tokenizer = pickle.load(f)

    interpreter = tf.lite.Interpreter(model_path=os.path.join(abs_model_path, f"{model_name}.tflite"))
    interpreter.allocate_tensors()
    return tokenizer, interpreter

def loadClusterModel():
    script_dir = os.path.dirname(os.path.abspath(__file__)) 
    cluster_model_path = os.path.join(script_dir, "..", "model", "cluster", "kmeans_8_cluster.pkl")  

    with open(cluster_model_path, 'rb') as f:
        kmeans = pickle.load(f)
    return kmeans

# Load models
kmeans = loadClusterModel()
bias_tokenizer, bias_interpreter = loadModel("../model/bias", "bias")
hoax_tokenizer, hoax_interpreter = loadModel("../model/hoax", "hoax")
ideology_tokenizer, ideology_interpreter = loadModel("../model/ideology", "ideology")

stopword_factory = StopWordRemoverFactory()
stopword = stopword_factory.create_stop_word_remover()
stemmer_factory = StemmerFactory()
stemmer = stemmer_factory.create_stemmer()

def preprocessText(text):
    text = str(text)

    # change text to lowercase
    text = text.lower()

    # change link with http/https patterns
    text = re.sub(r'http\S+', '', text)

    # remove hashtag and username
    text = re.sub(r'(@\w+|#\w+)', '', text)

    # remove character other than a-z and A-Z
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)

    # replace new line '\n' with space
    text = re.sub(r'\n', ' ', text)
    text = re.sub(r'\t', ' ', text)

    # remove stopword with sastrawi library
    text = stopword.remove(text)

    # do stemming with sastrawi library
    text = stemmer.stem(text)

    # removing more than one space
    text = re.sub(r'\s{2,}', ' ', text)

    return text

def predictWithModel(newsText, tokenizer, interpreter, maxLen):
    new_sequences = tokenizer.texts_to_sequences([newsText])
    new_padded = pad_sequences(new_sequences, maxlen=maxLen, padding='post', truncating='post')
    new_padded = new_padded.astype('float32')

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    interpreter.set_tensor(input_details[0]['index'], new_padded)
    interpreter.invoke()

    predictions = interpreter.get_tensor(output_details[0]['index'])
    return predictions

def predictBias(newsText):    
    predictions = predictWithModel(newsText, bias_tokenizer, bias_interpreter, 30)
    return float(predictions[0])

def predictHoax(newsText):
    predictions = predictWithModel(newsText, hoax_tokenizer, hoax_interpreter, 100)
    return float(predictions[0])

def predictIdeology(newsText):
    predictions =  predictWithModel(newsText, ideology_tokenizer, ideology_interpreter, 100)
    return float(predictions[0])

def dfEmbedding(df):
    df['embedding'] = df.apply(
            lambda row: row['embedding'] if isinstance(row.get('embedding'), (list, np.ndarray)) else Settings.embed_model.get_text_embedding(row['content']), 
            axis=1
    )
    return df

def completeDf(df):
    for col in ['bias', 'hoax', 'ideology', 'embedding', 'cleaned']:
        if col not in df.columns:
            df[col] = None

    mask = df['cleaned'].isnull() | (df['cleaned'] == '')

    df.loc[mask, 'cleaned'] = df.loc[mask, 'content'].swifter.apply(preprocessText)

    df = dfEmbedding(df)

    df['bias'] = df.swifter.apply(
        lambda row: row['bias'] if pd.notnull(row['bias']) else predictBias([row['cleaned']]),
        axis=1
    )

    df['hoax'] = df.swifter.apply(
        lambda row: row['hoax'] if pd.notnull(row['hoax']) else predictHoax([row['cleaned']]),
        axis=1
    )

    df['ideology'] = df.swifter.apply(
        lambda row: row['ideology'] if pd.notnull(row['ideology']) else predictIdeology([row['cleaned']]),
        axis=1
    )

    return df

def getClusters(df):
    X = np.array(df['embedding'].to_list(), dtype=np.float32)
    clusters = kmeans.predict(X)
    modeCluster = np.bincount(clusters).argmax()
    return int(modeCluster)

def topSimilarArticles(textEmbedding, df, n):
    similarities = cosine_similarity([textEmbedding],list(df['embedding']))[0]

    similarities = list(enumerate(similarities))
    topSimilar = sorted(similarities, key=lambda x: x[1], reverse=True)
    topSimilar = topSimilar[:n]

    article_idx = [i[0] for i in topSimilar]
    similarity_values = [i[1] for i in topSimilar]

    recommendations = df.iloc[article_idx].copy()
    recommendations['similarity'] = similarity_values
    return recommendations