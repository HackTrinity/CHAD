FROM python:3.8-alpine

COPY requirements.txt /opt/
RUN apk --no-cache add tini redis docker-cli easy-rsa openvpn musl-dev gcc && \
    ln -s /usr/share/easy-rsa/easyrsa /usr/bin/easyrsa && \
    pip install -r /opt/requirements.txt && \
    apk --no-cache del musl-dev gcc

COPY entrypoint.sh /
WORKDIR /opt
COPY CHAD/ /opt/CHAD
VOLUME /etc/chad_pki

ENV WORKERS=1
ENTRYPOINT ["tini", "--", "/entrypoint.sh"]
EXPOSE 80/tcp
