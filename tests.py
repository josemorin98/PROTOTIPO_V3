import json
import requests
import time
import socket

headers = {'PRIVATE-TOKEN': '<your_access_token>', 'Content-Type':'application/json'}


jsonSend = {
    "paramsOrchestrator":{"balanceType":["TEMPORAL", "ESPATIAL"],
                          "paramsBalancer":
                              [{
                              "startTime":"2001-01-01 00:00:00",
                               "endTime":"2001-12-31 00:00:00",
                               "nRange":1,
                               "typeDate":"Y"},
                               {"typeEspatial": "STATE"}]
                          },
    "cubes":{
        "df0_100000k":{"nameFile":"df0_100000k.csv",
                   "Espatial":"state",
                   "Temporal":["fecha","%Y-%m-%d %H:%M:%S"],
                   "Tranformation":{
                              "Fusion":{"columnFusion":["fecha","state"]}
                                    }
                   },
             
        "df1_1000000k":{"nameFile":"df1_100000k.csv",
                   "Espatial":"state",
                   "Temporal":["fecha","%Y-%m-%d %H:%M:%S"],
                   "Tranformation":{
                              "Fusion":{"columnFusion":["fecha","state"]}
                                    }
                   },
        "df2_1000000k":{"nameFile":"df2_100000k.csv",
                   "Espatial":"state",
                   "Temporal":["fecha","%Y-%m-%d %H:%M:%S"],
                   "Tranformation":{
                              "Fusion":{"columnFusion":["fecha","state"]}
                                    }
                   }
    },
    "PIPELINE":["balance/espatial","analytics/fusion"],
    "startRequestTime":time.time()
}

print('sending')

ip_cinves = "148.247.204.165"
ip_neg = "192.168.1.77"
ip_home = "192.168.0.16"
ip_gama = "148.247.202.73"
ip_inp = "10.249.26.15"
ip = socket.gethostbyname(socket.gethostname())
url = "http://{}:5001/balance/temporal".format(ip) # Negocio

print(url)

for x in range(1):
    req = requests.post(url,data=json.dumps(jsonSend), headers=headers)