from flask import Flask, render_template, jsonify
import subprocess

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('d4.html')

@app.route('/api/desc/<id>/<task>')
def get_description(id, task):
    try:
        result = subprocess.check_output(['python3', 'AIChatter.py', id, task])
        return result
    except subprocess.CalledProcessError as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True, port=8000)
