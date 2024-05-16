# MQTT over Quic

This repository contains tests and comparisons between MQTT running over the QUIC protocol in contrast to
TCP. The client library used is the python bindings in https://github.com/wanghaEMQ/pynng-mqtt.

# Setup


We build pynng-mqtt inside a docker container to make it easier to manage dependencies. You must first build
the docker image by running:

```bash
docker build . -t  pynng:latest
```

You have to manually create a docker network named `mqtt`:

```bash
docker network create mqtt

```

Then you can spinup an environment by running docker-compose as follows:

```bash
export COMPOSE_FILE=docker-compose-broker.yaml
docker compose up -d
```

The `docker-compose.broker.yaml` file contains the service definition for
the EMQX broker and the prometheus and grafana services that we use to collect
and visualize the performance metrics.

You can run the load tests by using the following docker command:

```
docker run --name=pynng --network=mqtt \
    -v "$PWD/locust-tests:/app/examples" --rm -it 
    -e MQTT_BROKER_QUIC_HOST=j
    pynng:latest \
    locust --headless -u <number of clients> -r <user increment ratio> -t <duration in seconds> -f examples/locustfile_tcp.py
```

The locust command accepts several flags, the most relevant are:

1. `--headless`: to stop locust from starting a webserver for its web interface.
2. `-u`: The number of concurrent users or clients that is going to be used across the test.
3. `-t`: the duration of the test in seconds.
4. `-f`: The locust file with the test specification. At the moment there are 2 tests: `locustfile_tcp.py` and `locustfile_quic.py`


You can start your docker container with the `-e` flags to set environment variables,
the tests can use the `MQTT_BROKER_QUIC_HOST` and `MQTT_BROKER_QUIC_PORT` variables to
configure the address used to connect to the broker. By default the use the docker compose
name for the broker `emqx`.
