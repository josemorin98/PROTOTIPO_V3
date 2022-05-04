#!/bin/sh
docker-compose down
cd NODE_GENERIC
docker build -t jmorin98/node_v3:latest .
docker push jmorin98/node_v3:latest
cd ..
cd ORCHESTRATOR
docker build -t jmorin98/orchestrator:latest .
docker push jmorin98/orchestrator:latest
cd ..
docker-compose up --build
