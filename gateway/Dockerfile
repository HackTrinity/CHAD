FROM alpine:3.11
RUN apk --no-cache add iproute2 openvpn

ENV OVPN_CONFIG=/run/secrets/server.conf
COPY entrypoint.sh /

ENTRYPOINT ["/entrypoint.sh"]
EXPOSE 1194/tcp
