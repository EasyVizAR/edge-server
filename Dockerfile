FROM python:3.8

ENV QUART_APP=server.main:app
ENV QUART_ENV=production
ENV VIZAR_HOST=0.0.0.0
ENV VIZAR_PORT=5000

EXPOSE 5000/tcp

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data/maps data/headsets

CMD [ "python", "-m", "server" ]
