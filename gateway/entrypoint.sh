#!/bin/sh
set -ex

BLUE='\033[0;34m'
NC='\033[0m'

info() {
    echo -e ":: ${BLUE}${@}${NC}"
}

mkdir -p /dev/net
if [ ! -c /dev/net/tun ]; then
    mknod /dev/net/tun c 10 200
fi

info "Creating network interfaces..."

ip link add name gw-bridge type bridge
ip link set dev gw-bridge up

openvpn --mktun --dev-type tap --dev gw
ip link set dev gw up
ip link set dev gw master gw-bridge

ip link add challenge type vxlan id 1337 group 239.137.137.137 dev ethwe0 dstport 4789
ip link set dev challenge up
ip link set dev challenge master gw-bridge

exec openvpn "$OVPN_CONFIG"
