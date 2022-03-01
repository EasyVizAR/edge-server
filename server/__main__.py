import sys

from .main import app


def main():
    return app.run(host=app.config['VIZAR_HOST'], port=app.config['VIZAR_PORT'])


if __name__ == "__main__":
    sys.exit(main())
