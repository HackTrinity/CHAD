FROM alpine:3.11

RUN apk --no-cache add su-exec iproute2 iptables

ENV __CAP_ADD=NET_ADMIN
COPY entrypoint.sh /
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/sh"]
