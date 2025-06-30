import spacy
from app.db import chatbot_db
nlp = spacy.load("es_core_news_md")

def process_user_input(message, category):
    doc = nlp(message)
    keywords = [token.lemma_ for token in doc if token.is_alpha and not token.is_stop]

    collection = chatbot_db[category]  # Por ejemplo, 'recomendaciones'

    # Buscar documentos que contengan alguna de las keywords
    query = {"$text": {"$search": " ".join(keywords)}}
    results = list(collection.find(query))

    if results:
        return results[0]["respuesta"]
    else:
        return "Lo siento, no encontré una respuesta para eso."
