import json
import requests
import time
import socket

headers = {'PRIVATE-TOKEN': '<your_access_token>', 'Content-Type':'application/json'}


jsonSend = {
    "paramsOrchestrator":{"balanceType":["ESPATIAL", "TEMPORAL"],
                          "paramsBalancer":
                              [{"typeEspatial": "STATE"},
                               {
                              "startTime":"2001-01-01 00:00:00",
                               "endTime":"2001-12-31 00:00:00",
                               "nRange":1,
                               "typeDate":"Y"}
                               ]
                          },
    "cubes":{
        "df0_100000k":{"nameFile":"df0_100000k.csv",
                   "Espatial":"state",
                   "Temporal":["fecha","%Y-%m-%d %H:%M:%S"],
                   "Tranformation":{
                            "fusion":{"columns":["fecha","state"],
                                        "typeFusion": "rows"},
                            "mediaClass":{"columns":["A","B","C","D","E","F","G","H","I"],
                                          "numImportant":3},
                            "correlation":{"columns":["A","B","C","D","E","F","G","H","I"],
                                           "normalize":1,
                                           "algorithm":["pearson", "spearman"],# pearson’, ‘kendall’, ‘spearman
                                           "addColumnIn":"regression",
                                           "numSendPair":2},
                            "regression":{"algorithm":["lineal"],
                                          "columns":[]}
                            },
                   },
             
        "df1_1000000k":{"nameFile":"df1_100000k.csv",
                   "Espatial":"state",
                   "Temporal":["fecha","%Y-%m-%d %H:%M:%S"],
                   "Tranformation":{
                            "fusion":{"columns":["fecha","state"],
                                        "typeFusion": "rows"},
                            "mediaClass":{"columns":["A","B","C","D","E","F","G","H","I"],
                                          "numImportant":3,
                                          "addColumnIn":"correlation"},
                            "correlation":{"columns":["A","B","C","D","E"],
                                           "normalize":1,
                                           "algorithm":["pearson", "spearman"],
                                           "addColumnIn":"regression",
                                           "numSendPair":2}
                                    }
                   },
        "df2_1000000k":{"nameFile":"df2_100000k.csv",
                   "Espatial":"state",
                   "Temporal":["fecha","%Y-%m-%d %H:%M:%S"],
                   "Tranformation":{
                              "fusion":{"columns":["fecha","state"],
                                        "typeFusion": "rows"
                                        
                                        },
                            "mediaClass":{"columns":["A","B","C","D","E","F","G","H","I"],
                                          "numImportant":3,
                                          "addColumnIn":"correlation"},
                            "correlation":{"columns":["A","B","C","D","E"],
                                           "normalize":1,
                                           "algorithm":["pearson", "spearman"],
                                           "addColumnIn":"regression",
                                           "numSendPair":2}
                                    }
                   }
    },
    "PIPELINE":["balance/temporal","analytics/fusion","analytics/mediaClass","/analytics/correlation","/analytics/regression"],
    "startRequestTime":time.time()
}

print('sending')

ip_cinves = "148.247.204.165"
ip_neg = "192.168.1.77"
ip_home = "192.168.0.16"
ip_inp = "10.249.26.15"
ip = socket.gethostbyname(socket.gethostname())

ip = "localhost"
url = "http://{}:5001/balance/espatial".format(ip) # Negocio

print(url)

for x in range(1):
    req = requests.post(url,data=json.dumps(jsonSend), headers=headers)
    print(req.status_code)