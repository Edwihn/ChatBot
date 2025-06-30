from flask import Flask, render_template, Blueprint, request, jsonify
from app.spacy import process_user_input

bp = Blueprint('main', __name__)

@bp.route('/')
def inicio():
    return render_template('index.html')

@bp.route('/prueba')
def test():
    return render_template('test.html')

@bp.route('/input', methods=['POST'])
def chatbot_response():
    user_message = request.json.get('message')
    category = request.json.get('category')  # si tu bot usa categorías
    response = process_user_input(user_message, category)
    if not response:
        response = "Lo siento, no tengo una respuesta para eso." 
    return jsonify({"response": response})

