FROM python:3.6-slim-stretch

RUN apt-get update && apt-get upgrade -y
RUN apt-get install --reinstall build-essential
RUN apt install -y gcc g++

COPY . /
RUN pip install -r requirements.txt

EXPOSE 5000 3000
WORKDIR flask_app/

CMD python app.py