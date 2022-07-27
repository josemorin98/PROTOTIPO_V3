from datetime import datetime
import pandas as pd
import time
import numpy as np
import methods as mtd

def dateString(date):
    date = date.split(' ')[0]
    return date

sources = ["historico_EMAS-MERRA.csv_1.csv","meteorological_data.csv"]

columns = [["year"],["year"]]
nameFile = './{}'.format(sources[0])

print("---- LECTURA")
startReadTime = time.time()
sourcesDF = list()
for pos,cvs in enumerate(sources):
    print("--------------------- {}".format(cvs))
    df = pd.read_csv("./{}".format(cvs))
    df = df.round(3)
    if(pos ==1):
        df["fecha"] = pd.to_datetime(df["fecha"])
        df["year"] = pd.DatetimeIndex(df['fecha']).year
        df["year"] = df['year'].astype(int)
        print(df.head(5))
    sourcesDF.append([df,cvs,columns[pos],"rows"])
endReadTime = time.time()
totalReadTime = endReadTime - startReadTime
print("---- FIN LECTURA")


# print(" ---- RANGOS")
# processTimeSum=0
# startRangeTime = time.time()
# startTime = "2001-01-01 00:00:00"
# endTime = "2020-12-31 00:00:00"
# typeDate = "Y"
# nRange = 1
# ranges = mtd.generateRangos(inicio=startTime,
#                                             fin=endTime,
#                                             tipo=typeDate,
#                                             n=nRange)
# fin = datetime.strptime(endTime, "%Y-%m-%d %H:%M:%S")   # FECHA DE FIN (DATETIME)
# ranges = np.append(ranges,fin)
                
# endRangeTime = time.time()
# processTimeSum = processTimeSum + (endRangeTime - startRangeTime)

# print(" ---- FIN RANGOS")


# print(" ---- FILTRO")
# startFilteringTime = time.time()                                            # TIEMPO DE INICIO DEL RANGOS
# dfByDates = list()
                
# for posRange, valRange in enumerate(ranges):
#     dfByDateAux = list()
                    
#     for posDf, df in enumerate(sourcesDF):
                        
#         cubeName = df[1]
#         variableToBalance = df[2][0]
#         print(variableToBalance)  
#         start, end, conditional = mtd.getStartEndTime(posRange=posRange, 
#                                                                 ranges=ranges,
#                                                                 startTime=startTime)
                        
#         if(variableToBalance == "NO_TEMPORAL"):
#             df_aux = df.copy()
#             dfByDateAux.append([df_aux, cubeName, start, end])                              # GUARDAMOS LOS VALORES DEL TOTAL DEL REGISTRO
#             break
#         else:     
#             formatDate = "%Y"
#             df[0][variableToBalance] = pd.to_datetime(df[0][variableToBalance],                   # CONVERTIRMOS LA COLUMNA EN DATETIME FORMAT 
#                                                          format=formatDate)    
                        
#         if (conditional==False):                                                            # SI ES LA PRIEMRA POSICION NOS RETRASAMOS UN RANGO
#             mask = (df[0][variableToBalance] >= start) & (df[0][variableToBalance] <= end)         # CACHAMOS LAS FECHAS DENTRO DE LOS RANGOS SELECCIONADOS
                            
#         else:                                                                   
#             mask = (df[0][variableToBalance] > start) & (df[0][variableToBalance] <= end)         # CACHAMOS LAS FECHAS DENTRO DE LOS RANGOS SELECCIONADOS
                        
#         df_aux = df[0].loc[mask]                                                               # APARTAMOS LOS VALORES DEL TOTAL DEL REGISTRO
#         print(" ------ {} - {} - {}".format((start),(end), len(df_aux.index)))
#         dfByDateAux.append([df_aux, cubeName, start, end])                                  # GUARDAMOS LOS VALORES DEL TOTAL DEL REGISTRO
#         del df_aux        
#     del df
#     dfByDates.append(dfByDateAux)
# del sourcesDF
# del dfByDateAux
# endFilteringTime = time.time()
# processTimeSum = processTimeSum + (endFilteringTime - startFilteringTime)


# print(" ---- FIN FILTRO")
# print(" ---- BALNCEO")
# startBalancer = time.time()
# workersCant = 15
# initBoxWorkers = mtd.initWorkresArray(workersCant)  # CREAMOS LAS CAJAS VACIAS DE LOS TRABAJADOR PARA EL BALANEO DE CARGA
# algorithmBalancer="TC"
# if (algorithmBalancer=="TC"):
#     balanceData = mtd.toBalanceDataTC_Temporal(initWorkers=initBoxWorkers,  # CAJAS VACIAS PARA LAS FUENTES
#                                                 balanceData=ranges,                         # ALGORITMO DE BALANCEO
#                                                 sources=dfByDates)                          # NOMBRE DE LOS ARCHIVOS DE CADA FUENTE
# else:
#     balanceData = mtd.toBalanceData(initWorkers=initBoxWorkers,             # CAJAS VACIAS PARA LAS FUENTES
#                                                 balanceData=ranges,                         # NOMBRE DE LOS ARCHIVOS DE CADA FUENTE
#                                                 algorithm=algorithmBalancer)                # ALGORITHM DE BALANCEO
                
# endBalancer = time.time()                                                   # TIEMPO DE TERMINO DEL BALANCEO
# balancerTime = endBalancer - startBalancer                                  # TIEMPO TOTAL DEL BALANCEO
# processTimeSum = processTimeSum + balancerTime
# print(" ---- FIN BALANCEO")
# print(" ---- FRAGMENTACION")
# omunicationTimeSum = 0
# balanceDataSave = list() 
# print("{} == {} ".format(len(balanceData),len(initBoxWorkers)))
# for posWorker,dataWorker in enumerate(balanceData):                     # POSICIONES POR TRABAJADOR
#     print("-------- Worker {}".format(posWorker))
#     auxBalanceData = list()
#     for dataBalanceo in dataWorker:                                     # POSICIONES POR BALANCEO
#         print(" ----------- {}".format(type(dataBalanceo)))
#         cubesNew = {}                                                   # JSON VACIO PARA LOS CUBOS MODIFICADOS
#         for posData,data in enumerate(dataBalanceo):                                       # POSICIONES POR CUBO DE DATOS (FUENTES)
#             rowByTemporal = data[0]                                     # REGISTROS DEL RANGO
#             cubeName = data[1]                                          # OBTENMOS EL NOMBRE DEL CUBO                     
#             startFilterTime = data[2]                                   # RANGO DE INICIO
#             endFilterTime = data[3]                                     # RANGO DE FIN
#             auxBalanceData.append([startFilterTime, endFilterTime])
#             nameFile = "{}_{}_{}".format(cubeName,
#                                         dateString(startFilterTime),    # NOMBRE DEL ARCHIVO FRGAMENTADO POR UN TEMPORAL
#                                         dateString(endFilterTime))   
#                                                              # GENERAMOS UNA COPIA DEL CUBO PARA TRABAJAR SOBRE ELLA
#             print(cubesNew.keys())
#             directoryFile = "./results/{}.csv".format(nameFile)     # CREAMOSS EL DIRECTORIO DEL NODO LOCAL
#             rowByTemporal.to_csv(directoryFile, index = False)                 # GUARDAMOS EL ARCHIVO CSV

#     balanceDataSave.append(auxBalanceData)                                                              
                                
# endFilteringTime = time.time()                        
# filteringTime = (endFilteringTime - startFilteringTime)
# processTimeSum = processTimeSum + filteringTime
# print(" ---- FIN FRAGMENTACION -> {}".format(processTimeSum))

print("\n---- FUSION")
startFusionTime = time.time()
mtd.fusion(sourcesDF)
endFusionTime = time.time()
totalFusionTime = endFusionTime - startFusionTime
total = totalFusionTime + totalReadTime
print("---- FIN FUSION -> {}".format((total)))


print("\n---- CLUTERING")
startClusteringTime = time.time()
kvals=[9,10,11,12]
for x in sourcesDF:
    df = x[0]
    columnsList = df.select_dtypes(include=np.number).columns.tolist()[:-1]
    print(columnsList)
    for k in kvals:
        labels = mtd.K_means(k=int(k), data=df[columnsList])
        df["K{}".format(k)] = labels
    df.to_csv("./results/{}".format(x[1]), index=False)   
endClusteringTime = time.time()
totalClusteringTime = endClusteringTime - startClusteringTime
print("---- Fin CLUTERING -> {}".format(totalClusteringTime+totalReadTime))



column_tem = ["MAX MERRA","temperatura"]
print("\n---- PLOT MAP")
startMapTime = time.time()
for pos,x in enumerate(sourcesDF):
    df = x[0]
    for k in kvals:
        mtd.mapingMX(df=df,name=x[1],columnColor="K{}".format(k),k=k)
endMapTime = time.time()
totalMap = endMapTime - startMapTime
print("---- FIN PLOT MAP -> {}".format(totalMap+totalReadTime))