FROM alpine:3.11 AS builder
WORKDIR /root
COPY build_nginx_connect.sh .
RUN ./build_nginx_connect.sh


FROM alpine:3.11
RUN apk --no-cache add pcre easy-rsa openvpn && \
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

RUN easyrsa init-pki
COPY dh.pem $EASYRSA_PKI/dh.pem
COPY entrypoint.sh /

EXPOSE 80/tcp
