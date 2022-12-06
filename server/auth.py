import json
import os
import secrets

from quart import g, request


class Authenticator:
    def __init__(self):
        self.tokens = []
        self.headset_tokens = dict()
        self.path = "auth.json"

    def authenticate_request(self):
        auth = request.headers.get("Authorization", "")
        parts = auth.split()
        if len(parts) >= 2 and parts[0] == "Bearer":
            g.headset_id = self.lookup(parts[1])
            print("Request has headset_id: {}".format(g.headset_id))

    def create_headset_token(self, headset_id):
        token = secrets.token_urlsafe(16)
        self.headset_tokens[headset_id] = token
        self.tokens.append({
            "type": "headset",
            "id": headset_id,
            "token": token
        })
        return token

    def lookup(self, token):
        return self.headset_tokens.get(token)

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
                        auth.headset_tokens[item['id']] = item['token']
        except Exception as error:
            print("Warning: failed to load {} ({})".format(auth.path, error))

        return auth
