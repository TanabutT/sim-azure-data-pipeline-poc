FROM jupyter/pyspark-notebook:latest

USER root

RUN apt-get update && apt-get install -y \
    curl \
    vim \
    git \
    && rm -rf /var/lib/apt/lists/*

USER jovyan

COPY requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir -r /tmp/requirements.txt

RUN mkdir -p /home/jovyan/work /home/jovyan/spark_warehouse

WORKDIR /home/jovyan

EXPOSE 8888 4040

CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", "--NotebookApp.token=''", "--NotebookApp.password=''"]
