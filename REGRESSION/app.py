# from asyncio.log import logger
import sys
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
sendData = mtd.trueOrFalse(os.environ.get('SEND',"0")) # CONDICIONAL DE ENVIO DE DATOS

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

logs_info_file = './data{}/info'.format(logPath)       # ESTABLECER RUTA DE LOGS INFO
if (not os.path.exists(logs_info_file)):
    os.mkdir(logs_info_file)
logs_info_file = './data{}/info/{}_info.log'.format(logPath,nodeId)       # ESTABLECER RUTA DE LOGS INFO

logs_error_file = './data{}/error'.format(logPath)     # ESTABLECER RUTA DE LOGS ERROR# -------- LOGGER INFO
if (not os.path.exists(logs_error_file)):
    os.mkdir(logs_error_file)
logs_error_file = './data{}/error/{}_error.log'.format(logPath,nodeId)     # ESTABLECER RUTA DE LOGS ERROR# -------- LOGGER INFO
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
            "events":0,
            "algorithm": os.environ.get('ALGORITHM','RR')}                                                 # CANTIDAD DE EVENTOS CALCULADOS

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
tableState = {"totalEvents":0,    # TOTAL DE EVENTOS EJECUTADOS
            "nodeID":nodeId,    # ID DEL NODO LOCAL
            "events":{}}        # LISTA DE INFORMACION DE LOS EVENTOS


# -----------------------------------------------------msg------------------------------------------------------------------
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# -----------------------------------------------------------------------------------------------------------------------

# -------- 
def loggerInfoSet(message:json):
    """
        Metodo que despligea en consola y guarda en el archivo .log correspondiete
        a nodo en el que se este ejecurando un evento.
        
        El json a recibir es con la siguiente estructura:
        json: { message["OPERATION"]:str,
                message["READ_TIME"]:int,
                message["PROCESS_TIME"]:int,
                message["ARRIVAL_TIME"]:int,
                message["START_REQUEST_TIME"]:int,
                (message["ARRIVAL_TIME"]-message["START_REQUEST_TIME"])

    Args:
        message (): json
    """
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
    exc_type, exc_obj, exc_tb = sys.exc_info()
    lineError = exc_tb.tb_lineno
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    msg = "{} - LineCode={} - CODE_ERROR {}".format(fname,lineError, message)
    loggerError.error(msg)
    
def loggerErrorFlag(message):
    global loggerError
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
        message = "501-ERROR CREATE_NODE {}".format(e)          # MENSAJE DE ERROR
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
    """
        Fucion encargada de mostrar la infromacion de los nodos trabajadores

    Returns:
        json: infromacion de los nodos trabajadores
    """
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
    """
        Funcion que nos ayudara a retornar el estado de los eventos EJECUTADOS
        dentro del nodo, con sus diferentes trabajadores.
        Esta funcion guardara infromacion relevante de los proceso hechos, asi
        como los tiempos obtenidos dentro del nodo.

    Returns:
        json: infromacion de los eventos
    """
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
        eventName = "event_{}".format(numberEvent)                  # GENERAMOS EL ID DEL EVENTOS
        jsonState = {"NODE_ID":nodeId,                              # GUARDAMOS EL ID DEL NODO
                    "DATA_PROCESS": procesList,                     # GUARDAMOS EL PROCESO
                    "INFO_RESPONSE":jsonRespone}                    # TIEMPOS DEL NODO
    except Exception as e:
        message = "501-ERROR READ_EVENTS {}".format(e)
        loggerErrorSet(message)
        return jsonify({"response":message}),501
    
    try:
        if (eventName in tableState["events"]):                     # VERIFCA EL ID DEL EVENTOS
            tableState["events"][eventName].append(jsonState)       # GUARDAMOS EL JSON DE EVENTO
            tableState['totalEvents']=len(tableState["events"])# ACTUALIZAMOS LA CANTIDAD DE NODOS
        else:   
            
            tableState["events"][eventName] = list()                # LO IGUALAMOS A UNA LISTA
            tableState["events"][eventName].append(jsonState)       # GUARDAMOS EL JSON DE EVENTO
            tableState['totalEvents']=len(tableState["events"])# ACTUALIZAMOS LA CANTIDAD DE NODOS
        return "OK",200
    except Exception as e:
        message = "502-ERROR PROCESS_EVENTS {}".format(e)
        loggerErrorSet(message)
        return jsonify({"response":message}),502
    

# -----------------------------------------------------------------------------------------------------------------------
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# -----------------------------------------------------------------------------------------------------------------------


# -------- FUNCION PARA EMPEZAR UNA PETICION
def sendDataVal(url,jsonSend,nodeId):
    """
    Funcion encargada para enviar los datos en un formato json, y mandar a actualizar los eventos 
    generados dentro del nodo.

    Args:
        url (str): url destino
        jsonSend (json): json a enviar
        nodeId (str): identificacion del nodo

    Returns:
        str: "OK" si todo se ejecuto perfectamente
    """
    try:
        headers = {'PRIVATE-TOKEN': '<your_access_token>',  # HEADER DE LA PETICION
                   'Content-Type':'application/json'}
        loggerErrorFlag("Sending --------- {}".format(url))
        response = requests.post(url,                       # URL DESTINO
                    data=json.dumps(jsonSend),              # JSON A ENVIAR
                    headers=headers)                        # ASIGNAMOS HEADERS
        return "OK",200
    except Exception as e:
        message = "503-ERROR COMUNICATION_REQUEST {} {}".format(nodeId,e)
        loggerErrorSet(message)
        return jsonify({"response":message}), 503


# -----------------------------------------------------------------------------------------------------------------------
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# -----------------------------------------------------------------------------------------------------------------------


# -------- FUNCION PARA REALIZAR UNA REGRESSION LINEAL
@app.route('/analytics/regression', methods = ['POST'])
def regression():
    """
        END-POINT dedicado a realizar una regression entre dos o mas tuplas
        donde la primera posicion corresponde a la variable "X" y la segunda posicion
        corresponde a la variable "Y".

        
        Tranformation json de entrada:
            {
                "columns": [[var1,var2], [var3,var4], ..., [varN,varM]]
            }
        
        Nota: 

    Returns:
        json: descripcion de los tiempos del proceso
    """
    global nodeLocal
    global sourcePath
    global nodeManager
    global sendData
    
    try:
        # -------- LECTURA
        arrivalTime = time.time()                                   # TIEMPO DE LLEGADA    
        nodes = nodeLocal.getNodes()                                # GUARDAMOS LA INFO DE LOS NODOS TRABAJADORES
        numberEvent = nodeLocal.getNumberEvents()                   # CANTIDAD DE EVENTOS GENERADOS AL MOMENTO
        requestJson = request.get_json()                            # RECIBIR LOS PARAMETROS
        startRequestTime = requestJson["startRequestTime"]          # TIEMPO DE INICIO DE SOLICITUD (startRequestTime)
        cubes = requestJson["cubes"]                                # CUBOS DE ENTRADA
        readTimeSum = 0
        comunicationTimeSum=0
        # CARGAREMOS TODAS LAS FUENTES QUE TENGAN LA KEY DE FUSION
        sourcesDF = list()                                                                       # LISTADO DE DATAFRAMES
        for posCube, cubeName in enumerate(cubes.keys()):
            cube = cubes[cubeName]
            
            if("regression" in cube["Tranformation"].keys()):    
                source = cube["nameFile"]
                
                if(nodeManager.getID()=="-"):                                                   # VERIFICA SI EXISTE UN NODO MANAGER
                    pathString = ".{}/{}".format(sourcePath,source)
                    df = pd.read_csv(pathString)
                
                else:                                                                           # SI EXISTE CONCATENA EL NODE ID DEL MANAGER
                    df = pd.read_csv('.{}/{}/{}'.format(sourcePath,nodeManager.getID(),source))
                
                sourcesDF.append([df,cubeName])                                                            # GUARDAMOS EN MEMORIA LOS DATAFRAMES
                del df
            else:
                raise Exception("No hay parametros")
        # -------- LECTURA
        endReadTime = time.time()                               # FIN DE LETURA
        readTime = endReadTime - arrivalTime                    # TIEMPO DE LECTURA
        readTimeSum = readTimeSum + readTime
    except Exception as e:
        message = "ERROR READ_PARAMAS_ENDPOINT {} {}".format(nodeId,e)
        loggerErrorSet(message)
        return jsonify({"response":message}), 501
    
    
    
    try:
        # -------- regression
        startFusionTime = time.time()                               # TIEMPO DE INICIO DEL RANGOS
        processTimeSum = 0
        listNamesFusion = list()
        for posSource,source in enumerate(sourcesDF):
            nameSource = source[1]
            cube = cubes[nameSource]['Tranformation']['regression']
            df = source[0]
            columnsReg = cube["columns"]
            
            if ("normalize" in cube.keys()):
                normalizeVal = mtd.trueOrFalse(cube['normalize'])
                if (normalizeVal!=False):
                    df = mtd.normalize(df[columnsReg],columnsReg)
            
            for tupla in columnsReg:
                xName = tupla[0]
                yName = tupla[1]
                
                X = df[xName].values.reshape(-1,1)
                y = df[yName].values
                
                regressionLabel, R2_score = mtd.regressionLineal(X=X, y=y)
                regressionLabel = mtd.plotRegression(X=X, y=y, xLabel=xName, 
                                                     yLabel=yName, 
                                                     predicts= regressionLabel, 
                                                     sourcePath=sourcePath, 
                                                     nameSource=nameSource,
                                                     nodeId=nodeLocal.getID(),
                                                     namePlot=nameSource,
                                                     r2=R2_score)
                nameColumn = "RegL_{}".format("_".join(tupla))
                df[nameColumn] = regressionLabel
                loggerErrorFlag(" ------------ {}".format(nameColumn))
            del regressionLabel
            del X, y                 
            nameFile = "{}".format(nameSource)
            directoryFile = ".{}/{}/{}.csv".format(sourcePath, nodeLocal.getID(), nameFile)     # GUARDAMOS EL DIRECTORIO DEL NODO LOCAL                
            df.to_csv("{}".format(directoryFile), index=False)
            # -------- NEX NODOS
            # if ("addColumnIn" in cube.keys()):
            #     cubeNext["columns"]= listColummn
            #     cubes[source[1]]['Tranformation'][nextC] = cubeNext
            # -------- NEXT NODO
            del df
        endFusionTime = time.time()                                 # TIEMPO DE FIN DE LA FUSION
        processTimeSum = processTimeSum + (endFusionTime - startFusionTime)
        del sourcesDF
        # -------- FUSION
    except Exception as e:
        message = "ERROR REGRESSION_ENDPOINT {} {}".format(nodeId,e)
        loggerErrorSet(message)
        return jsonify({"response":message}), 502
    
    try:
        #  -------- COMUNICACION
        if (sendData == True):
            modeToSend = nodeLocal.getMode()                    # GUARDAMOS EL TIPO DE COMUNICACION DE
            endPoint = requestJson["PIPELINE"][0]               # GUARDAMOS EL ENDPOINT DE LOS TRABAJADORES
            del requestJson["PIPELINE"][0]
            for posNode, node in enumerate(nodes):
                startComunicationTime = time.time()
                sendJson = requestJson.copy()
                sendJson['cubes'] = cubes
                loggerErrorFlag(sendJson['cubes'].keys())
                url = node.getURL(mode=modeToSend, endPoint=endPoint)
                startRequestTime = time.time()
                sendJson["startRequestTime"]=startRequestTime
                t = threading.Thread(target=sendDataVal, args=(url,sendJson,node.getID()))
                t.start() 
                endComunicationTime = time.time()
                comunicationTimeSum = comunicationTimeSum + (endComunicationTime - startComunicationTime)
        #  -------- COMUNICACION
        # UPDATE TABLE STATUS
        messageInfo = {"OPERATION": "REGRESSION",           # MENSAJE PARA EL LOGGER INFO
                        "READ_TIME": readTimeSum,
                        "PROCESS_TIME":processTimeSum,
                        "ARRIVAL_TIME":arrivalTime,
                        "START_REQUEST_TIME":startRequestTime}
        updateStateTable(jsonRespone=messageInfo,                       # JSON A GUARDAR EN EVEENTOS
                            numberEvent=numberEvent,                    # NUMERO DE EVENTOS
                            procesList=listNamesFusion,                 # ARCHIVOS PROCESADOS
                            nodeId=nodeId)                              # ID DEL NODO TRABAJADOR
        nodeLocal.setNumberEvents()                                     # SE INCREMENTA EL EVENTO CUANDO TERMINA EL PROCESO
        loggerInfoSet(message=messageInfo)
        return jsonify(messageInfo),200
    except Exception as e:
        message = "ERROR COMUNICATION_ENDPONIT {} {}".format(nodeId,e)
        loggerErrorSet(message)
        return jsonify({"response":message}), 503
    
  

# -----------------------------------------------------------------------------------------------------------------------
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# -----------------------------------------------------------------------------------------------------------------------

@app.route('/prueba', methods = ['POST'])
def pruebaSend():
    global nodeLocal
    
    nodes= nodeLocal.getNodes()
    numberEvent = nodeLocal.getNumberEvents()
    for worker in nodes:
        url = worker.getURL(mode=nodeLocal.getMode(), endPoint="response")
        loggerInfo.info("\nURL - {}".format(url))
        
        startRequestTime = time.time()
        jsonSend={"prueba":"prueba1",
                    "startRequestTime": startRequestTime}
        response = sendData(url=url, 
                            jsonSend=jsonSend,
                            numberEvent=numberEvent,                        
                            procesList=[worker.getID()],                    # COLOCAR LOS ARCHIVOS PROCESADOS
                            nodeId=worker.getID())                          # ID DEL NODO TRABAJADOR
    nodeLocal.setNumberEvents()
    return jsonify(jsonSend),200

@app.route('/response', methods = ['POST'])
def pruebaResponde():
    global nodeLocal
    try:
        arrivalTime = time.time()                               # TIEMPO DE LLEGADA (arrivalTime)
        requestJson = request.get_json()                        # RECIBIR LOS PARAMETROS
        startRequestTime = requestJson["startRequestTime"]      # TIEMPO DE INICIO DE SOLICITUD (startRequestTime)
        
        # -------- LECTURA
        loggerErrorFlag(requestJson['cubes'])
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
        messageInfo = {"OPERATION": "REQUEST_NODE",              # MENSAJE PARA EL LOGGER INFO
                        "READ_TIME": readTime,
                        "PROCESS_TIME":processTime,
                        "ARRIVAL_TIME":arrivalTime,
                        "START_REQUEST_TIME":startRequestTime}
        loggerInfoSet(message=messageInfo)
        
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
            messageInfo = {"OPERATION": "SEND_PRESENTATION",
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
    app.run(host= '0.0.0.0',port=state['dockerPort'],debug=False)