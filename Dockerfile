FROM python:3.12-slim

WORKDIR /app

# COPY requirements.txt requirements.txt
# RUN pip install -r requirements.txt

RUN pip install Flask
RUN pip install google-cloud-storage
RUN pip install flask-cors

COPY . .

EXPOSE 8081

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=8081
ENV GOOGLE_APPLICATION_CREDENTIALS=accesa-equipo3-6f10afb05ee2.json

CMD ["flask", "run"]
