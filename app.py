from flask import Flask, render_template, request, jsonify
import subprocess
import json

app = Flask(__name__, static_folder='public', template_folder='templates')

@app.route('/')
def home():
    return render_template('d4.html')

# Call AIChatter.py using <id> and <task>
@app.route('/api/desc/<id>/<task>')
def call_aichatter(id, task):
    try:
        result = subprocess.check_output(['python3', 'AIChatter.py', id, task])
        return result
    except subprocess.CalledProcessError as e:
        return str(e), 500

# Call temp.py using POST JSON input
@app.route('/api/temp', methods=['POST'])
def call_temp():
    try:
        input_data = request.get_json()
        result = subprocess.check_output(
            ['python3', 'temp.py'],
            input=json.dumps(input_data).encode(),
            stderr=subprocess.STDOUT
        )
        return result
    except subprocess.CalledProcessError as e:
        return jsonify({'error': e.output.decode()}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8000)
