#!/bin/sh
set -ex

BLUE='\033[0;34m'
NC='\033[0m'

info() {
    echo -e ":: ${BLUE}${@}${NC}"
}

generate_configs() {
    SERVER_CN="${INSTANCE_ID}.${DOMAIN}"

    info "Generating CA..."
    EASYRSA_BATCH="yes" EASYRSA_DN=org EASYRSA_REQ_CN="HackTrinity Challenge $INSTANCE_ID CA" easyrsa build-ca nopass

    info "Generating OpenVPN static key..."
    openvpn --genkey --secret "$EASYRSA_PKI/ta.key"

    info "Generating server key, certificate and configuration..."
    EASYRSA_DN=org easyrsa build-server-full "$SERVER_CN" nopass

    # TODO: Should probably not assume /24
    ADDR_START="$(ifconfig gw-bridge | grep 'inet addr' | sed -n 's/\s*inet addr:\(\d*\.\d*\.\d*\).*/\1/p')"
    cat > "$OPENVPN/server.conf" <<EOF
verb 3
mode server
tls-server
ifconfig-pool ${ADDR_START}.50 ${ADDR_START}.254 255.255.255.0

ca $EASYRSA_PKI/ca.crt
cert $EASYRSA_PKI/issued/$SERVER_CN.crt
key $EASYRSA_PKI/private/$SERVER_CN.key
dh $EASYRSA_PKI/dh.pem
tls-auth $EASYRSA_PKI/ta.key 0

keepalive 10 60
persist-key
persist-tun
#local 127.0.0.1
port 1194
proto tcp-server
dev-type tap
dev gw

status /tmp/openvpn-status.log
user nobody
group nogroup
EOF

    info "Generating client key and certificate..."
    easyrsa build-client-full "user" nopass
    cat > "$OPENVPN/client.conf" <<EOF
verb 3
client
nobind
remote-cert-tls server

<ca>
$(cat $EASYRSA_PKI/ca.crt)
</ca>
<cert>
$(cat $EASYRSA_PKI/issued/user.crt)
</cert>
<key>
$(cat $EASYRSA_PKI/private/user.key)
</key>
<tls-auth>
$(cat $EASYRSA_PKI/ta.key) 0
</tls-auth>
key-direction 1

remote $SERVER_CN 1194 tcp
#http-proxy $PROXY 80
dev-type tap
dev ht-${INSTANCE_ID}
EOF
    chmod 600 "$OPENVPN/client.conf"
}

mkdir -p /dev/net
if [ ! -c /dev/net/tun ]; then
    mknod /dev/net/tun c 10 200
fi

LAN_IP="$(ip addr show dev $LAN_IFACE | grep inet | awk '{ print $2 }')"
GATEWAY="$(ip route show | grep default | awk '{ print $3 }')"
ip addr del "$LAN_IP" dev "$LAN_IFACE"

openvpn --mktun --dev-type tap --dev gw
ip link set dev gw up

ip link add name gw-bridge type bridge
ip link set dev gw-bridge up

ip link set dev eth0 master gw-bridge
ip link set dev gw master gw-bridge
ip addr add dev gw-bridge "$LAN_IP"
ip route add default via "$GATEWAY"

[ ! -f "$OPENVPN/server.conf" ] && generate_configs
