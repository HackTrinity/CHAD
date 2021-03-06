#!/bin/sh
set -e

BLUE='\033[0;34m'
NC='\033[0m'

info() {
    echo -e ":: ${BLUE}${@}${NC}"
}

HOOK_DIR="/etc/challbase"

VXLAN_OUT="ethwe0"
VXLAN_IFACE="challenge"
VXLAN_ID=1337
VXLAN_MCAST="239.137.137.137"

setup_vxlan() {
    info "Connecting VXLAN interface $VXLAN_IFACE to challenge networking as $1"
    ip link add "$VXLAN_IFACE" type vxlan id "$VXLAN_ID" group "$VXLAN_MCAST" dev "$VXLAN_OUT" dstport 4789
    ip addr add "$1" dev "$VXLAN_IFACE"
    ip link set "$VXLAN_IFACE" up

    info "Configuring iptables to isolate challenge network"
    net="$(ip route | grep "${VXLAN_IFACE}.*scope link" | awk '{ print $1 }')"
    iptables -A FORWARD -i "$VXLAN_IFACE" -j DROP
    iptables -A OUTPUT -o lo -j ACCEPT
    iptables -A OUTPUT -d "$net" -j ACCEPT
    iptables -A OUTPUT -o "$VXLAN_OUT" -p udp --dport 4789 -j ACCEPT
    iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED -j ACCEPT
    iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
    iptables -A OUTPUT -d 10.0.0.0/8,172.16.0.0/12,192.168.0.0/16 -j DROP

    if [ -z "$KEEP_INTERNET" ]; then
        info "Disabling internet access"
        iptables -P OUTPUT DROP
    fi
}

[ -f "$HOOK_DIR/pre-net.sh" ] && "$HOOK_DIR/pre-net.sh"
[ ! -z "$CHALLENGE_IP" ] && setup_vxlan "$CHALLENGE_IP"

[ -f "$HOOK_DIR/pre-drop.sh" ] && "$HOOK_DIR/pre-drop.sh"

rm -r "$HOOK_DIR/"
rm -- "$0"

if [ ! -z "$KEEP_NET_ADMIN" ]; then
    info "Staying as root and keeping CAP_NET_ADMIN while executing '$@'"
    exec "$@"
elif [ ! -z "$KEEP_ROOT" ]; then
    info "Staying as root while executing '$@'"
    exec drop_net_admin "$@"
else
    info "Dropping to nobody:nogroup to execute '$@'"
    exec su-exec nobody:nogroup "$@"
fi
