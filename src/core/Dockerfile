ARG DOCKER_IMAGE_BASE=siesa-report
ARG DEV=false

FROM ${DOCKER_IMAGE_BASE}-core-base:latest

COPY ./scripts /scripts
COPY ./app /app
COPY ./requirements.txt /tmp/requirements.txt

# set work directory
WORKDIR /app

RUN pip install -r /tmp/requirements.txt && \
    chmod -R +x /scripts && \
    rm -rf /tmp/*

USER app-user

ENV PATH="/scripts:/py/bin:$PATH"
CMD ["run.sh"]