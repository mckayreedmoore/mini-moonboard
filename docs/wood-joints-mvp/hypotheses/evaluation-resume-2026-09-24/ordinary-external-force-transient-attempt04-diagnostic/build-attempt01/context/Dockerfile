ARG BASE_IMAGE=sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38
FROM ${BASE_IMAGE}
ARG BASE_IMAGE
WORKDIR /opt/ccx-attempt04
COPY source.tar.bz2 diagnostic.patch diagnostic-lock.json base-build-manifest.json .
COPY Makefile.upstream record_build.py Dockerfile ./
RUN CCX_BASE_IMAGE="${BASE_IMAGE}" python3 record_build.py
WORKDIR /work
