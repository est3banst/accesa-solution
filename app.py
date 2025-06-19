from flask import Flask, request, jsonify
from google.cloud import storage
from google.api_core.exceptions import NotFound
from datetime import timedelta
from flask_cors import CORS
import os
import logging
import traceback
from google.cloud import bigquery
import pandas as pd
import re
import unicodedata
import io


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

CORS(app, 
     origins=["https://accesa-client.vercel.app"],
     methods=["GET", "PUT", "POST", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True
)

BUCKET_NAME = "accesa-data-gather"

@app.route("/generate-signed-url", methods=["POST", "OPTIONS"])
def get_signed_url():
    try:
        if request.method == "OPTIONS":
            response = jsonify({"status": "ok"})
            return response, 200
        
        if not request.is_json:
            logger.error("Request not json")
            return jsonify({"error": "Request must be json"}), 400
        
        data = request.get_json()
        if not data:
            logger.error("No data")
            return jsonify({"error": "No data provided"}), 400
            
        file_name = data.get("file_name")
        content_type = data.get("content_type", "application/octet-stream")

        if not file_name:
            logger.error("file_name not found")
            return jsonify({"error": "file_name is required"}), 400

        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"accesa-data/{file_name}")

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=15),
            method="PUT",
            content_type=content_type,
        )

        logger.info(f"Generated signed url for file: {file_name}")
        return jsonify({"signed_url": url}), 200
        
    except Exception as e:
        logger.error(f"Error get_signed_url: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": "Internal server error"}), 500


@app.route("/pubsub-notify-hook", methods=["POST"])
def pubsub_hook():
    try:
        envelope = request.get_json()
        if not envelope:
            msg = "No message"
            logger.error(msg)
            return msg, 400

        pubsub_message = envelope.get("message")
        if not pubsub_message:
            msg = "Invalid Pub/Sub format"
            logger.error(msg)
            return msg, 400

        import base64
        data = base64.b64decode(pubsub_message["data"]).decode("utf-8")
        logger.info(f"Pub/Sub Message: {data}")


        import json
        event_data = json.loads(data)
        file_name = event_data["name"]
        try:
            logger.info(f"Triggering file process for: {file_name}")
            process_file(file_name)
        except Exception as e:
            logger.error(f"Error processing file {file_name}: {str(e)}")

        return "OK", 200
    except Exception as e:
        logger.error(f"hook failed: {e}")
        logger.error(traceback.format_exc())
        return "Internal Error", 500

def clean_column_name(name):
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8')

    name = name.strip().lower().replace(" ", "_")

    name = re.sub(r"[^\w]", "_", name)

    name = re.sub(r"_+", "_", name)

    if not re.match(r"^[a-zA-Z_]", name):
        name = f"col_{name}"

    return name[:128]

# Función para procesar los archivos y cargarlos a BigQuery, llamada por Pub/Sub
def process_file(file_name):
    try:
        if not file_name:
            raise ValueError("Missing file_name in process_file")

        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(file_name)
        file_ext = file_name.split(".")[-1]

        file_data = blob.download_as_bytes()
        
        if file_ext == "csv":
            df = pd.read_csv(io.BytesIO(file_data))
        elif file_ext in ["xls", "xlsx"]:
            df = pd.read_excel(io.BytesIO(file_data))
        else:
            raise ValueError(f"error, unsupported file format {file_ext}")
        logger.info(f"Dataframe shape: {df.shape}")
        df.columns = [clean_column_name(col) for col in df.columns]
        logger.info(f"columnas procesadas: {df.columns.tolist()}")

        project_id = "accesa-equipo3"
        dataset_id = "accesa_dataset"
        file_name = file_name.lower()
        if "roaming" in file_name:
            table_name = "roaming_data"
        elif "automatismo" in file_name:
            table_name = "automatismo_data"
        elif "congestion" in file_name:
            table_name = "congestion_data"
        elif "habilidad" in file_name:
            table_name = "habilidad_data"
        elif "reclamos" in file_name:
            table_name = "reclamos_data"
        elif "611" in file_name:
            table_name = "611_data"
        else:
            table_name = "sin_categorizar"

        table_id = f"{project_id}.{dataset_id}.{table_name}"

        bq_client = bigquery.Client(project=project_id)

        try:
            bq_client.get_dataset(f"{project_id}.{dataset_id}")
            logger.info(f"Dataset {dataset_id} already exists.")
        except NotFound:
            logger.warning(f"Dataset {dataset_id} not found. Creating it...")
            dataset = bigquery.Dataset(f"{project_id}.{dataset_id}")
            dataset.location = "southamerica-east1" 
            dataset = bq_client.create_dataset(dataset)
            logger.info(f"Created dataset: {dataset.dataset_id}")

        job = bq_client.load_table_from_dataframe(df, table_id)
        job.result()

        logger.info(f"archivo: {file_name} cargado a: {table_name}"), 200

    except Exception as e:
        logger.error(f"Error in process_upload: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting server on port: {port}")
    app.run(host="0.0.0.0", port=port, debug=False)