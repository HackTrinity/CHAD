FROM python:3.8-alpine

COPY requirements.txt /opt/
RUN apk --no-cache add tini redis docker-cli musl-dev gcc && \
    pip install -r /opt/requirements.txt && \
    apk --no-cache del musl-dev gcc

COPY entrypoint.sh /
WORKDIR /opt
COPY CHAD/ /opt/CHAD

ENV WORKERS=1
ENTRYPOINT ["tini", "--", "/entrypoint.sh"]
EXPOSE 80/tcp
