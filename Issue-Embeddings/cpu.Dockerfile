# the gpu image: docker run --runtime=nvidia -it --net=host --ipc=host -p 3006:3006 -v <host_dir>:/ds hamelsmu/ml-gpu-lite
# this image (cpu): https://cloud.docker.com/u/github/repository/docker/github/mdtok
FROM python:3.7-slim-stretch

RUN apt-get update 
RUN apt-get upgrade -y
RUN apt-get install --reinstall build-essential -y
RUN apt install -y gcc g++

ENV CXXFLAGS="-std=c++11"
ENV CFLAGS="-std=c99"

RUN pip3 install https://download.pytorch.org/whl/cpu/torch-1.1.0-cp37-cp37m-linux_x86_64.whl
RUN pip3 install torchvision

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY notebooks notebooks/

EXPOSE 7654

CMD ["sh", "-c", "jupyter notebook --no-browser --allow-root --port=7654 --NotebookApp.token='$pass'"]