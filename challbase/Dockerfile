FROM alpine:3.11 AS builder
RUN apk --no-cache add gcc musl-dev libcap-dev

WORKDIR /usr/local/src
COPY drop_net_admin.c .
RUN gcc -o /usr/local/bin/drop_net_admin drop_net_admin.c -lcap


FROM alpine:3.11

RUN apk --no-cache add libcap su-exec iproute2 iptables
COPY --from=builder /usr/local/bin/drop_net_admin /usr/local/bin/drop_net_admin

ENV __CAP_ADD=NET_ADMIN
RUN mkdir /etc/challbase
COPY entrypoint.sh /
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/sh"]
