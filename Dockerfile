FROM python:3.6

RUN pip install numpy ktext pandas scikit-learn dill tensorflow
RUN mkdir /data
RUN mkdir /output
COPY src /src
