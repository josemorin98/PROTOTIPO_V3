import logging
import time
from flask import Flask
from flask import jsonify
import json
import requests
import os
from flask import Flask, request

app = Flask(__name__)
app.debug = True
app.config['PROPAGATE_EXCEPTIONS'] = False

nodeId = "test"
logPath = os.environ.get("LOGS_PATH",'/logs')
# Format to logs
FORMAT = '%(created).0f %(levelname)s %(message)s'
# object formatter
formatter = logging.Formatter(FORMAT)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# config format
console.setFormatter(fmt=formatter)
# config del logging
logs_info_file = './data{}/info'.format(logPath)       # ESTABLECER RUTA DE LOGS INFO
if (not os.path.exists(logs_info_file)):
    os.mkdir(logs_info_file)
logs_info_file = './data{}/info/{}_info.log'.format(logPath,nodeId)       # ESTABLECER RUTA DE LOGS INFO

logs_error_file = './data{}/error'.format(logPath)     # ESTABLECER RUTA DE LOGS ERROR# -------- LOGGER INFO
if (not os.path.exists(logs_error_file)):
    os.mkdir(logs_error_file)
logs_error_file = './data{}/error/{}_error.log'.format(logPath,nodeId)     # ESTABLECER RUTA DE LOGS ERROR# -------- LOGGER INFO
loggerInfo = logging.getLogger('LOGS_INFO')
hdlr_1 = logging.FileHandler(logs_info_file)
hdlr_1.setFormatter(formatter)
loggerInfo.setLevel(logging.INFO)
loggerInfo.addHandler(hdlr_1)
loggerInfo.addHandler(console)

nodeId = os.environ.get("NODE_ID",'prueba')
portNode = os.environ.get("NODE_PORT",5000)

tableState = {"numEvents":0,
            "nodeID":nodeId,
            "events":[]}

# GET ALL NODES WORKERS
@app.route('/events', methods = ['GET'])
def show_worker():
    global tableState
    return jsonify(tableState)

def updateStateTable(jsonRespone,numberEvent,procesList,nodeId):
    global tableState
    eventName = "event_{}".format(numberEvent)
    loggerInfo.error("----------------------------------- RESPONSE {}".format(eventName))
    # saber si existe el evneto en la tabla de estado
    jsonState = {"NODE_ID":nodeId,
                "DATA_PROCESS": procesList,
                "INFO_RESPONSE":jsonRespone}
    if (eventName in tableState["events"]):
        tableState["events"][eventName] = list()
        tableState["events"][eventName].append(jsonState)
    else:
        tableState["events"][eventName].append(jsonState)
    
    return 



@app.route('/test', methods = ["GET"])
def test():
    global tableState
    
    # RECIBIMOS EL JSON
    data_file = request.get_json()
    
    
    # Cabezeras
    headers = {'PRIVATE-TOKEN': '<your_access_token>', 'Content-Type':'application/json'}
    # IP UTILIZADAS
    ip_cinves = "148.247.204.165"
    ip_neg = "192.168.1.77"
    ip_home = "192.168.0.16"
    ip_gama = "148.247.202.73"
    hostname = "lb_generic_z_0"
    hostname2 = "conteo_0"
    hostnameTest = "espatial_0"
    url = "http://{}:5000/balance/espatial".format(hostnameTest) # Negocio
    # url = "http://{}:5000/analytics/conteo".format(hostname2) # Negocio

    loggerInfo.info(url)

    req = requests.post(url,data=json.dumps(data_file), headers=headers)

    # loggerInfo.info(req.json())

    

    return jsonify({"response":"Termino"})


if __name__ == '__main__':
    app.run(host= '0.0.0.0',port=portNode,debug=True,use_reloader=False)