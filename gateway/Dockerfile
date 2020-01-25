FROM alpine:3.11
RUN apk --no-cache add easy-rsa openvpn nginx tini && \
    ln -s /usr/share/easy-rsa/easyrsa /usr/bin/easyrsa

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
    rm /var/lib/nginx/html/index.html && \
    ln -s "$OPENVPN/client.conf" /var/lib/nginx/html/client.conf
COPY dh.pem $EASYRSA_PKI/dh.pem
COPY entrypoint.sh /

ENTRYPOINT ["tini", "--", "/entrypoint.sh"]
EXPOSE 1194/tcp
EXPOSE 80/tcp
