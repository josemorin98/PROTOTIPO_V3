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
cd MEDIA_CLASS
docker build -t jmorin98/media:latest .
docker push jmorin98/media:latest
cd ..
cd CORRELATION
docker build -t jmorin98/correlation:latest .
docker push jmorin98/correlation:latest
cd ..
cd REGRESSION
docker build -t jmorin98/regression:latest .
docker push jmorin98/regression:latest
cd ..
docker-compose up --build
