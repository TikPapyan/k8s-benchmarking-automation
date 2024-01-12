FROM python:3.9

RUN apt-get update && \
    apt-get install -y openssh-client sshpass && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install kubernetes

WORKDIR /usr/src/app

COPY bench.py .
COPY logg.py .
COPY calculations.py .
COPY cleanup.py .
COPY k8s.py .
COPY hw.py .
COPY hw.sh .
COPY deployment_processing.py .

RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && chmod +x ./kubectl \
    && mv ./kubectl /usr/local/bin/kubectl

CMD ["python3", "./bench.py"]
