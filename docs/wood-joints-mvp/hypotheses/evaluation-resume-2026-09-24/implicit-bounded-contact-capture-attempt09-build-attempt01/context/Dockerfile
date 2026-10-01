ARG BASE_IMAGE=mini-moonboard-fea:ccx-upstream-2.23-v1-pinned-31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38
FROM ${BASE_IMAGE}
ARG BASE_IMAGE
ARG BASE_IMAGE_ID
WORKDIR /opt/ccx-bounded-contact-capture-attempt09-build01
COPY source.tar.bz2 capture.patch patch-preparation.json base-build-manifest.json base-image-pin.json attempt09-base-image-pin.json ./
COPY Makefile.upstream record_capture_build.py Dockerfile ./
RUN CCX_BASE_IMAGE_ID="${BASE_IMAGE_ID}" CCX_BASE_IMAGE_REFERENCE="${BASE_IMAGE}" python3 record_capture_build.py
WORKDIR /work
