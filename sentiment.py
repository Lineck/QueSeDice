from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoConfig
import re

# Cargar modelo y tokenizador
MODEL = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
tokenizer = AutoTokenizer.from_pretrained(MODEL, use_fast=False)
model = AutoModelForSequenceClassification.from_pretrained(MODEL)
config = AutoConfig.from_pretrained(MODEL)

def roberta(text):
    try:
        # El texto se tokeniza y se convierte en un formato numérico que el modelo puede procesar.
        encoded_text = tokenizer(text, return_tensors='pt')
        # Procesar el texto con el modelo
        output = model(**encoded_text)
        # Identificar el sentimiento predominante
        index_of_sentiment = output.logits.argmax().item()
        # Convertir el índice a una etiqueta de sentimiento
        sentiment = config.id2label[index_of_sentiment]

        return sentiment
    except Exception as e:
        print(f"Error procesando el texto: {e}")
        return None

def preprocess(text):
    # Reemplazar etiquetas HTML de enlaces (incluyendo texto visible)
    text = re.sub(r'<a\s+href=["\']https?://\S+["\']>(https?://\S+)</a>', 'http', text)

    # Reemplazar menciones (@usuario) por @user
    text = " ".join(['@user' if t.startswith('@') else t for t in text.split()])

    # Reemplazar enlaces restantes (URLs simples)
    text = re.sub(r'(https?://\S+|www\.\S+)', 'http', text)

    return text
