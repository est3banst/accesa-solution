from flask import Flask, request, jsonify
from google.cloud import storage
from google.api_core.exceptions import NotFound
from datetime import timedelta, datetime
from vertexai.preview.language_models import TextGenerationModel
import vertexai
from docx import Document
from flask_cors import CORS
import os
import logging
import traceback
import math
from google.cloud import bigquery
import pandas as pd
import re
import unicodedata
import calendar
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

vertexai.init(project="accesa-equipo3", location="southamerica-east1")



def convert_month_to_abbr(month_str):
    """Convert '2025-04' to 'Abr-25'"""
    year, month = map(int, month_str.split('-'))
    month_names = {
        1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
    }
    return f"{month_names.get(month, '---')}-{str(year)[2:]}"

def fetch_monthly_automatismo(table_name):
    bq = bigquery.Client()
    query = f"""
        SELECT 
        * FROM `accesa-equipo3.accesa_dataset.{table_name}`
        ;
    """
    return bq.query(query).to_dataframe()

def fetch_monthly_congestion(table_name):
    bq = bigquery.Client()
    query = f"""
        SELECT 
        * FROM `accesa-equipo3.accesa_dataset.{table_name}` 
        ;
    """
    return bq.query(query).to_dataframe()

def fetch_monthly_reclamos(table_name):
    bq = bigquery.Client()
    query = f"""
        SELECT 
        * FROM `accesa-equipo3.accesa_dataset.{table_name}`
        ;
    """
    return bq.query(query).to_dataframe()

def fetch_monthly_incidencias(table_name):
    bq = bigquery.Client()
    query = f"""
        SELECT 
        * FROM `accesa-equipo3.accesa_dataset.{table_name}`
        ;
    """
    return bq.query(query).to_dataframe()

def fetch_monthly_habilidad(table_name):
    bq = bigquery.Client()
    query = f"""
        SELECT 
        * FROM `accesa-equipo3.accesa_dataset.{table_name}`
        ;
    """
    return bq.query(query).to_dataframe()

def fetch_monthly_skill(table_name):
    bq = bigquery.Client()
    query = f"""
        SELECT 
        * FROM `accesa-equipo3.accesa_dataset.{table_name}`
        ;
    """
    return bq.query(query).to_dataframe()

def fetch_monthly_roaming(table_name):
    bq = bigquery.Client()
    query = f"""
        SELECT 
        * FROM `accesa-equipo3.accesa_dataset.{table_name}`
        ;
    """
    return bq.query(query).to_dataframe()

def summarize_dataframe(df, context=""):
    model = TextGenerationModel.from_pretrained("text-bison@001")
    prompt = f"""
Actúa como un analista de datos senior. Resume los siguientes datos ({context}) en español con una narrativa profesional, señalando tendencias, anomalías o valores atípicos.
 {df.describe(include='all').to_string()}
"""
    return model.predict(prompt=prompt, temperature=0.7, max_output_tokens=1024).text

def add_report_header(doc, month):
    doc.add_heading("Informe Mensual de Gestión", 0)
    doc.add_paragraph(f"Móvil – {month}", style="Subtitle")
    doc.add_paragraph(f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d')}")
    doc.add_paragraph("")

def add_general_summary(doc):
    doc.add_heading("Resumen General", level=1)
    doc.add_paragraph(
        "Informe mensual de gestión de servicios de Accesa Contact Center para los servicios 0800 6611 y *611 de atención de clientes de Móvil Antel y 0800 2466, atención a Agentes de Venta y Clientes Internos. El servicio se atiende todos los días del año de 0 a 24 horas."
    )
    
    
def add_summary_table_movil_611(doc, month_str, metrics):
    """
    Adds the custom summary table for Antel - Móvil 611 section with specific fields and structure.
    """
    table = doc.add_table(rows=1, cols=2)
    table.style = 'Table Grid'

    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "ANTEL - MÓVIL 611"
    hdr_cells[1].text = month_str

    rows = [
        ("Llamadas al servicio", "llamadas_al_servicio", "int"),
        ("Llamadas atendidas totales", "llamadas_atendidas_totales", "int"),
        ("Llamadas abandonadas", "llamadas_abandonadas", "int"),
        ("% Llamadas no atendidas", "porcentaje_no_atendidas", "percent"),
        ("Cumplimiento Nivel de Servicio 80/20", "nivel_de_servicio_80_20", "percent"),
        ("Índice de respuesta", "indice_respuesta", "percent"),
        ("TRSAC", "trsac", "float"),
        ("Promedio operación (segundos)", "promedio_tiempo_operacion_segundos", "float"),
        ("Tiempo total atención (horas)", "tiempo_total_atencion_horas", "float"),
        ("Congestión", "congestion_6611", "percent")
    ]

    for label, key, dtype in rows:
        row = table.add_row().cells
        value = metrics.get(key)
        if value is None:
            display_value = "N/A"
        else:
            try:
                if dtype == "percent":
                    display_value = f"{float(value):.2f}%"
                elif dtype == "float":
                    display_value = f"{float(value):.2f}"
                else:
                    display_value = str(int(value))
            except (ValueError, TypeError):
                display_value = "N/A"

        row[0].text = label
        row[1].text = display_value

    promedio = metrics.get("promedio_llamadas_por_dia")
    if promedio is not None:
        try:
            promedio_val = int(promedio)
            doc.add_paragraph(
                f"El promedio de llamadas diarias ingresado al servicio en el mes fue de {promedio_val:,}"
            )
        except (ValueError, TypeError):
            pass
     

def add_incidencias_bullet_section(doc, metrics):
    """
    Adds a heading and a bulleted list of incidencias, with their dates and descriptions.
    """
    fechas = metrics.get("fecha_incidente", [])
    descripciones = metrics.get("descripcion_incidente", [])

    if fechas is None or descripciones is None or len(fechas) == 0:
        doc.add_paragraph("No se registraron incidencias que afectaran el servicio móvil este mes.")
        return

    doc.add_paragraph("Incidencias que afectaron el servicio móvil en el mes:", style="List Bullet")

    for fecha, descripcion in zip(fechas, descripciones):
        item = f"{fecha}: {descripcion}"
        doc.add_paragraph(item, style="List Bullet")


def add_metrics_section(doc, section_title, metrics_dict, summary_text=None):
    """
    Adds a custom table per section using human-readable labels for each metric.
    """
    doc.add_heading(section_title.replace("_", " ").title(), level=1)

    if summary_text:
        doc.add_paragraph(summary_text)

    custom_labels = {
        "roaming_data": {
            "mensajes_entrantes": "Mensajes entrantes",
            "mensajes_salientes": "Mensajes salientes",
            "total_mensajes": "Total de mensajes",
            "promedio_mensajes_por_interaccion": "Prom. mensajes por interacción"
        },
        "automatismo_data": {
            "total_correcto": "Total correcto",
            "total_error": "Total error",
            "total_automatismos": "Total automatismos",
            "porcentaje_correcto": "% Correcto",
            "porcentaje_error": "% Error"
        },
        "reclamos_data": {
            "total_tiempo_llamadas": "Tiempo total de llamadas",
            "total_llamadas": "Total llamadas",
            "nombre_de_cola": "Colas involucradas",
            "nombre_de_codigo_de_conclusion": "Códigos de conclusión"
        },
        "incidencias_data": None 
    }

    label_map = custom_labels.get(section_title, {})

    if not label_map:
    
        logger.warning(f"No custom label mapping found for section: {section_title}")
        return

    table = doc.add_table(rows=1, cols=2)
    table.style = 'Table Grid'

    for key, value in metrics_dict.items():
        if key not in label_map:
            continue  

        label = label_map[key]
        row_cells = table.add_row().cells
        row_cells[0].text = label
        row_cells[1].text = (
            ", ".join(value) if isinstance(value, list) else str(value)
        )


def add_dataframe_table(doc, section_title, df, summary_text=None):
    """
    Crea el encabezado, resumen, y la tabla de un dataframe para el actual docx Documento.
    """
    doc.add_heading(section_title.replace("_", " ").title(), level=1)

    if summary_text:
        doc.add_paragraph(summary_text)

    table = doc.add_table(rows=1, cols=len(df.columns))
    table.style = 'Table Grid'

    for i, col in enumerate(df.columns):
        table.rows[0].cells[i].text = str(col)

    for row in df.itertuples(index=False):
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = str(val)
            
            
def build_report(month, metrics_by_section, summaries_by_section):
    doc = Document()
    add_report_header(doc, month)
    add_general_summary(doc)

    doc.add_heading("Indicadores de Gestión de las Llamadas", level=1)

    combined_611_metrics = {}
    combined_611_metrics.update(metrics_by_section.get("habilidad_data", {}))
    combined_611_metrics.update(metrics_by_section.get("skill_data", {}))
    combined_611_metrics.update(metrics_by_section.get("reclamos_data", {}))
    combined_611_metrics.update(metrics_by_section.get("congestion_data", {}))

    if "total_tiempo_llamadas" in combined_611_metrics:
        ms = combined_611_metrics["total_tiempo_llamadas"]
        combined_611_metrics["tiempo_total_atencion_horas"] = round(ms / (1000 * 60 * 60), 2)

    add_summary_table_movil_611(doc, convert_month_to_abbr(month), combined_611_metrics)

    if "incidencias_data" in metrics_by_section:
        incidencias_metrics = metrics_by_section["incidencias_data"]
        add_incidencias_bullet_section(doc, incidencias_metrics)

    for section, metrics in metrics_by_section.items():
        if section in {"habilidad_data", "skill_data", "reclamos_data", "congestion_data", "incidencias_data"}:
            continue  
        summary = summaries_by_section.get(section, "")
        add_metrics_section(doc, section, metrics, summary)

    filename = f"reporte_{month}.docx"
    doc.save(filename)
    return filename



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
        if file_name.startswith("reports/") or file_name.endswith(".docx"):
            logger.info(f"Archivo de reporte : {file_name}")
            return "Archivo de reporte omitido", 200
        
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

@app.route("/generate-report", methods=["POST"])
def generate_report():
    handler_map = {
    "roaming_data" : (fetch_monthly_roaming, calc_roaming),
    "habilidad_data": (fetch_monthly_habilidad, calc_habilidad),
    "skill_data": (fetch_monthly_skill, calc_skill),
    "reclamos_data":(fetch_monthly_reclamos, calc_reclamos),
    "congestion_data": (fetch_monthly_congestion, calc_congestion),
    "automatismo_data": (fetch_monthly_automatismo, calc_automatismo),
    "incidencias_data" : (fetch_monthly_incidencias, calc_incidencias)
    }
    try:
        data = request.get_json()
        month = data.get("month")

        metrics_by_section = {}
        summaries_by_section = {}

        for table, (fetch_fn, calc_fn) in handler_map.items():
            try:
                df = fetch_fn(table)
                if not df.empty:
                    metrics = calc_fn(df)
                    metrics_by_section[table] = metrics
                    summaries_by_section[table] = summarize_dataframe(df, context=metrics)
            except Exception as e:
                logger.warning(f"Failed to fetch data for {table}: {e}")

        if not metrics_by_section:
            return jsonify({"error": f"No data for period {month}"}), 404

        report_filename = build_report(month, metrics_by_section, summaries_by_section)

        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"reports/report_{month}.docx")
        blob.upload_from_filename(report_filename)

        # Download URL
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=15),
            method="GET"
        )
        return jsonify({"download_url": url}), 200

    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": "Internal server error"}), 500


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
            df = pd.read_excel(io.BytesIO(file_data), header=None)
            logger.info(f"Dataframe actual: {df.shape}")
            if df.shape[1] == 1 and isinstance(df.iloc[0, 0], str) and df.iloc[0, 0].count(',') > 1:
                
                logger.warning("Improperly formatted Excel file with comma-delimited content.")

                split_df = df.iloc[:, 0].str.split(',', expand=True)

                split_df.columns = split_df.iloc[0].fillna("col_unnamed")
                df = split_df.iloc[1:].reset_index(drop=True)
            else:
                if "roaming" in file_name.lower():
                    df = pd.read_excel(io.BytesIO(file_data), skiprows=6)
                elif "skill" in file_name.lower():
                    df = pd.read_excel(io.BytesIO(file_data), skiprows=3)
                elif "automatismo" in file_name.lower():
                    df = pd.read_excel(io.BytesIO(file_data), skiprows=4)
                elif "habilidad" in file_name.lower():
                    df = pd.read_excel(io.BytesIO(file_data), skiprows=1)
                elif "congestion" in file_name.lower():
                    df = pd.read_excel(io.BytesIO(file_data), skiprows=4)
                else:
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
        elif "incidencias" in file_name:
            table_name = "incidencias_data"
        elif "congestion" in file_name:
            table_name = "congestion_data"
        elif "habilidad" in file_name:
            table_name = "habilidad_data"
        elif "skill" in file_name:
            table_name = "skill_data"
        elif "reclamos" in file_name:
            table_name = "reclamos_data"
        elif "611" in file_name:
            table_name = "611_data"
        else:
            table_name = "sin_categorizar"

        table_id = f"{project_id}.{dataset_id}.{table_name}"

        bq_client = bigquery.Client(project=project_id)

        dataset_ref = bq_client.dataset(dataset_id)

        try:
            bq_client.get_dataset(dataset_ref)
            logger.info(f"Dataset {dataset_id} already exists.")
        except NotFound:
            logger.warning(f"Dataset {dataset_id} not found. Creating it...")
            dataset = bigquery.Dataset(dataset_ref)
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

def calc_habilidad(df):
    total_llamadas = df["ofrecidas"].sum()
    atendidas = df["atendidas"].sum()
    abandonadas = df["abandonadas"].sum()
    dias_mes = df["fecha"].nunique()

    porcentaje_no_atendidas = (abandonadas / total_llamadas) * 100 if total_llamadas else 0
    indice_respuesta = 100 - porcentaje_no_atendidas
    promedio_llamadas = total_llamadas / dias_mes if dias_mes else 0

    return {
        "llamadas_servicio": total_llamadas,
        "llamadas_atendidas": atendidas,
        "llamadas_abandonadas": abandonadas,
        "porcentaje_no_atendidas": round(porcentaje_no_atendidas, 2),
        "indice_respuesta": round(indice_respuesta, 2),
        "promedio_llamadas_por_dia": math.trunc(promedio_llamadas),
    }

def calc_skill(df):
    trsac_antel_movil = df["demora_en_atender"][1] if len(df["demora_en_atender"]) > 1 else 0
    antel_movil_ofrecidas = df["ofrecidas"][1] if len(df["ofrecidas"]) > 1 else 0
    antel_movil_contestadas = df["contestadas"][1] if len(df["contestadas"]) > 1 else 0
    antel_movil_abandonadas = df["abandonadas"][1] if len(df["abandonadas"]) > 1 else 0
    referentes_movil_ofrecidas = df["ofrecidas"][0] if len(df["ofrecidas"]) > 0 else 0
    horas_operacion = df["horas_operacion"][1] if len(df["horas_operacion"]) > 1 else 0
    promedio_tiempo_operacion_segundos = df["tiempo_operacion"][1] if len(df["tiempo_operacion"]) > 1 else 0
    calidad = df["calidad_"][1] if len(df["calidad_"]) > 1 else 0
    nivel_de_servicio = round((calidad * 100) / 80, 2)

    return {
        "trsac": trsac_antel_movil,
        "llamadas_al_servicio": antel_movil_ofrecidas,
        "llamadas_atendidas_totales": antel_movil_contestadas,
        "llamadas_abandonadas" : antel_movil_abandonadas,
        "referentes_movil_ofrecidas": referentes_movil_ofrecidas,
        "tiempo_total_atencion_horas": horas_operacion,
        "nivel_de_servicio_80_20": nivel_de_servicio,
        "promedio_tiempo_operacion_segundos": promedio_tiempo_operacion_segundos,}

def calc_congestion(df):
    df_seis_uno = df["col_6611_"].sum()
    df_uno_dos_uno = df["col_121_"].sum()
    
    return {
        "congestion_6611": int(df_seis_uno)
    }


def calc_roaming(df):
    mensajes_entrantes = df["cantidad_de_mensajes_entrantes"]
    mensajes_salientes = df["cantidad_de_mensajes_salientes"]
    total_mensajes = mensajes_entrantes + mensajes_salientes
    promedio_mensajes_por_interaccion = df["promedio_de_mensajes_por_interaccion"]

    return {
        "mensajes_entrantes": mensajes_entrantes,
        "mensajes_salientes": mensajes_salientes,
        "total_mensajes": total_mensajes,
        "promedio_mensajes_por_interaccion": promedio_mensajes_por_interaccion,
    }
    

def calc_automatismo(df):
    total_correcto = df["total_correcto"].sum()
    total_error = df["total_error"].sum()

    porcentaje_correcto = ((total_correcto * 100 )/ (total_correcto + total_error)) if (total_correcto + total_error) > 0 else 0
    porcentaje_error = ((total_error * 100) / (total_correcto + total_error)) if (total_correcto + total_error) > 0 else 0
    total_automatismos = total_correcto + total_error

    return {
        "total_correcto": total_correcto,
        "total_error": total_error,
        "total_automatismos": total_automatismos,
        "porcentaje_correcto": round(porcentaje_correcto, 2),
        "porcentaje_error": round(porcentaje_error, 2),
    }

def ms_to_hms(ms):
    seconds = int(ms / 1000)
    return str(timedelta(seconds=seconds))

def calc_incidencias(df):
    df["responsabilidad"] = df["responsabilidad"].str.lower()
    df = df[df["responsabilidad"] == "cliente"]
    
    fecha_incidente = df["fecha"]
    descripcion_incidente = df["descripcion"]
    
    return {
        "fecha_incidente" : fecha_incidente,
        "descripcion_incidente" : descripcion_incidente
    }

def calc_reclamos(df):
    df["_acumulado_o_detallado_"] = df["_acumulado_o_detallado_"].str.lower()
    df = df[df["_acumulado_o_detallado_"] == "detallado"]

    total_tiempo_llamadas = df["_manejo_total_"].sum()
    total_llamadas = df["_manejo_"].sum()
    nombre_de_cola = df["_nombre_de_cola_"].to_list()
    nombre_de_codigo_de_conclusion = df["_nombre_de_codigo_de_conclusion_"].to_list()

    return {
        "total_tiempo_llamadas": ms_to_hms(total_tiempo_llamadas),
        "total_llamadas": total_llamadas,
        "nombre_de_cola": nombre_de_cola,
        "nombre_de_codigo_de_conclusion": nombre_de_codigo_de_conclusion,
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting server on port: {port}")
    app.run(host="0.0.0.0", port=port, debug=False)