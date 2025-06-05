from flask import Flask, request, jsonify
from google.cloud import storage
from datetime import timedelta
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)   

BUCKET_NAME = "accesa-data-gather"

@app.route("/generate-signed-url", methods=["POST"])
def get_signed_url():
    data = request.get_json()
    file_name = data.get("file_name")
    content_type = data.get("content_type", "application/octet-stream")

    if not file_name:
        return jsonify({"error": "file_name is required"}), 400

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"accesa-data/{file_name}")

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=15),
            method="PUT",
            content_type=content_type
        )

        return jsonify({"signed_url": url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Optional: Set GOOGLE_APPLICATION_CREDENTIALS
    port = os.environ.get("PORT", 8080)
    app.run(host="0.0.0.0", port=port)
