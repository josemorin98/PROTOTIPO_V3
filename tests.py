import json
import requests
import time
import socket

headers = {'PRIVATE-TOKEN': '<your_access_token>', 'Content-Type':'application/json'}

# jsonSend = {
#     "paramsOrchestrator":{"balanceType":["TEMPORAL"],
#                           "paramsBalancer":[
#                               {"typeTemporal":""}
#                                             ]
#                           },
#     "cubes":{
#         "TasaD_preV3":{"nameFile":"TasaD_preV3.csv",
#                    "Espatial":"nombre entidad",
#                    "Temporal":"anio_ocur",
#                    "Tranformation":{"PROCES_A":{"A":1,"B":2},
#                                     "PROCES_B":{"A":3,"B":4}}
#                    }
#     },
#     "PIPELINE":["/response"],
#     "startRequestTime":time.time()
# }

jsonSend = {
    "paramsOrchestrator":{"balanceType":["TEMPORAL"],
                          "paramsBalancer":
                              [{
                              "startTime":"2000-01-01 00:00:00",
                               "endTime":"2005-12-31 00:00:00",
                               "nRange":1,
                               "typeDate":"Y"}]
                          },
    "cubes":{
        "Suic_Medio_Derhab_tasasporsexo":{"nameFile":"Suic_Medio_Derhab_tasasporsexo.csv",
                   "Espatial":"nombre entidad",
                   "Temporal":["anio","%Y"],
                   "Tranformation":{
                              "Fusion":{"columnFusion":"cve_ent_mun_x"}
                                    }
                   },
             
        "Variables_Macroeconomicas":{"nameFile":"Variables Macroeconomicas.csv",
                   "Espatial":"nombre entidad",
                   "Temporal":"NO_TEMPORAL",
                   "Tranformation":{
                              "Fusion":{"columnFusion":"cve_ent_mun"}
                                    }
                   }
    },
    "PIPELINE":["response"],
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