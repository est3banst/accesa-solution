FROM --platform=linux/amd64 python:3.12-alpine

WORKDIR /app

RUN pip install Flask google-cloud-storage flask-cors gunicorn

COPY . .

EXPOSE 8080 

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app