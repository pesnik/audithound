
import os
import pickle
import sqlite3
from flask import Flask, request

app = Flask(__name__)

# Hardcoded credentials (bandit will catch this)
API_KEY = "sk-1234567890abcdef"
DATABASE_PASSWORD = "admin123"

# SQL Injection vulnerability
def get_user(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # Vulnerable to SQL injection
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    return cursor.fetchone()

# Command injection vulnerability
@app.route('/ping')
def ping():
    host = request.args.get('host', 'localhost')
    # Vulnerable to command injection
    result = os.system(f'ping -c 1 {host}')
    return f"Ping result: {result}"

# Pickle deserialization vulnerability
def load_config(config_data):
    # Dangerous use of pickle
    return pickle.loads(config_data)

# Weak random generation
def generate_token():
    import random
    return random.randint(1000, 9999)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')  # Debug mode in production
