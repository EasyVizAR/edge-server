from quart import Quart, request

app = Quart(__name__)


@app.route('/headset/register', methods=['POST'])
async def register():
    body = await request.get_json()

    if 'password' not in body or 'username' not in body:
        return {"isSuccessful": False}

    # TODO: Finalize authentication method
    username = body['username']
    password = body['password']

    return {"isSuccessful": True}


@app.route('/headset/authenticate', methods=['POST'])
async def authenticate():
    body = await request.get_json()

    if 'password' not in body or 'username' not in body:
        return {"isSuccessful": False}

    username = body['username']
    password = body['password']

    # TODO: Generate token or session
    token = username + password

    return {"token": token}


@app.route('/headset/update_position', methods=['POST'])
async def update_position():
    body = await request.get_json()

    if 'x' not in body or 'y' not in body:
        return {"isSuccessful": False}

    x = body['x']
    y = body['y']

    # TODO: Position update logic

    return {"isSuccessful": True}
