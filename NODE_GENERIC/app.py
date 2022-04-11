# from asyncio.log import logger
from datetime import datetime
import string
import threading
from flask import Flask, request
from flask import jsonify
from node import NodeWorker
import os
import json
import time
import methods as mtd
import node as node
import logging
import requests
import pandas as pd

app = Flask(__name__)
app.debug = True
app.config['PROPAGATE_EXCEPTIONS'] = True

# -------- VARIABLES DE ENTRONO RECIBIDAS 
# //////// AQUI AGRENAR LAS QUE SEAN NECESARIAS ///////
logPath = os.environ.get("LOGS_PATH",'./')                              # RUTA DE LOS LOGS
sourcePath = os.environ.get("SOURCE_PATH","./")                         # RUTA DE ARCHIVOS GENERADOS
nodeId = os.environ.get("NODE_ID",'')                                   # ID DEL NODO
presentationValue = mtd.trueOrFalse(os.environ.get('PRESENTATION',"0")) # PRESENTACION DEL NODO A NODO MANAGER

# -------- EN CASO DE QUE NO EXITA LA RUTA SE CREARA LA CARPETA
if (not os.path.exists(".{}/{}".format(sourcePath,nodeId))):
    os.mkdir(".{}/{}".format(sourcePath,nodeId))


# -----------------------------------------------------------------------------------------------------------------------
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# -----------------------------------------------------------------------------------------------------------------------


# -------- CONFIGURACION DE LOGS ERROR E INFO
FORMAT = '%(created).0f %(levelname)s {} %(message)s'.format(nodeId) # FORMATO A UTILIZAR EN LOS LOGS
formatter = logging.Formatter(FORMAT)                                # GENERAR EL FORMATO PARA CONSOLA Y LOGGERS
console = logging.StreamHandler()                                    # GENERAR EL MANEJADOR CONSOLE
console.setLevel(logging.INFO)                                       # ESTABLECER EL NIVEL DE CONSOLA
console.setFormatter(fmt=formatter)                                  # ESTABLECER EL FORMATO DE CONSOLA
logs_info_file = './data{}/{}_info.log'.format(logPath,nodeId)       # ESTABLECER RUTA DE LOGS INFO
logs_error_file = './data{}/{}_error.log'.format(logPath,nodeId)     # ESTABLECER RUTA DE LOGS ERROR
# -------- LOGGER INFO
loggerInfo = logging.getLogger('LOGS_INFO')                          # CONFIGURACION DEL NOMBRE
hdlr_1 = logging.FileHandler(logs_info_file)                         # COLOCAR RUTA DE LOGS INFO
hdlr_1.setFormatter(formatter)                                       # ESTABLECER FORMATO
loggerInfo.setLevel(logging.INFO)                                    # ESTABLECER NIVE DEL LOGGER INFO
loggerInfo.addHandler(hdlr_1)                                        # AÑADIR MANEJADOR
loggerInfo.addHandler(console)                                       # AÑADIR MANEJADOR A CONSOLA
# -------- LOGGER ERROR
loggerError = logging.getLogger("LOGS_ERROR")                        # CONFIGURACION DEL NOMBRE
hdlr_2 = logging.FileHandler(logs_error_file)                        # COLOCAR RUTA DE LOGS ERROR
hdlr_2.setFormatter(formatter)                                       # ESTABLECER FORMATO
loggerError.setLevel(logging.ERROR)                                  # ESTABLECER NIVE DEL LOGGER ERROR
loggerError.addHandler(hdlr_2)                                       # AÑADIR MANEJADOR
loggerError.addHandler(console)                                      # AÑADIR MANEJADOR A CONSOLA



# -----------------------------------------------------------------------------------------------------------------------
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# -----------------------------------------------------------------------------------------------------------------------

# -------- JSON DE CONFIGURACION TOTAL DEL NODO
""" 
    NOTA:
        AQUI SE AGREGARAN LAS VARIABLES DE ENTRONO DEL NODO, CADA VARIABLE 
        AGREGADA, TENDRA QUE SER AGREGADA DENTRO DEL ARCHIVO "NODE.PY" 
"""
    
state = {"nodes": [],
            "nodeId": nodeId,                                           # ID DEL NODO
            "ip": os.environ.get('IP','127.0.0.1'),                     # IP DEL NODO
            "publicPort": os.environ.get('PUBLIC_PORT',5000),           # PUERTO PUBLICO DEL NODO
            "dockerPort": os.environ.get('DOCKER_PORT',5000),           # PUERTO DEL CONTENEDOR (DOCKER) DEL NODO
            "mode": os.environ.get('MODE','DOCKER'),                    # MODO DE COMUNICACION ENTRE LOS NODOS
            "events":0}                                                 # CANTIDAD DE EVENTOS CALCULADOS

nodeLocal = node.NodeWorker(**state)                                    # GENERAMOS EL OBJETO NODOLOCAL

nodeInfoManager = {"nodeId": os.environ.get('NODE_ID_MANAGER','-'),     # ID DEL NODO MANAGER
            "ip": os.environ.get('IP_MANAGER','127.0.0.1'),             # IP DEL NODO MANAGER
            "publicPort": os.environ.get('PUBLIC_PORT_MANAGER',5000),   # PUERTO PUBLICO DEL NODO MANAGER
            "dockerPort": os.environ.get('DOCKER_PORT_MANAGER',5000)}   # PUERTO DEL CONTENEDOR (DOCKER) DEL NODO MANAGER

nodeManager = node.NodeWorker(**nodeInfoManager)                        # GENERAMOS EL OBJETODE NODO MANAGER

# -----------------------------------------------------------------------------------------------------------------------
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# -----------------------------------------------------------------------------------------------------------------------

# -------- TABLA DE ESTADOS DE EVENTOS DEL NODO
tableState = {
            "totalEvents":0,    # TOTAL DE EVENTOS EJECUTADOS
            "nodeID":nodeId,    # ID DEL NODO LOCAL
            "events":[]}        # LISTA DE INFORMACION DE LOS EVENTOS


# -----------------------------------------------------------------------------------------------------------------------
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# -----------------------------------------------------------------------------------------------------------------------


def loggerInfoSet(message:json):
    global loggerInfo
    # OPERATION READ_TIME PROCESS_TIME ARRIVAL_TIME START_RESQUEST_TIME LATENCE_TIME
    msg = "{} {} {} {} {} {}".format(message["OPERATION"],
                                           message["READ_TIME"],
                                           message["PROCESS_TIME"],
                                           message["ARRIVAL_TIME"],
                                           message["START_RESQUEST_TIME"],
                                           (message["ARRIVAL_TIME"]-message["START_REQUEST_TIME"]))
    loggerInfo.info(msg) 



# -----------------------------------------------------------------------------------------------------------------------
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# -----------------------------------------------------------------------------------------------------------------------


# -------- FUNCION QUE AGREGARA LOS NODOS TRABAJADORES
@app.route('/workers', methods = ['POST'])
def add_worker():
    """ Esta funcion estara dedicada a guardar la informacion de los workers.

        La funcion esta recibiendo un json de con la informacion del nodo worker
        con la siguiente estructura:
        
        infoSend = {
            'nodeId': int,
            'ip': string,    
            'publicPort': int,
            'dockerPort': int
        }
        
        Returns:
            json: informacion del resultado y tiempos obtenidos
            status: codigo del estado del servidor
    """
    global nodeLocal                                            # ESTABLECAMOS LA VARIAVBLE GLOBLA NODE LOCAL
    try:    
        arrivalTime = time.time()                               # TIEMPO DE LLEGADA
        nodeNewInfo = request.get_json()                        # LECTURA DE DATOS
        startRequestTime = nodeNewInfo['startRequestTime']
        endReadTime = time.time()                               # TIEMPO FINAL DE LECTURA
        readTime = endReadTime - arrivalTime                    # TIEMPO DE LECTURA
    except Exception as e:
        message = "ERROR_READING CREATE_NODE {}".format(e)      # MENSAJE DE ERROR
        return  jsonify({"response":message}),501               # RETORNO 501-LECTURA
    
    try:
        startTimeProcess = time.time()                          # TIEMPO INCIAL DEL PROCESO
        nodeNew = NodeWorker(**nodeNewInfo["nodeInfo"])         # PROCESO DE CREAR EL NODO TRABAJADOR
        nodeLocal.addNode(nodeNew)                              # AGREGAMOS EL NODO TRABAJADOR
        endTimeProcess = time.time()                            # TIEMPO FINAL DEL PROCESO
        processTime = endTimeProcess - startTimeProcess         # TIEMPO DE PROCES
        send = True                                         
    except Exception as e:
        message = "ERROR_PROCCESING CREATE_NODE {}".format(e)   # MENSAJE DE ERROR
        return jsonify({"response":message}),502                # RETORNO 502-PROCCESING
    
    """
        MESSAGE = OPERATION READ_TIME PROCESS_TIME ARRIVAL_TIME START_REQUEST_TIME LATENCE_TIME
        
        LATENCE_TIME = ARRIVAL_TIME - START_REQUEST_TIME
    """
    messageInfo = {"OPERATION": "CREATE_NODE",
                   "READ_TIME": readTime,
                   "PROCESS_TIME":processTime,
                   "ARRIVAL_TIME":arrivalTime,
                   "START_REQUEST_TIME":startRequestTime}
    # loggerInfo.info('"CREATED"_NODE {} {}'.format(nodeNew.nodeId,(endTime-startTime)))
    loggerInfoSet(messageInfo)
    return jsonify({'response':"OK"}), 200




# GET ALL NODES WORKERS
@app.route('/workers', methods = ['GET'])
def show_worker():
    global state
    # show all nodes
    nodes = state['nodes']
    nodesReturn = []
    for node in nodes:
        nodesReturn.append(node.toJSON())
    return jsonify(nodesReturn)


@app.route('/status', methods = ['GET'])
def send_balance():
    global tableState
    return jsonify(tableState)

def updateStateTable(jsonRespone,numberEvent,procesList,nodeId):
    global tableState
    eventName = "event_{}".format(numberEvent)
    loggerError.error("----------------------------------- RESPONSE {}".format(eventName))
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

def sendData(url,jsonSend,numberEvent,procesList,nodeId):
    try:
        headers = {'PRIVATE-TOKEN': '<your_access_token>', 'Content-Type':'application/json'}
        requests.post(url, data=json.dumps(jsonSend), headers=headers)
        # jsonResponse = response.json()
        # updateStateTable(jsonRespone=jsonResponse,numberEvent=numberEvent, procesList=procesList, nodeId=nodeId)
        return "OK"
    except:
        loggerError.error('BALANCER_ERROR SEND_INFO {}'.format(nodeId))
        return "ERROR"

@app.route('/prueba', methods = ['GET'])
def pruebaSend():
    return 1
    
    
@app.before_first_request
def presentation():
    """
        Funcion dedicada a realizar la presentation a su nodo manager para que este le mande
        el trabajo a realizar con los parametros debidos.
        
        Esta funcion retorna la informacion del nodo con la siguiente estructura:
        
        infoSend = {
            'nodeId': int,
            'ip': string,    
            'publicPort': int,
            'dockerPort': int
        }
        
        Returns:
            str: estado del envio de la presentation
    """
    global state
    global nodeManager
    global presentationValue
    global nodeLocal
    time.sleep(5)
    try:
        startTimeRead = time.time()                                                                 # TIEMPO DE INCIO DE LETURA
        headers = {'PRIVATE-TOKEN': '<your_access_token>', 'Content-Type':'application/json'}       # CABECERA DE PETICION
        infoSend = {"nodeInfo":nodeLocal.toJSON(),                                                  # INFORMACION DEL NODO LOCAL
                "startRequestTime":0}                                                               # TIEMPO DE INICIO DE PETICION
        endTimeRead = time.time()                                                                   # TIEMPO FINAL DE LECTURA
        readTime = endTimeRead - startTimeRead                                                      # TIEMPO DE LECTURA
    except Exception as e:
        msg = "ERROR PRESENTATION_READ {}".format(e)
        return jsonify({"responde":msg})
    # send info to manager
    
    # Node Manager
    startTimeProcess = time.time()
    contPresentation = 1 
    while True:
        try:
            if (presentationValue == False):                                    # VERIFCA SI LA PRESENTACION ESTA ACTIVA
                break
            url = nodeManager.getURL(mode=nodeLocal.getMode())                  # OBTENEMOS EL URL DESTINO
            startRequestTime = time.time()                                      # TIEMPO DE INICIO DE PETICION
            infoSend["startRequestTime"]=startRequestTime                       # ALMACENAMOS EL TIEMPO PARA ENVIARLO
            requests.post(url, data=json.dumps(infoSend), headers=headers)      # REALIZAMOS LA PETICION
            endTimeProcess = time.time()                                        # TIEMPO FINAL DEL PROCESO
            processTime = endTimeProcess-startTimeProcess                       # Tiempo FINAL DEL PROCESO
            messageInfo = {"OPERATION": "CREATE_NODE",
                   "READ_TIME": readTime,
                   "PROCESS_TIME":processTime,
                   "ARRIVAL_TIME":0,
                   "START_REQUEST_TIME":startRequestTime}
            loggerInfoSet(messageInfo)                                          # LOGGER INFO SET
            presentationValue = False                                           # DESACTIVAMOS LA PRESENTACION
            break
        except requests.ConnectionError as e:
            # loggerError.error('CONNECTION_REFUSED PRESENTATION_SEND {} {}'.format(nodeManager.nodeId, contPresentation))
            msg = "ERROR PRESENTATION_SEND_{} {}".format(contPresentation,e)
            contPresentation = contPresentation + 1
            if (contPresentation == 10):
                msg = "CONNECTION_REFUSED PRESENTATION_SEND_{} {}".format(contPresentation,e)
                return jsonify({"response":msg})
            time.sleep(5)
    
    return "CONNECTION_SUCCESSFULLY"

if __name__ == '__main__':
    presentation()
    app.run(host= '0.0.0.0',port=state['dockerPort'],debug=False,use_reloader=False)