# build this container: docker build -t hamelsmu/ml-gpu-issue-lang-model -f gpu.Dockerfile .
# run this container: docker run --runtime=nvidia -it --net=host --ipc=host -v <host_dir>:/ds hamelsmu/ml-gpu-issue-lang-model bash

FROM hamelsmu/ml-gpu-lite

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY notebooks notebooks/

EXPOSE 7654
CMD ["sh", "-c", "jupyter notebook --no-browser --allow-root --port=7654 --NotebookApp.token='$pass'"]