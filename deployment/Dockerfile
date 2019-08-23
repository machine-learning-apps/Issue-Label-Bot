FROM python:3.6-slim-stretch

RUN apt-get update 
RUN apt-get upgrade -y
RUN apt-get install --reinstall build-essential -y
RUN apt install -y gcc g++

# hardcode some install so rebuilds are faster, because cannot cache requirements.txt
RUN pip install \
    asn1crypto==0.24.0 \
    astor==0.7.1 \
    backcall==0.1.0 \
    backports.weakref==1.0.post1 \
    bleach==3.1.0 \
    blis==0.2.4 \
    cachetools==3.1.0 \
    certifi==2019.3.9 \
    cffi==1.12.2 \
    chardet==3.0.4 \
    click==7.0 \
    cryptography==2.6.1 \
    cycler==0.10.0 \
    cymem==2.0.2 \
    cytoolz==0.9.0.1 \
    dask==1.1.5 \
    decorator==4.4.0 \
    defusedxml==0.5.0 \
    dill==0.2.9 \
    entrypoints==0.3 \
    enum34==1.1.6 \
    flask-session==0.3.1 \
    flask-sqlalchemy==2.3.2 \
    flask==1.0.2 \
    ftfy==4.4.3 \
    gast==0.2.2 \
    github3.py==1.3.0 \
    grpcio==1.19.0 \
    h5py==2.9.0 \
    html5lib==1.0.1 \
    idna==2.8 \
    ijson==2.3 \
    ipdb==0.12 \
    ipykernel==5.1.0 \
    ipython-genutils==0.2.0 \
    ipython==7.4.0 \
    ipywidgets==7.4.2 \
    itsdangerous==1.1.0 \
    jedi==0.13.3 \
    jinja2==2.10 \
    jsonify==0.5 \
    jsonschema==2.6.0 \
    jupyter-client==5.2.4 \
    jupyter-console==6.0.0 \
    jupyter-core==4.4.0 \
    jupyter==1.0.0 \
    jwcrypto==0.6.0 \
    jwt==0.6.1 \
    keras-applications==1.0.7 \
    keras-preprocessing==1.0.9 \
    keras==2.2.4 \
    kiwisolver==1.0.1 \
    ktext==0.34 \
    numpy==1.16.2 \
    pandas==0.24.2 \
    pyarrow==0.12.1 \
    scikit-learn==0.20.3 \
    seldon-core==0.2.6 \
    tensorflow==1.12.0 \
    seldon-core==0.2.6

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY flask_app flask_app/

EXPOSE 3000 80 443
WORKDIR flask_app/

CMD python app.py