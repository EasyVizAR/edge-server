from setuptools import setup, find_packages

setup(
    name="easyvizar-edge",
    version="1.1.0",
    description="Central point for coordinating AR headsets",
    url="https://github.com/EasyVizAR/edge-server/",

    project_urls = {
        "Documentation": "https://easyvizar.github.io/edge-server/apispec.html",
        "Homepage": "https://wings.cs.wisc.edu/easyvizar/",
        "Source": "https://github.com/EasyVizAR/edge-server/",
    },

    packages=find_packages(),

    entry_points={
        "console_scripts": [
            "server = server.__main__:main"
        ]
    }
)
