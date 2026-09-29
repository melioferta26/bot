from flask import Flask, render_template, jsonify
from database import get_dashboard_data
from scraper import run_bot_job
import threading

app = Flask(__name__)

@app.route('/')
def dashboard():
    stats, logs = get_dashboard_data()
    return render_template('index.html', stats=stats, logs=logs)

@app.route('/run-now', methods=['POST'])
def trigger_bot():
    # Ejecuta el scraper en un hilo separado para no bloquear el panel web
    thread = threading.Thread(target=run_bot_job)
    thread.start()
    return jsonify({'status': 'started', 'message': 'Bot ejecutándose en segundo plano...'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)