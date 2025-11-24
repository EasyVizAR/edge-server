#
# Generate protobuf code
#
FROM rvolosatovs/protoc AS protoc

WORKDIR /usr/src/protobuf

COPY messages.proto /usr/src/protobuf/
RUN protoc --python_out=. messages.proto

#
# Build the frontend using npm
#
FROM node:16.13.0 AS build

WORKDIR /usr/src/frontend

COPY server/frontend/package*.json /usr/src/frontend/
RUN npm install

COPY server/frontend /usr/src/frontend
COPY messages.proto /usr/src/frontend/public/
RUN npm run build

#
# Prepare the application server using Python
#
FROM python:3.12

ENV QUART_APP=server.main:app
ENV QUART_ENV=production
ENV VIZAR_HOST=0.0.0.0
ENV VIZAR_PORT=5000

EXPOSE 5000/tcp

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=protoc /usr/src/protobuf/messages_pb2.py /usr/src/app/server/
COPY --from=build /usr/src/frontend/build /usr/src/app/server/frontend/build

RUN mkdir -p data/maps data/headsets

CMD [ "python", "-m", "server" ]
