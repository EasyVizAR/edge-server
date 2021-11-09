import os

# Host and port the server will listen on:
VIZAR_HOST = os.environ.get('VIZAR_HOST', '127.0.0.1')
VIZAR_PORT = os.environ.get('VIZAR_PORT', 5000)

# Host (and port) that should appear in URLs:
VIZAR_EDGE_HOST = os.environ.get('VIZAR_EDGE_HOST', '127.0.0.1:5000')

VIZAR_DATA_DIR='data'
VIZAR_HEADSET_DIR='headsets'
IMAGE_UPLOADS='/images/uploads/'
