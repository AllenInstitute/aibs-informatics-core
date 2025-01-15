FROM public.ecr.aws/lts/ubuntu:22.04_stable

ARG PYTHON_VERSION=3.11
ARG UV_VERSION=0.5.18

# Update and install deps
# uv installer requires curl (and certificates) to download the release archive
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    python${PYTHON_VERSION} \
    python3-pip

# Download the latest installer
# ENV UV_INSTALL_DIR="/opt/.uv" 
# ENV UV_UNMANAGED_INSTALL="/opt/.uv"
RUN if [ -n "$UV_VERSION" ]; then \
    curl -sSL "https://astral.sh/uv/${UV_VERSION}/install.sh" -o /uv-installer.sh; \
else \
    curl -sSL "https://astral.sh/uv/install.sh" -o /uv-installer.sh; \
fi

# Run the installer then remove it
RUN env UV_INSTALL_DIR='/opt/.uv' UV_UNMANAGED_INSTALL="/opt/.uv" sh /uv-installer.sh \
    && rm /uv-installer.sh

COPY . /opt/python/aibs-informatics-core/

WORKDIR /opt/python/aibs-informatics-core
RUN /opt/.uv/uv pip install --system .
WORKDIR /

RUN rm -rf /opt/.uv

CMD ["python3"]
