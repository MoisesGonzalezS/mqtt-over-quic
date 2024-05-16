FROM python:3.10-slim-bookworm AS base

RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
        apt update && apt install -y \
        pkg-config build-essential cmake git libmbedtls-dev

FROM base AS source
WORKDIR /app
RUN git clone --depth 1 https://github.com/MoisesGonzalezS/pynng-mqtt.git /app/pynng
RUN git -C /app/pynng submodule update --init --recursive --depth 1

FROM base AS msquic
#COPY --from=source /usr/local/prefix /usr/local
COPY --from=source /app/pynng/nng/extern/msquic /app/msquic
WORKDIR /app/msquic/build
RUN cmake -DCMAKE_INSTALL_PREFIX=/usr/local/prefix .. && make -j8 && make install

FROM base AS pynng
COPY --from=msquic /usr/local/prefix/ /usr/local/
COPY --from=source /app/pynng /app/pynng
WORKDIR /app/pynng

RUN pip install -e .
ENV LD_LIBRARY_PATH=/usr/local/
RUN python setup.py bdist_wheel

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install /app/pynng/dist/pynng-0.7.1-cp310-cp310-linux_x86_64.whl
RUN pip install locust

FROM python:3.10-slim-bookworm AS final

COPY --from=msquic /usr/local/prefix/ /usr/local
COPY --from=pynng /opt/venv /opt/venv
ENV LD_LIBRARY_PATH=/usr/local/lib
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app
