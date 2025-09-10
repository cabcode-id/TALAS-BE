import os
from simpletransformers.ner import NERModel, NERArgs

def setup_environment():
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

def get_model(labels):
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the current script's directory
    model_path = os.path.join(script_dir, "..", "model", "ner")  # Construct absolute model path
    model_path = os.path.abspath(model_path)

    model_args = NERArgs()
    model_args.labels_list = labels
    model_args.do_lower_case = True

    return NERModel(model_type='distilbert', model_name=model_path, labels=labels, args=model_args, use_cuda=False)

def predict_text(model, text):
    if not isinstance(text, list):
        text = [text]
    predictions, raw_outputs = model.predict(text)
    return predictions
 
def filter_predictions(labels, predictions):
    filtered_predictions = [
    [{word: tag} for token in sentence for word, tag in token.items() if tag in labels and tag != 'O']
    for sentence in predictions
    ]
    return filtered_predictions

def main(text):
    setup_environment()
    labels = ['O', 'B-PER', 'I-PER', 'B-LOC', 'I-LOC', 'B-ORG', 'I-ORG']
    model = get_model(labels)
    predictions = predict_text(model, text)
    filtered_predictions = filter_predictions(labels, predictions)
    return filtered_predictions