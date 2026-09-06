ARG BASE_IMAGE
FROM ${BASE_IMAGE}
WORKDIR /opt/ccx-kinematic-observer-2.21
COPY patch.py kinematic_patch.py record_build.py Dockerfile ./
RUN python3 kinematic_patch.py /opt/ccx-upstream-2.21/CalculiX/ccx_2.21/src patched \
    && cp patched/stressmortar.c patched/nonlingeo.c /opt/ccx-upstream-2.21/CalculiX/ccx_2.21/src/ \
    && make -C /opt/ccx-upstream-2.21/CalculiX/ccx_2.21/src -f /opt/ccx-upstream-2.21/Makefile.upstream -j2 \
    && install -m755 /opt/ccx-upstream-2.21/CalculiX/ccx_2.21/src/ccx_2.21 /usr/local/bin/ccx-kinematic-observer-2.21 \
    && python3 record_build.py
WORKDIR /work
