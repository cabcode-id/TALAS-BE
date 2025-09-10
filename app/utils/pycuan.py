import joblib
from bs4 import BeautifulSoup
import nltk
import re
import unicodedata
from googletrans import Translator
import contractions
import pandas as pd
from keras.models import load_model
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
import os
import numpy as np
from sklearn.preprocessing import StandardScaler
import yfinance as yf

def loadnltk():
    # Ensure NLTK loads from the correct path without modifying working directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    nltk.data.path.append(os.path.join(script_dir, "..", "model", "nltk"))

def load_models():
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Get current script's directory
    base_path = os.path.join(script_dir, "..", "model", "pycuan")  # Only look in model/pycuan/

    def find_file(filename):
        file_path = os.path.join(base_path, filename)
        if os.path.exists(file_path):
            return file_path
        raise FileNotFoundError(f"{filename} not found in {base_path}")

    rf_classifier = joblib.load(find_file("random_forest_model.joblib"))
    tfidf_vectorizer = joblib.load(find_file("tfidf_vectorizer.joblib"))
    model = load_model(find_file("time_series_model.h5"))

    return tfidf_vectorizer, rf_classifier, model

# Fungsi-fungsi pra-pemrosesan teks
def strip_html_tags(text):
    # Fungsi ini menghapus tag HTML dari teks menggunakan BeautifulSoup
    soup = BeautifulSoup(text, "html.parser")
    [s.extract() for s in soup(['iframe', 'script'])]
    stripped_text = soup.get_text()
    stripped_text = re.sub(r'[\r|\n|\r\n]+', '\n', stripped_text)
    return stripped_text

def remove_accented_chars(text):
    # Fungsi ini menghapus karakter aksen dari teks menggunakan normalisasi Unicode
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8', 'ignore')
    return text

# Fungsi pra-pemrosesan teks khusus Bahasa Indonesia
def preprocess_text_sastrawi(text):
    # Fungsi ini menggunakan Sastrawi untuk menghapus stop word dan melakukan stemming pada teks Bahasa Indonesia
    factory1 = StopWordRemoverFactory()
    stopword_sastrawi = factory1.create_stop_word_remover()

    factory2 = StemmerFactory()
    stemmer_sastrawi = factory2.create_stemmer()

    tokens = nltk.word_tokenize(text)
    tokens = [stopword_sastrawi.remove(token) for token in tokens]
    tokens = [stemmer_sastrawi.stem(token) for token in tokens if token != '']
    return " ".join(tokens)

def pre_process_text(text, language):
    # Fungsi ini melakukan pra-pemrosesan teks seperti mengonversi teks ke huruf kecil,
    # menghapus tag HTML, karakter aksen, kontraksi, dan karakter khusus
    text = text.lower()
    text = strip_html_tags(text)
    text = text.translate(text.maketrans("\n\t\r", "   "))
    text = remove_accented_chars(text)
    text = contractions.fix(text)
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text, re.I | re.A)
    text = re.sub(' +', ' ', text)
    if language == 'indonesian':
        text = preprocess_text_sastrawi(text)
    return text

def translate_text(text, dest_language='en'):
    translator = Translator()
    translated_text = translator.translate(text, dest=dest_language).text
    return translated_text

def sentiment_analysis(text, tfidf_vectorizer, rf_classifier, language='indonesian'):
    translated_text = translate_text(text, dest_language='en')
    translated_text_tfidf = tfidf_vectorizer.transform([translated_text])
    sentiment_probability = rf_classifier.predict_proba(translated_text_tfidf)[0, 1]

    return sentiment_probability

def get_stock_data(stock_symbol, start_date, end_date):
    df = yf.download(stock_symbol, start=start_date, end=end_date)
    return df

def normalize_data(data):
    scaler = StandardScaler()
    normalized_data = scaler.fit_transform(np.array(data).reshape(-1, 1))
    return normalized_data

def prepare_time_series_data(normalized_data, seq_length=30):
    X_data = []
    for i in range(len(normalized_data) - seq_length):
        X_data.append(normalized_data[i:i + seq_length])
    X_new_data = np.array(X_data)
    return X_new_data

def predict_time_series(model, X_data):
    predictions = model.predict(X_data)
    return predictions

def forecast_stock_prices(model, normalized_data, forecast_days=5, seq_length=30):
    X_forecast = np.copy(normalized_data[-seq_length:])
    forecasted_values = []
    for _ in range(forecast_days):
        forecasted_value = model.predict(X_forecast.reshape(1, seq_length, 1))
        forecasted_values.append(forecasted_value[0, 0])
        X_forecast = np.roll(X_forecast, -1)
        X_forecast[-1] = forecasted_value
    return forecasted_values

def calculate_percentage_change(last_actual_price, forecasted_price):
    price_difference = forecasted_price - last_actual_price
    percentage_change = price_difference / last_actual_price
    return price_difference, percentage_change

def combine_weights(sentiment_probability, time_series_weight, sentiment_ratio=0.65):
    time_series_ratio = 1 - sentiment_ratio
    combined_weight = (sentiment_ratio * sentiment_probability + time_series_ratio * time_series_weight)
    return combined_weight

def main(new_text, stock_symbol, start_date, end_date):

    tfidf_vectorizer, rf_classifier, model = load_models()
    sentiment_probability = sentiment_analysis(new_text, tfidf_vectorizer, rf_classifier)
    
    stock_data = get_stock_data(stock_symbol, start_date, end_date)
    last_actual_day = stock_data.index[-1]
    last_actual_opening_price = stock_data['Open'].iloc[-1].item()
    
    normalized_data = normalize_data(stock_data['Open'].values)
    forecasted_values = forecast_stock_prices(model, normalized_data)
    first_forecast_opening_price = forecasted_values[0]
    
    forecast_days = 5
    forecast_dates = pd.date_range(last_actual_day, periods=forecast_days + 1)[1:]
    
    price_difference, percentage_change = calculate_percentage_change(last_actual_opening_price, first_forecast_opening_price)
    
    weighted_metric = (percentage_change + 1) / 2
    final_weight = combine_weights(sentiment_probability, weighted_metric)
    final_sentiment = "Positive📈" if final_weight > 0.5 else "Negative📉"
    
    return last_actual_day, last_actual_opening_price, forecast_dates[0], first_forecast_opening_price, price_difference, percentage_change, final_sentiment, final_weight

# if __name__ == "__main__":
#         # sentiment
#     new_text = "Revision of Subsidized Fertilizer Policy, Now Farmers Can Redeem Using KTP"

#     # time series
#     stock_symbol = 'FTT-USD' # tambahkan .JK untuk bursa efek indonesia (BBCA.JK) | -USD untuk global
#     start_date = '2022-11-14'
#     end_date = '2023-11-14'

#     print(main(new_text, stock_symbol, start_date, end_date))
