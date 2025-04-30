from flask import Flask, request, jsonify
from flask_cors import CORS
from auth import check_auth, admin_password
from metrics import get_metrics
from logs import get_logs

app = Flask(__name__)
CORS(app)

@app.route('/metrics', methods=['GET'])
def metrics():
    if not check_auth(request):
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(get_metrics())

@app.route('/logs/<container_name>', methods=['GET'])
def logs(container_name):
    if not check_auth(request):
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'logs': get_logs(container_name)})

@app.route('/auth', methods=['POST'])
def auth():
    data = request.json
    if data.get('password') == admin_password:
        return jsonify({'success': True})
    return jsonify({'success': False}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Only local access
