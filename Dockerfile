FROM python:3.6-slim-stretch

RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update
RUN apt install -y python3-dev gcc

COPY . /
RUN pip install -r requirements.txt

EXPOSE 5000 3000
WORKDIR flask_app/

CMD python app.py