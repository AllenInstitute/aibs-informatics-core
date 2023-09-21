FROM public.ecr.aws/lts/ubuntu:22.04_stable

# Update and install deps
RUN apt-get update -y && apt-get install -y \
    python3.9 \
    python3-pip

COPY . /opt/python/aibs-informatics-core/

WORKDIR /opt/python/aibs-informatics-core
RUN pip3 install --no-cache-dir -r requirements-docker.txt
WORKDIR /

CMD ["python3"]
