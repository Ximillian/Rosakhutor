from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_httpauth import HTTPBasicAuth
from threading import Lock

app = Flask(__name__, template_folder='../templates')
app.secret_key = 'super-secret-key'
auth = HTTPBasicAuth()

users = {
    "operator": "password"
}

@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username

# Инициализация глобальных объектов (будет передаваться из main)
ranking_engine = None
audit_logger = None
state_store = None

@app.route('/')
@auth.login_required
def index():
    return render_template('index.html')

@app.route('/api/top')
@auth.login_required
def get_top():
    top = ranking_engine.get_top_suspicious()
    result = []
    for ticket, data in top:
        result.append({
            'ticket_number': ticket,
            'max_score': round(data['max_score'], 4),
            'last_score': round(data['last_score'], 4),
            'last_event_time': data['last_event_time'].strftime('%Y-%m-%d %H:%M:%S'),
            'blocked': data['blocked']
        })
    return jsonify(result)

@app.route('/api/block', methods=['POST'])
@auth.login_required
def block():
    ticket = request.json.get('ticket')
    operator = auth.current_user()
    state_store.block_ticket(ticket)
    audit_logger.log(operator, 'block', ticket, 'Blocked via operator action')
    return jsonify({'status': 'ok'})

def start_web(host, port, debug, rank_eng, audit, store):
    global ranking_engine, audit_logger, state_store
    ranking_engine = rank_eng
    audit_logger = audit
    state_store = store
    app.run(host=host, port=port, debug=debug)