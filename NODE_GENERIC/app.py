# from asyncio.log import logger
from datetime import datetime
from email import message
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


# -----------------------------------------------------msg------------------------------------------------------------------
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# -----------------------------------------------------------------------------------------------------------------------

# -------- 
def loggerInfoSet(message:json):
    global loggerInfo
    # OPERATION READ_TIME PROCESS_TIME ARRIVAL_TIME START_RESQUEST_TIME LATENCE_TIME
    msg = "{} {} {} {} {} {}".format(message["OPERATION"],
                                           message["READ_TIME"],
                                           message["PROCESS_TIME"],
                                           message["ARRIVAL_TIME"],
                                           message["START_REQUEST_TIME"],
                                           (message["ARRIVAL_TIME"]-message["START_REQUEST_TIME"]))
    loggerInfo.info(msg) 

def loggerErrorSet(message):
    global loggerError
    # OPERATION READ_TIME PROCESS_TIME ARRIVAL_TIME START_RESQUEST_TIME LATENCE_TIME
    # msg = "{} {} {} {} {} {}".format(message["OPERATION"],
    #                                        message["READ_TIME"],
    #                                        message["PROCESS_TIME"],
    #                                        message["ARRIVAL_TIME"],
    #                                        message["START_RESQUEST_TIME"],
    #                                        (message["ARRIVAL_TIME"]-message["START_REQUEST_TIME"]))
    loggerError.error(message)

# -----------------------------------------------------------------------------------------------------------------------
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# -----------------------------------------------------------------------------------------------------------------------


# -------- FUNCION QUE AGREGARA LOS NODOS TRABAJADORES
@app.route('/workers', methods = ['POST'])
def add_worker():
    """ Esta funcion estara dedicada a guardar la informacion de los workers.

        La funcion esta recibiendo un json de con la imsgformacion del nodo worker
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
        message = "501-ERROR CREATE_NODE {}".format(e)      # MENSAJE DE ERROR
        loggerErrorSet(message)
        return  jsonify({"response":message}),501               # RETORNO 501-LECTURA
    
    try:
        startTimeProcess = time.time()                          # TIEMPO INCIAL DEL PROCESO
        nodeNew = NodeWorker(**nodeNewInfo["nodeInfo"])         # PROCESO DE CREAR EL NODO TRABAJADOR
        nodeLocal.addNode(nodeNew)                              # AGREGAMOS EL NODO TRABAJADOR
        endTimeProcess = time.time()                            # TIEMPO FINAL DEL PROCESO
        processTime = endTimeProcess - startTimeProcess         # TIEMPO DE PROCES
        send = True
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
    except Exception as e:
        message = "502-ERROR CREATE_NODE {}".format(e)   # MENSAJE DE ERROR
        loggerErrorSet(message)
        return jsonify({"response":message}),502                # RETORNO 502-PROCCESING
    
   



# -----------------------------------------------------------------------------------------------------------------------
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# -----------------------------------------------------------------------------------------------------------------------


# -------- FUNCION MOSTRARA LOS NODOS PRESENTADOS
@app.route('/workers', methods = ['GET'])
def show_worker():
    global nodeLocal
    try:
        nodes = nodeLocal.getNodes()            # ALMACENAMOS LOS NODOS DISPONIBLES
    except Exception as e:
        message = "501-ERROR READ_NODES {}".format(e)
        loggerErrorSet(message)
        return jsonify({"response":message}), 501
    try:    
        nodesReturn = []                        # LISTA VACIA DE RETORNO
        for node in nodes:
            nodesReturn.append(node.toJSON())   # GUARDAMOS EL FORMATO JSON DE CADA NODO
        return jsonify(nodesReturn),200             # RETORNAMOS
    except Exception as e:
        message = "502-ERROR PROCESS_NODES {}".format(e)
        loggerErrorSet(message)
        return jsonify({"response":message}), 502


# -----------------------------------------------------------------------------------------------------------------------
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# -----------------------------------------------------------------------------------------------------------------------


# -------- FUNCION MOSTRARA LA TABLA DE EVENTOS
@app.route('/status', methods = ['GET'])
def send_balance():
    global tableState
    return jsonify(tableState)      # RETORNA LOS VALORES DE LA TABLA DE EVENTOS

# -----------------------------------------------------------------------------------------------------------------------
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# -----------------------------------------------------------------------------------------------------------------------


# -------- FUNCION PARA ACTUALIZAR LA TABLA DE EVENTOS
def updateStateTable(jsonRespone,numberEvent,procesList,nodeId):
    """
    Esta funcion esta dedicada a actualizar la tabla de eventos del nodo.

    Args:
        jsonRespone (json): json retornado por el nodo de la peticion
        numberEvent (int): numero de evento ejecutado
        procesList (list): lista de cubos ejecutados en el nodeID
        nodeId (str): identificador del nodo de la peticion

    Returns:
        str: "OK" si todo se ejecuto perfectamente
    """
    global tableState
    global nodeLocal
    try:
        eventName = "event_{}".format(numberEvent)              # GENERAMOS EL ID DEL EVENTOS
        jsonState = {"NODE_ID":nodeId,                          # GUARDAMOS EL ID DEL NODO
                    "DATA_PROCESS": procesList,                 # GUARDAMOS EL PROCESO
                    "INFO_RESPONSE":jsonRespone}                # TIEMPOS DEL NODO
    except Exception as e:
        message = "501-ERROR READ_EVENTS {}".format(e)
        loggerErrorSet(message)
        return jsonify({"response":message}),501
    
    try:
        if (eventName in tableState["events"]):                 # VERIFCA EL ID DEL EVENTOS
            tableState["events"][eventName].append(jsonState)   # GUARDAMOS EL JSON DE EVENTO
        else:
            tableState["events"][eventName] = list()            # LO IGUALAMOS A UNA LISTA
            tableState["events"][eventName].append(jsonState)   # GUARDAMOS EL JSON DE EVENTO
        return "OK",200
    except Exception as e:
        message = "502-ERROR PROCESS_EVENTS {}".format(e)
        loggerErrorSet(message)
        return jsonify({"response":message}),502
    

# -----------------------------------------------------------------------------------------------------------------------
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# -----------------------------------------------------------------------------------------------------------------------


# -------- FUNCION PARA EMPEZAR UNA PETICION
def sendData(url,jsonSend,numberEvent,procesList,nodeId):
    """
    Funcion encargada para enviar los datos en un formato json, y mandar a actualizar los eventos 
    generados dentro del nodo.

    Args:
        url (str): url destino
        jsonSend (json): json a enviar
        numberEvent (int): numero de evento
        procesList (list): cubos ejecutados
        nodeId (str): identificacion del nodo

    Returns:
        str: "OK" si todo se ejecuto perfectamente
    """
    try:
        headers = {'PRIVATE-TOKEN': '<your_access_token>', 'Content-Type':'application/json'}
        response = requests.post(url, data=json.dumps(jsonSend), headers=headers)
        jsonResponse = response.json()
        updateStateTable(jsonRespone=jsonResponse,numberEvent=numberEvent, procesList=procesList, nodeId=nodeId)
        return "OK",200
    except Exception as e:
        message = "503-ERROR COMUNICATION_REQUEST {} {}".format(nodeId,e)
        loggerErrorSet(message)
        return jsonify({"response":message}), 503

@app.route('/prueba', methods = ['GET'])
def pruebaSend():
    global nodeLocal
    
    nodes= nodeLocal.getNodes()
    numberEvent = nodeLocal.getNumberEvents()
    for worker in nodes:
        url = worker.getURL(mode=nodeLocal.getMode(), endPoint="/respose")
        
        startRequestTime = time.time()
        jsonSend={"prueba":"prueba1",
                    "startRequestTime": startRequestTime}
        response = sendData(url=url, 
                            jsonSend=jsonSend,
                            numberEvent=numberEvent, 
                            procesList=[worker.getID()],
                            nodeId=worker.getID())
    return jsonify(jsonSend),200

@app.route('/response', methods = ['GET'])
def pruebaResponde():
    """
    Resumen de la funcion a realizar

    Returns:
        _type_: _description_
    """
    global nodeLocal
    try:
        arrivalTime = time.time()                               # TIEMPO DE LLEGADA (arrivalTime)
        requestJson = request.get_json()                        # RECIBIR LOS PARAMETROS
        startRequestTime = requestJson["startRequestTime"]      # TIEMPO DE INICIO DE SOLICITUD (startRequestTime)
        
        # -------- LECTURA
        time.sleep(1)                                           # LECTURA
        # -------- LECTURA
        
        endReadTime = time.time()                               # FIN DE LETURA
        readTime = endReadTime - arrivalTime                    # TIEMPO DE LECTURA
    except Exception as e:
        message = "ERROR READ_ENDPOINT {} {}".format(nodeId,e)
        loggerErrorSet(message)
        return jsonify({"response":message}), 501
    
    try:
        # PROCESO
        time.sleep(2)                                           # PROCESO
        endProcessTime = time.time()                            # FIN DEL PROCESO
        processTime = endProcessTime-endReadTime                # TIEMPO DE PROCESO
        latenceTime = arrivalTime- startRequestTime
        messageInfo = {"OPERATION": "CREATE_NODE",              # MENSAJE PARA EL LOGGER INFO
                        "READ_TIME": readTime,
                        "PROCESS_TIME":processTime,
                        "ARRIVAL_TIME":arrivalTime,
                        "START_REQUEST_TIME":startRequestTime}
        
    except Exception as e:
        message = "ERROR PROCESS_ENDPONIT {} {}".format(nodeId,e)
        loggerErrorSet(message)
        return jsonify({"response":message}), 502
        
    
    
    jsonReturn ={
            "CODE_STATUS": 200,
            "RESPONSE_STATUS": "SUCCESSFULLY",
            "OPERATION": "TEST",
            "READ_TIME": readTime,
            "ARRIVAL_TIME": arrivalTime,
            "START_REQUEST_TIME": startRequestTime,
            "LATENCIE_TIME": latenceTime 
        }
    return jsonify(jsonReturn),200
    
    
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
            msg = "WARNING COMUNICATION_PRESENTATION {} {}".format(contPresentation,e)
            contPresentation = contPresentation + 1
            if (contPresentation == 10):
                msg = "504-ERROR COMUNICATION_PRESENTATION {} {}".format(contPresentation,e)
                return jsonify({"response":msg}), 504
            time.sleep(5)
    
    return "CONNECTION_SUCCESSFULLY"

if __name__ == '__main__':
    presentation()
    app.run(host= '0.0.0.0',port=state['dockerPort'],debug=False,use_reloader=False)