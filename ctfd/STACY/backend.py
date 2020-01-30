import requests

class CHADError(Exception):
    pass
class InstanceExistsError(CHADError):
    pass
class InstanceNotFoundError(CHADError):
    pass

class CHADClient:
    def __init__(self, endpoint):
        self.endpoint = endpoint

    def __raise_status(self, res):
        if res.status_code < 400 or res.status_code >= 500:
            return

        message = res.json().get('message', 'unknown error')
        if res.status_code == 404:
            raise InstanceNotFoundError(message)
        elif res.status_code == 409:
            raise InstanceExistsError(message)

    def get_ovpn(self, user_id):
        res = requests.get(f'{self.endpoint}/gateways/{user_id}/ovpn/client')
        res.raise_for_status()

        return res.text

    def create_instance(self, user_id, chall_id, stack, service, flag):
        res = requests.post(f'{self.endpoint}/instances/{user_id}/{chall_id}', json={
            'stack': stack,
            'service': service,
            'flag': flag
        })
        self.__raise_status(res)
        res.raise_for_status()

        return res.json()

    def delete_instance(self, user_id, chall_id):
        res = requests.delete(f'{self.endpoint}/instances/{user_id}/{chall_id}')
        self.__raise_status(res)
        res.raise_for_status()
