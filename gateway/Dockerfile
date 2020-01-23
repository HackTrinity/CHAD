FROM alpine:3.11 AS builder
WORKDIR /root
COPY build_nginx_connect.sh .
RUN ./build_nginx_connect.sh


FROM alpine:3.11
RUN apk --no-cache add pcre easy-rsa openvpn tini && \
    ln -s /usr/share/easy-rsa/easyrsa /usr/bin/easyrsa
COPY --from=builder /usr/local/nginx /usr/local/nginx

ENV OPENVPN=/etc/openvpn
ENV EASYRSA=/usr/share/easy-rsa
ENV EASYRSA_PKI=$OPENVPN/pki

ENV EASYRSA_REQ_COUNTRY=IE
ENV EASYRSA_REQ_PROVINCE=Dublin
ENV EASYRSA_REQ_CITY=Dublin
ENV EASYRSA_REQ_ORG=Netsoc
ENV EASYRSA_REQ_EMAIL=admin@hacktrinity.org
ENV EASYRSA_REQ_OU=HackTrinity
ENV EASYRSA_CA_EXPIRE=30
ENV EASYRSA_CERT_EXPIRE=30

ENV LAN_IFACE=eth0
ENV PROXY=chad-gw.sys.hacktrinity.org
ENV DOMAIN=challs.hacktrinity.org
ENV INSTANCE_ID=abcdEFGH
ENV CONFIG_PASSWORD_FILE=/run/secrets/config_password

RUN easyrsa init-pki && \
    rm /usr/local/nginx/html/index.html && \
    ln -s "$OPENVPN/client.conf" /usr/local/nginx/html/client.conf
COPY dh.pem $EASYRSA_PKI/dh.pem
COPY entrypoint.sh /

ENTRYPOINT ["tini", "--", "/entrypoint.sh"]
EXPOSE 80/tcp
