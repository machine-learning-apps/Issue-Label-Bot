
# for https://cloud.docker.com/u/hamelsmu/repository/docker/hamelsmu/issuefeatures-api-cpu
FROM python:3.6-slim-stretch

RUN apt-get update 
RUN apt-get upgrade -y
RUN apt-get install --reinstall build-essential -y
RUN apt install -y gcc g++
RUN apt-get -y install cmake

# install large files first so that they are cached.
RUN pip install https://download.pytorch.org/whl/cpu/torch-1.1.0-cp36-cp36m-linux_x86_64.whl
RUN pip install https://download.pytorch.org/whl/cpu/torchvision-0.3.0-cp36-cp36m-linux_x86_64.whl
RUN pip install plac==0.9.6 fastai==1.0.53.post3 fastprogress==0.1.21 mdparse==0.13 spacy==2.1.4 numpy==1.16.4 \
    pandas==0.24.2 scikit-learn==0.20.3 scipy==1.2.1 matplotlib==3.0.3 jupyter-core==4.4.0

# hardcode some install so rebuilds are faster, because cannot cache requirements.txt
RUN pip install \
    appnope==0.1.0 \
    beautifulsoup4==4.7.1 \
    bs4==0.0.1 \
    flask==1.0.2 \
    ftfy==4.4.3 \
    gcsfs==0.2.1 \
    google-auth-oauthlib==0.3.0 \
    google-auth==1.6.3 \
    gunicorn==19.9.0 \
    html5lib==1.0.1 \
    idna==2.8 \
    ijson==2.3 \
    ipdb==0.12 \
    ipykernel==5.1.0 \
    ipython-genutils==0.2.0 \
    ipython==7.5.0 \
    mistune==0.8.4 \
    pillow==6.0.0 \
    pycparser==2.19 \
    six==1.12.0 \
    tqdm==4.32.2 \
    widgetsnbextension==3.4.2

COPY requirements.txt .
RUN pip install -r requirements.txt

# copy files for api server
RUN apt install wget
RUN wget https://storage.googleapis.com/issue_label_bot/model/lang_model/models_22zkdqlr/trained_model_22zkdqlr.pkl -O model.pkl

COPY flask_app flask_app/
RUN cp model.pkl flask_app/
WORKDIR flask_app/
RUN mkdir -p model_files

EXPOSE 3000 80 443
CMD python app.py
#CMD gunicorn -w 1 app:app -b 0.0.0.0:$PORT