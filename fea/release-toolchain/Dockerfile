FROM mini-moonboard-fea:box-v1
# The release audit reuses the existing NumPy compliance check.
RUN apt-get update && apt-get install -y --no-install-recommends python3-numpy \
    && rm -rf /var/lib/apt/lists/*
