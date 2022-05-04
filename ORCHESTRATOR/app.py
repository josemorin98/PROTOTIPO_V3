# from asyncio.log import logger
from datetime import datetime
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
import dask.dataframe as dd

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

mtd.initEspatial()
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
    msg = "{} - {} - CODE_ERROR {}".format(fname,lineError, message)
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
        headers = {'PRIVATE-TOKEN': '<your_access_token>',  # HEADER DE LA PETICION
                   'Content-Type':'application/json'}
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


# -------- FUNCION PARA FILTRAR MEDIANTE EL ESPACIAL
@app.route('/balance/espatial',methods = ['POST'])
def fillterEspatial():
    global nodeLocal
    global sourcePath
    global nodeManager
    
    try:
        # -------- LECTURA
        arrivalTime = time.time()                                   # TIEMPO DE LLEGADA    
        nodes = nodeLocal.getNodes()                                # GUARDAMOS LA INFO DE LOS NODOS TRABAJADORES
        numberEvent = nodeLocal.getNumberEvents()                   # CANTIDAD DE EVENTOS GENERADOS AL MOMENTO
        requestJson = request.get_json()                            # RECIBIR LOS PARAMETROS
        startRequestTime = requestJson["startRequestTime"]          # TIEMPO DE INICIO DE SOLICITUD (startRequestTime)
        cubes = requestJson["cubes"]                                # CUBOS DE ENTRADA
        paramsOrchestrator = requestJson["paramsOrchestrator"]      # PARAMETROS DEL ORQUESTADOR
        balanceType = paramsOrchestrator["balanceType"][0]          # TIPO DE BALANCEO {FLT_1, FLT_2, ... ,FLT_n}
        paramsBalancer = paramsOrchestrator["paramsBalancer"][0]    # PARAMETROS DEL BALANCEO [paramsFLT_1]
        readTimeSum = 0
        if (balanceType == "ESPATIAL"):
            typeBalanceEspatial = paramsBalancer["typeEspatial"]                    # TIPO DE ESPACIAL
            toBalanceData = mtd.typeBalnceEspatial(typeBalance=typeBalanceEspatial) # EXTRAMOS EL BALANCEO ESPACIAL
        else:
            e="NOT ESPATIAL"
            message = "ERROR READ_ENDPOINT {} {}".format(nodeId,e)
            loggerErrorSet(message)
            return jsonify({"response":message}), 501
        # -------- LECTURA
        
        endReadTime = time.time()                               # FIN DE LETURA
        readTime = endReadTime - arrivalTime                    # TIEMPO DE LECTURA
        readTimeSum = readTimeSum + readTime
    except Exception as e:
        message = "ERROR READ_PARAMAS_ENDPOINT {} {}".format(nodeId,e)
        loggerErrorSet(message)
        return jsonify({"response":message}), 501
    
    
    try:
        # -------- PROCESO
        #__________________ BALANCEO
        startBalancer = time.time()
        workersCant = len(nodes)                            # CANTIDAD DE NODOS PRESENTADOS
        initBoxWorkers = mtd.initWorkresArray(workersCant)  # CREAMOS LAS CAJAS VACIAS DE LOS TRABAJADOR PARA EL BALANEO DE CARGA
        algorithmBalancer = nodeLocal.getAlgorithm()        # ALGORITMO DE BALANEO
        variablesToBalance=mtd.getItems(itemName="Espatial",cubes=cubes)            # OBTENEMOS LA COLUMNA DE CADA FUENTE
        if (algorithmBalancer=="TC"):
            sourcesFiles = mtd.getItems(itemName="nameFile",cubes=cubes)            # OBTENEMOS LOS NOMBRES DE LOS ARCHIVOS DE LAS FUENETES DE DATOS
            
            balanceData = mtd.toBalanceDataTC(initWorkers=initBoxWorkers,           # CAJAS VACIAS PARA LAS FUENTES
                                        balanceData=toBalanceData,                  # LISTA DE ESPACIAL A BALANCEAR
                                        algorithm=algorithmBalancer,                # ALGORITMO DE BALANCEO
                                        sources=sourcesFiles,                       # NOMBRE DE LOS ARCHIVOS DE CADA FUENTE
                                        varSpatial=variablesToBalance,              # COLUMNA DE CADA FUENTE
                                        sourcePath=sourcePath)                      # DIRECCION DE ORIGEN DE LOS ARCHIVOS
        else:
            balanceData = mtd.toBalanceData(initWorkers=initBoxWorkers,
                                        balanceData=toBalanceData,
                                        algorithm=algorithmBalancer)
        endBalancer = time.time()
        balancerTime = endBalancer - startBalancer
        #__________________ BALANCEO
        
        #__________________ FILTRADO
        del paramsOrchestrator["balanceType"][0]            # ELIMINAMOS BALANCEO REALIZADO
        modeToSend = nodeLocal.getMode()                    # GUARDAMOS EL TIPO DE COMUNICACION DE
        endPoint = requestJson["PIPELINE"][0]               # GUARDAMOS EL ENDPOINT DE LOS TRABAJADORES
        del requestJson["PIPELINE"][0]                      # ELIMINAMOS EL ENDPOINT DE LOS TRABAJADOR
        
        if (balanceType == "ESPATIAL"):
            comunicationTimeSum = 0                                                 # SUMA DE TIEMPOS DE COMUNICACION
            processTimeSum = 0
            sourcesFiles = mtd.getItems(itemName="nameFile",cubes=cubes)            # OBTENEMOS LOS NOMBRES DE LOS ARCHIVOS DE LAS FUENETES DE DATOS

            sourcesDF = list()                                                       # LISTADO DE DATAFRAMES
            try:
                # -------- LECTURA FILTRO
                for posSource,source in enumerate(sourcesFiles):
                    startReadTime = time.time()                                                     # INICIO DEL TIEMPO DE LECTURA
                    if(nodeManager.getID()=="-"):                                                   # VERIFICA SI EXISTE UN NODO MANAGER
                        # df = pd.read_csv('.{}/{}'.format(sourcePath,source))
                        df = dd.read_csv('.{}/{}'.format(sourcePath,source))
                    else:                                                                           # SI EXISTE CONCATENA EL NODE ID DEL MANAGER
                        # df = pd.read_csv('.{}/{}/{}'.format(sourcePath,nodeManager.getID(),source))
                        df = dd.read_csv('.{}/{}/{}'.format(sourcePath,nodeManager.getID(),source))
                    endReadTime = time.time()                                                       # FIN DEL TIEMPO DE LECTURA
                    readTimeFile = (endReadTime - startReadTime)
                    readTimeSum = readTimeSum + readTimeFile
                # -------- LECTURA FILTRO
                
                # -------- PROCESO AGRUPADO
                    startGruopTime = time.time()                                                    # INICIO DEL TIEMPO DE AGRUPADO
                    df = df.groupby(variablesToBalance[posSource])                                  # AGRUPAMIENTO DE LOS VALORES
                    sourcesDF.append(df)                                                            # GUARDAMOS EN MEMORIA LOS DATAFRAMES
                    endGroupTime = time.time()                                                      # FIN DEL TIEMPO DE AGRUPADO
                    processTimeSum = processTimeSum + (endGroupTime - startGruopTime)               # SUMA DEL TIEMPO DE AGRUPADO
                # -------- LECTURA FILTRO
            except Exception as e:
                            message = "ERROR READ_FILTERING_ENDPOINT {} {}".format(nodeId,e)
                            loggerErrorSet(message)
                            return jsonify({"response":message}), 501
            
            # iteracion de nodos
            try:
                startFilteringTime = time.time()
                for valueGroup in range(mtd.maxValueInList(balanceData)):
                    for posNode, node in enumerate(nodes):
                                                    # INICIO DE TIEMPO DE FLTRADO
                        
                        if (valueGroup < len(balanceData[posNode])):                # VERIFICAMOS SI EL VALOR A EXTRAER ESTA DENTRO DE LA POSICION ACUTAL
                            espatialValue = balanceData[posNode][valueGroup]        # EXTRAMMOS EL ESPACIAL A MANDAR
                        else:
                            break
                        cubesNew = {}
                        for posSource,source in enumerate(sourcesDF):               # ITERAMOS LOS DATAFRAMES CARGADOS
                            rowByEspatial = source.get_group(espatialValue)         # ETRAEMOS LOS VALORES DE CADA DATAFRAME
                            if (len(rowByEspatial.index)>0):                        # VERIFICAMOS QUE TENGA VALORES
                                
                                cubeName = mtd.getNameCube(cubes=cubes,posCube=posSource)                       # OBTENMOS EL NOMBRE DEL CUBO
                                nameFile = "{}_{}".format(cubeName, espatialValue.replace(" ","_"))         # GENERAMOS EL NUEVO NOMBRE DEL ARCHIVO
                                loggerErrorFlag(nameFile)
                                auxCube = cubes[cubeName].copy()                                                # GENERAMOS UNA COPIA DEL CUBO PARA TRABAJAR SOBRE ELLA
                                auxCube["nameFile"] = "{}.csv".format(nameFile)                                                  # ASIGNAMOS EL NUEVO NOMBRE
                                cubesNew[nameFile] = auxCube                                                    # ASIGNAMOS LOS VALORES
                                loggerErrorFlag(cubesNew.keys())
                                directoryFile = ".{}/{}/{}.csv".format(sourcePath, nodeLocal.getID(), nameFile)     # GUARDAMOS EL DIRECTORIO DEL NODO LOCAL
                                rowByEspatial.to_csv(directoryFile, index = False,single_file=True)
                        
                        try:
                        # -------- COMUNICATION ENVIO DEL FILTERADO
                            startComunicationTime = time.time()
                            sendJson = requestJson.copy()
                            sendJson['cubes'] = cubesNew
                            loggerErrorFlag(sendJson['cubes'].keys())
                            url = node.getURL(mode=nodeLocal.getMode(), endPoint="response")
                            startRequestTime = time.time()
                            sendJson["startRequestTime"]=startRequestTime
                            t = threading.Thread(target=sendData, args=(url,sendJson,numberEvent,balanceData,node.getID()))
                            t.start() 
                            endComunicationTime = time.time()
                            comunicationTimeSum = comunicationTimeSum + (endComunicationTime - startComunicationTime)
                        # -------- COMUNICATION ENVIO DEL FILTERADO
                        except Exception as e:
                            message = "ERROR COMUNICATION_ENDPONIT {} {}".format(nodeId,e)
                            loggerErrorSet(message)
                            return jsonify({"response":message}), 502
                        
                endFilteringTime = time.time()                        
                filteringTime = (endFilteringTime - startFilteringTime) - comunicationTimeSum
                processTimeSum = processTimeSum + filteringTime
            except Exception as e:
                message = "ERROR PROCESS_ENDPONIT {} {}".format(nodeId,e)
                loggerErrorSet(message)
                return jsonify({"response":message}), 502
            
        else:
            e="NOT ESPATIAL"
            message = "ERROR READ_ENDPOINT {} {}".format(nodeId,e)
            loggerErrorSet(message)
            return jsonify({"response":message}), 501
        # UPDATE TABLE STATUS
        messageInfo = {"OPERATION": "ORCHESTRATION_ESPATIAL",           # MENSAJE PARA EL LOGGER INFO
                        "READ_TIME": readTimeSum,
                        "PROCESS_TIME":processTimeSum,
                        "ARRIVAL_TIME":arrivalTime,
                        "START_REQUEST_TIME":startRequestTime}
        updateStateTable(jsonRespone=messageInfo,                       # JSON A GUARDAR EN EVEENTOS
                            numberEvent=numberEvent,                    # NUMERO DE EVENTOS
                            procesList=balanceData,                     # ARCHIVOS PROCESADOS
                            nodeId=nodeId)                              # ID DEL NODO TRABAJADOR
        nodeLocal.setNumberEvents()                                     # SE INCREMENTA EL EVENTO CUANDO TERMINA EL PROCESO
        loggerInfoSet(message=messageInfo)
    except Exception as e:
        message = "ERROR PROCESS_ENDPONIT {} {}".format(nodeId,e)
        loggerErrorSet(message)
        return jsonify({"response":message}), 502
    
    return jsonify(),200



# -----------------------------------------------------------------------------------------------------------------------
# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# -----------------------------------------------------------------------------------------------------------------------


# -------- FUNCION PARA FILTRAR MEDIANTE EL TEMPORAL
@app.route('/balance/temporal',methods = ['POST'])
def balanceTemporal():
    global nodeLocal
    global sourcePath
    global nodeManager
    
    try:
        # -------- LECTURA
        arrivalTime = time.time()                                   # TIEMPO DE LLEGADA    
        nodes = nodeLocal.getNodes()                                # GUARDAMOS LA INFO DE LOS NODOS TRABAJADORES
        numberEvent = nodeLocal.getNumberEvents()                   # CANTIDAD DE EVENTOS GENERADOS AL MOMENTO
        requestJson = request.get_json()                            # RECIBIR LOS PARAMETROS
        startRequestTime = requestJson["startRequestTime"]          # TIEMPO DE INICIO DE SOLICITUD (startRequestTime)
        cubes = requestJson["cubes"]                                # CUBOS DE ENTRADA
        paramsOrchestrator = requestJson["paramsOrchestrator"]      # PARAMETROS DEL ORQUESTADOR
        balanceType = paramsOrchestrator["balanceType"][0]          # TIPO DE BALANCEO {FLT_1, FLT_2, ... ,FLT_n}
        paramsBalancer = paramsOrchestrator["paramsBalancer"][0]    # PARAMETROS DEL BALANCEO [paramsFLT_1]
        readTimeSum = 0
        if (balanceType == "TEMPORAL"):
            # cargamos los cubes
            sourcesDF = list()                                                       # LISTADO DE DATAFRAMES
            try:
                # -------- LECTURA FILTRO
                sourcesFiles = mtd.getItems(itemName="nameFile",cubes=cubes)                        # OBTENEMOS LOS NOMBRES DE LOS ARCHIVOS DE LAS FUENETES DE DATOS
                for posSource,source in enumerate(sourcesFiles):
                    startReadTime = time.time()                                                     # INICIO DEL TIEMPO DE LECTURA
                    if(nodeManager.getID()=="-"):                                                   # VERIFICA SI EXISTE UN NODO MANAGER
                        # df = pd.read_csv('.{}/{}'.format(sourcePath,source))
                        df = dd.read_csv('.{}/{}'.format(sourcePath,source))
                    else:                                                                           # SI EXISTE CONCATENA EL NODE ID DEL MANAGER
                        # df = pd.read_csv('.{}/{}/{}'.format(sourcePath,nodeManager.getID(),source))
                        df = dd.read_csv('.{}/{}/{}'.format(sourcePath,nodeManager.getID(),source))
                    endReadTime = time.time()                                                       # FIN DEL TIEMPO DE LECTURA
                    readTimeFile = (endReadTime - startReadTime)
                    readTimeSum = readTimeSum + readTimeFile
                # -------- LECTURA FILTRO
                
                # -------- PROCESO AGRUPADO
                    startGruopTime = time.time()                                                    # INICIO DEL TIEMPO DE AGRUPADO
                    df = df.groupby(variablesToBalance[posSource])                                  # AGRUPAMIENTO DE LOS VALORES
                    sourcesDF.append(df)                                                            # GUARDAMOS EN MEMORIA LOS DATAFRAMES
                    endGroupTime = time.time()                                                      # FIN DEL TIEMPO DE AGRUPADO
                    processTimeSum = processTimeSum + (endGroupTime - startGruopTime)               # SUMA DEL TIEMPO DE AGRUPADO
                # -------- LECTURA FILTRO
            except Exception as e:
                            message = "ERROR READ_FILTERING_ENDPOINT {} {}".format(nodeId,e)
                            loggerErrorSet(message)
                            return jsonify({"response":message}), 501
        else:
            e="NOT ESPATIAL"
            message = "ERROR READ_ENDPOINT {} {}".format(nodeId,e)
            loggerErrorSet(message)
            return jsonify({"response":message}), 501
        # -------- LECTURA
        
        endReadTime = time.time()                               # FIN DE LETURA
        readTime = endReadTime - arrivalTime                    # TIEMPO DE LECTURA
        readTimeSum = readTimeSum + readTime
    except Exception as e:
        message = "ERROR READ_PARAMAS_ENDPOINT {} {}".format(nodeId,e)
        loggerErrorSet(message)
        return jsonify({"response":message}), 501
    

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
        loggerErrorFlag(requestJson['cubes'].keys())
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
    app.run(host= '0.0.0.0',port=state['dockerPort'],debug=False,use_reloader=False)