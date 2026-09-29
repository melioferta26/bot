import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def log_event(status, message, product_name=None, product_url=None, affiliate_url=None):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO logs (status, message, product_name, product_url, affiliate_url)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (status, message, product_name, product_url, affiliate_url)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error escribiendo en BD: {e}")

def increment_stat(stat_type):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        if stat_type == 'run':
            cur.execute("UPDATE bot_stats SET total_runs = total_runs + 1, last_run = NOW() WHERE id = 1")
        elif stat_type == 'success':
            cur.execute("UPDATE bot_stats SET successful_sends = successful_sends + 1 WHERE id = 1")
        elif stat_type == 'fail':
            cur.execute("UPDATE bot_stats SET failed_runs = failed_runs + 1 WHERE id = 1")
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error actualizando métricas: {e}")

def get_dashboard_data():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM bot_stats WHERE id = 1")
    stats = cur.fetchone() or {'total_runs': 0, 'successful_sends': 0, 'failed_runs': 0, 'last_run': None}
    
    cur.execute("SELECT * FROM logs ORDER BY timestamp DESC LIMIT 50")
    logs = cur.fetchall()
    
    cur.close()
    conn.close()
    return stats, logs