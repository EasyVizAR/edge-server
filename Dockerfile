#
# Build the frontend using npm
#
FROM node:16.13.0 AS build

WORKDIR /usr/src/frontend

COPY server/frontend/package*.json /usr/src/frontend/
RUN npm install

COPY server/frontend /usr/src/frontend
RUN npm run build

#
# Prepare the application server using Python
#
FROM python:3.8

ENV QUART_APP=server.main:app
ENV QUART_ENV=production
ENV VIZAR_HOST=0.0.0.0
ENV VIZAR_PORT=5000

EXPOSE 5000/tcp

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY server/mapping/requirements.txt ./requirements-mapping.txt
RUN pip install --no-cache-dir -r requirements-mapping.txt

COPY . .
COPY --from=build /usr/src/frontend/build /usr/src/app/server/frontend/build

RUN mkdir -p data/maps data/headsets

CMD [ "python", "-m", "server" ]
