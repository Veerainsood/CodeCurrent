from flask import Flask, send_from_directory, jsonify
import subprocess

app = Flask(__name__, static_folder='public')

@app.route('/')
def index():
    return send_from_directory('public', 'd4.html')

@app.route('/api/desc/<id>/<task>')
def run_script(id, task):
    try:
        result = subprocess.check_output(['python3', 'AIChatter.py', id, task])
        return result
    except subprocess.CalledProcessError as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True, port=8000)
