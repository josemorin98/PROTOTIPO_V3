#!/bin/sh
docker-compose down
cd ORCHESTRATOR
docker build -t jmorin98/orchestrator:latest .
docker push jmorin98/orchestrator:latest
cd ..
cd FUSION
docker build -t jmorin98/fusion:latest .
docker push jmorin98/fusion:latest
cd ..
docker-compose up --build
