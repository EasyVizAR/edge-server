from .main import app

if __name__ == "__main__":
    app.run(host=app.config['VIZAR_HOST'], port=app.config['VIZAR_PORT'])
