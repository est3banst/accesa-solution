FROM --platform=linux/amd64 python:3.13-slim


WORKDIR /app

RUN pip install Flask google-cloud-storage flask-cors gunicorn pyarrow
RUN pip install google-cloud-aiplatform pandas pandas-gbq openpyxl xlrd google-cloud-bigquery python-docx

COPY . .

EXPOSE 8080

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app