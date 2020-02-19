verb 3
client
nobind
remote-cert-tls server

<ca>
$ca
</ca>
<cert>
$cert
</cert>
<key>
$key
</key>
<tls-auth>
$ta_key
</tls-auth>
key-direction 1

remote $server 1194 tcp
http-proxy $proxy 80
dev-type tap
dev tap
