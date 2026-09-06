ARG BASE_IMAGE=mini-moonboard-fea:box-v1
FROM ${BASE_IMAGE}
# build.py refuses a base image other than the recorded immutable image ID.
RUN sha256sum /usr/bin/ccx > /tmp/packaged-ccx.before.sha256
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc gfortran make libspooles-dev libarpack2-dev liblapack-dev curl bzip2 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/ccx-upstream-2.21
RUN curl --fail --location --retry 2 --max-time 120 \
    https://www.dhondt.de/ccx_2.21.src.tar.bz2 -o source.tar.bz2 \
    && echo '52a20ef7216c6e2de75eae460539915640e3140ec4a2f631a9301e01eda605ad  source.tar.bz2' | sha256sum -c - \
    && tar -xjf source.tar.bz2
COPY Makefile.upstream record_build.py Dockerfile /opt/ccx-upstream-2.21/
RUN make -C CalculiX/ccx_2.21/src -f /opt/ccx-upstream-2.21/Makefile.upstream -j2 \
    && install -m755 CalculiX/ccx_2.21/src/ccx_2.21 /usr/local/bin/ccx-upstream-2.21 \
    && sha256sum -c /tmp/packaged-ccx.before.sha256 \
    && python3 record_build.py
WORKDIR /work
