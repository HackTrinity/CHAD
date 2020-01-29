import requests

class CHADClient:
    def __init__(self, endpoint):
        self.endpoint = endpoint

    def get_ovpn(self, user_id):
        res = requests.get(f'{self.endpoint}/gateways/{user_id}/ovpn/client')
        res.raise_for_status()

        return res.text
