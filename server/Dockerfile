FROM python:3.8-alpine

COPY requirements.txt /opt/
RUN apk --no-cache add musl-dev gcc && \
    pip install -r /opt/requirements.txt && \
    apk --no-cache del musl-dev gcc

WORKDIR /opt
COPY CHAD/ .

COPY entrypoint.sh /
ENV WORKERS=1
ENTRYPOINT ["/entrypoint.sh"]
EXPOSE 80/tcp
