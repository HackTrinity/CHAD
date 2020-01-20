#!/bin/sh
set -e

apk update

apk add git
git clone https://github.com/chobits/ngx_http_proxy_connect_module

apk add musl-dev pcre-dev zlib-dev gcc make
NGINX_VERSION=1.16.1
wget "http://nginx.org/download/nginx-$NGINX_VERSION.tar.gz"
tar zxf "nginx-$NGINX_VERSION.tar.gz"
cd "nginx-$NGINX_VERSION/"

patch -p1 < ../ngx_http_proxy_connect_module/patch/proxy_connect_rewrite_101504.patch
./configure --add-module=../ngx_http_proxy_connect_module
make -j$(nproc)
make install
