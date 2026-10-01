ARG BASE_IMAGE=mini-moonboard-fea:ccx-upstream-2.21-v1
FROM ${BASE_IMAGE}
# build.py verifies the local base image; historical executables stay intact.
WORKDIR /opt/ccx-upstream-2.23
RUN curl --fail --location --retry 2 --max-time 120 \
    https://www.dhondt.de/ccx_2.23.src.tar.bz2 -o source.tar.bz2 \
    && echo '9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7  source.tar.bz2' | sha256sum -c - \
    && tar -xjf source.tar.bz2
COPY Makefile.upstream record_build.py Dockerfile ./
RUN make -C CalculiX/ccx_2.23/src -f /opt/ccx-upstream-2.23/Makefile.upstream -j2 \
    && install -m755 CalculiX/ccx_2.23/src/ccx_2.23 /usr/local/bin/ccx-upstream-2.23 \
    && python3 record_build.py
WORKDIR /work
