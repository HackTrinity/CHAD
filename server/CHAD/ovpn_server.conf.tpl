verb 3
mode server
tls-server
ifconfig-pool $pool

<ca>
$ca
</ca>
<cert>
$cert
</cert>
<key>
$key
</key>
<dh>
$dh
</dh>
<tls-auth>
$ta_key
</tls-auth>
key-direction 0
duplicate-cn
client-to-client

keepalive 10 60
persist-key
persist-tun
port 1194
proto tcp-server
dev-type tap
dev gw
tun-mtu 1300

status /tmp/openvpn-status.log
user nobody
group nogroup
