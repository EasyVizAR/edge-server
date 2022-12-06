import json
import os
import secrets

from quart import g, request


class Authenticator:
    def __init__(self):
        self.tokens = []
        self.headsets = dict()
        self.path = "auth.json"

    def authenticate_request(self):
        auth = request.headers.get("Authorization", "")
        parts = auth.split()
        if len(parts) >= 2 and parts[0] == "Bearer":
            entry = self.headsets.get(parts[1])
            if entry is not None:
                g.headset_id = entry['id']

    def create_headset_token(self, headset_id):
        token = secrets.token_urlsafe(16)
        self.headsets[token] = {
            "type": "headset",
            "id": headset_id,
            "token": token
        }
        self.tokens.append(self.headsets[token])
        return token

    def save(self):
        with open(self.path, "w") as output:
            output.write(json.dumps(self.tokens, indent=2))

    @classmethod
    def build_authenticator(_class, data_dir):
        auth = _class()
        auth.path = os.path.join(data_dir, "auth.json")

        try:
            with open(auth.path, "r") as source:
                data = json.load(source)
                for item in data:
                    auth.tokens.append(item)
                    if item['type'] == 'headset':
                        auth.headsets[item['token']] = item
        except Exception as error:
            print("Warning: failed to load {} ({})".format(auth.path, error))

        return auth
