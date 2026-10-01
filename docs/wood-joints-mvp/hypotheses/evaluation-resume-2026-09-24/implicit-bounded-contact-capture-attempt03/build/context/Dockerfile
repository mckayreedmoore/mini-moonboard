ARG BASE_IMAGE=mini-moonboard-fea:ccx-upstream-2.23-v1
FROM ${BASE_IMAGE}
ARG BASE_IMAGE
WORKDIR /opt/ccx-bounded-contact-capture
COPY source.tar.bz2 capture.patch patch-preparation.json base-build-manifest.json ./
COPY Makefile.upstream record_capture_build.py Dockerfile ./
RUN CCX_BASE_IMAGE_ID="sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38" python3 record_capture_build.py
WORKDIR /work
