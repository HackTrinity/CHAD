FROM alpine:3.11 AS builder
WORKDIR /root
COPY build_nginx_connect.sh .
RUN ./build_nginx_connect.sh


FROM alpine:3.11
RUN apk --no-cache add pcre

COPY --from=builder /usr/local/nginx /usr/local/nginx
ENTRYPOINT ["/usr/local/nginx/sbin/nginx", "-g", "daemon off;"]
EXPOSE 80/tcp
