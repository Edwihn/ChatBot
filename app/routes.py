from flask import Flask, render_template, Blueprint

bp = Blueprint('main', __name__)

@bp.route('/')
def inicio():
    return render_template('index.html')

bp.route('/prueba')
def test():
    return render_template('test.html')