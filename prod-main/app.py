from flask import Flask, send_from_directory, jsonify
import json
import os

app = Flask(__name__, static_folder='.')

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

@app.route('/api/products')
def get_products():
    with open('data.json', 'r') as f:
        data = json.load(f)
    return jsonify(data)

@app.route('/api/cart', methods=['GET', 'POST'])
def cart():
    return jsonify({"items": []})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
