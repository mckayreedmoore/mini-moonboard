ARG BASE_IMAGE=mini-moonboard-fea:ccx-upstream-2.23-v1
FROM ${BASE_IMAGE}
ARG CCX_BASE_IMAGE_ID
WORKDIR /opt/ccx-bounded-contact-capture
COPY source.tar.bz2 capture.patch patch-preparation.json base-build-manifest.json base-image-pin.json ./
COPY Makefile.upstream record_capture_build.py Dockerfile ./
RUN CCX_BASE_IMAGE_ID="${CCX_BASE_IMAGE_ID}" python3 record_capture_build.py
WORKDIR /work
