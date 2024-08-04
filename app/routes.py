from flask import Flask, request, jsonify, render_template, redirect
import hashlib
import base64
import redis
from werkzeug.routing import BaseConverter
from app import app

# Connect to Redis server
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super().__init__(url_map)
        self.regex = items[0]

# Register the custom converter
app.url_map.converters['regex'] = RegexConverter

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/shorten_url', methods=['POST'])
def shorten_url():
    data = request.json
    long_url = data.get('long_url')
    
    if not long_url:
        return jsonify({"error": "Missing long_url parameter"}), 400

    # Generate a short key for the long URL
    short_key = generate_short_key(long_url)

    # Store the long URL and short key in Redis
    redis_client.set(short_key, long_url)

    response = {
        "key": short_key,
        "long_url": long_url,
        "short_url": f"http://localhost/{short_key}"
    }

    return jsonify(response), 200

@app.route('/<regex("[a-zA-Z0-9]{5}"):short_key>', methods=['GET'])
def handle_short_key(short_key):
    # Retrieve the long URL from Redis
    long_url = redis_client.get(short_key)

    if long_url:
        # Redirect to the long URL
        return redirect(long_url)
    else:
        return jsonify({"error": "Invalid URL"}), 400

def generate_short_key(long_url):
    # Hash the long URL using SHA-256
    hash_object = hashlib.sha256(long_url.encode())
    # Encode the hash to base64 to make it URL safe and take the first 5 bytes
    short_url = base64.urlsafe_b64encode(hash_object.digest()[:5]).decode('utf-8')[:5]
    return short_url

