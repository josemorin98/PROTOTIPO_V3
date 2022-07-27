from datetime import datetime
import pandas as pd
import time
import random
import numpy as np
from sklearn.cluster import KMeans
import geopandas as gpd
import matplotlib.pyplot as plt
import geopandas


def K_means(k,data):
    # X_clima = data_clima.iloc[:,[7,8,9,10]]
    try:
        kmeans = KMeans(n_clusters=k).fit(data)
        labels = kmeans.predict(data)
        return labels
    except Exception:
        print("CLUSETRING_FAILED KMEANS")
        return np.zeros(data.shape[0])


def conteo(nameSource,conteoData,conteoVariables,grupoBY,group_by):
    arrivalTime = time.time()
    try:
        # loggerError.error("------------------------------ FLAG 2.1")
        DF_data = conteoData
        columns = DF_data.columns
        # variables para el conteo
        variables = list(conteoVariables)
        # varaible a agrupar / clave entidad
        group_columns = grupoBY
        query_str = "CVE_ENT"
        # --------------------------------
        columns= set(columns) - set(variables) #remove columns that are going to be group
        columns= set(columns) - set(group_columns) 
        applied_dict=dict()
        # loggerError.error("------------------------------ FLAG 2.2 {}".format(columns))
        for x in columns:
            applied_dict[x]="first"
        for x in variables:
            applied_dict[x]=group_by

        #print(DF_data)
        if (group_by == "count"):
            DF_data=DF_data[group_columns]
            DF_data['count'] = 0
            DF_data = DF_data.groupby(group_columns,as_index=False)['count'].count()
        else:
            DF_data = DF_data.groupby(group_columns,as_index=False).agg(applied_dict)
        # ==============================================================
        if query_str != "":
            try:
                DF_data = DF_data.query(query_str)
            except Exception as e:
                print(e)

        nameFile = "./{}_COUNT.csv".format(nameSource)
        
        DF_data.to_csv(nameFile,index=False)
        endTime = time.time()
        counttime = endTime-arrivalTime
        print("---------------------------- Select {}".format(counttime))
        return 1
    except Exception as e:
        print(e)
        return 0
    

def fusion(sourcesDF):
    for posSource,source in enumerate(sourcesDF):
        print("---------------  {}  --------------------------------------".format(source[1]))
        df = source[0]
        if (posSource != 0):
            column_left = source[2]
            typeFusion = source[3]
            if (typeFusion == "variable"):
                df_aux = df_aux.merge(df, how="inner", 
                        left_on=column_left,
                        right_on=column_right)	
            elif(typeFusion == "rows"):
                df_aux = pd.concat([df_aux,df], ignore_index=True, sort=False)
        else:
            df_aux = df.copy()
            column_right = source[2]
            print(source[1])

    nameFile = "fusion_{}".format("aa")
    directoryFile = "./results/{}.csv".format(nameFile)
    df_aux.to_csv("{}".format(directoryFile), index=False)


def initWorkresArray(workers):
    pet_in = []
    for i in range(workers):
        pet_in.append([])
    return pet_in


def toBalanceDataTC_Temporal(initWorkers,balanceData,sources):
    balancedData = TwoChoicesV4_temporal(cargas=initWorkers, traza=balanceData, sources=sources)
                            # (cargas=arrayWorkers, traza=list(toBalanceData), sources=sources,sourcePath=sourcePath, varSpatial=varSpatial)
    return balancedData

def TwoChoicesV4_temporal(cargas, traza, sources):
    #varSpatial es arreglo
    try:
        workers = len(cargas)
        cantWorkers = np.zeros(workers)
        select_bin = 0
        select_bin2 = 0
        aux = True
        # si es un workers
        if(workers==1):
            # for x in range(len(traza.iloc[:,0])):
            #     cargas[0].append(traza[0][x])
            return sources
        else:
            # for x in range(len(traza.iloc[:,0])):
            for posTraza, xTraza in enumerate(traza):
                # se selecciona el primer trabajador aleatorio
                select_bin = random.randint(0, workers-1)
                while(aux):
                    # se selecciona el segundo trabajador
                    select_bin2 = random.randint(0, workers-1)
                    # si es diferente rompe el ciclo
                    if(select_bin != select_bin2):
                        aux = False
                # revisamos la cantidad de registros con esa clase para cada fuente
                cantRows=0
                # print("{} - {}".format(select_bin, select_bin2))
                for pos,src in enumerate(sources[posTraza]):
                    # cantidad de registros
                    cantRows = cantRows + len(src[0].index)
                
                if( cantWorkers[select_bin] < cantWorkers[select_bin2]):
                    cargas[select_bin].append(sources[posTraza])
                    cantWorkers[select_bin] = cantWorkers[select_bin]+cantRows
                else:
                    cargas[select_bin2].append(sources[posTraza])
                    cantWorkers[select_bin2] = cantWorkers[select_bin2]+cantRows
                aux = True
        return cargas
    except Exception as e:
        return e

def str_date(date):
    return date.strftime("%Y-%m-%d %H:%M:%S")


def getStartEndTime(posRange, ranges, startTime):
    if (posRange==0):                                                       # SI ES LA PRIEMRA POSICION NOS RETRASAMOS UN RANGO
        start = datetime.strptime(startTime, '%Y-%m-%d %H:%M:%S')           # INICIO DE FECHA ENTRANTE
        start = start.strftime('%Y-%m-%d %H:%M:%S')
        end = ranges[(posRange)].strftime('%Y-%m-%d %H:%M:%S')              # TOMAMOS EL RANGO ACTUAL
        conditional = False
    else:
        start = ranges[(posRange-1)].strftime('%Y-%m-%d %H:%M:%S')                      # SALVAMOS LA FECHA ANTERIOR
        end = ranges[(posRange)].strftime('%Y-%m-%d %H:%M:%S')                          # TOMAMOS EL RANGO ACTUAL
        conditional = True
    return start, end, conditional

def generateRangos(inicio, fin, tipo, n):
    inicio =  datetime.strptime(inicio,"%Y-%m-%d %H:%M:%S")  # fecha de inicio (datetime)
    fin = datetime.strptime(fin, "%Y-%m-%d %H:%M:%S") # fecha de fin (datetime)
    rangos = list()
    # division por anos
    if(tipo=='Y'):
        rangos = pd.date_range(start=str_date(inicio), end=str_date(fin), freq=str(n)+'Y', closed='left').to_pydatetime()
    # division por meses
    elif(tipo=='M'):
        rangos = pd.date_range(start=str_date(inicio), end=str_date(fin), freq=str(n)+'M', closed='left').to_pydatetime()
    # division por dias
    elif(tipo=='D'):
        rangos = pd.date_range(start=str_date(inicio), end=str_date(fin), freq=str(n)+'D', closed='left').to_pydatetime()
    return rangos  
  
def mapingMX(df,name,columnColor,k):
    mexicoDF = gpd.read_file("./states/Mexico_Estados.shp")
    mexicoDF["ESTADO"]=mexicoDF["ESTADO"].replace("Distrito Federal","Ciudad de Mexico")
    columnPolygon="ESTADO"
    fig, ax = plt.subplots(figsize=(7,5))
    ax.set_aspect('equal')

    ploting = mexicoDF.plot(ax=ax, color="white",edgecolor="black",linewidth=1.5)


    gdf = geopandas.GeoDataFrame(
        df, geometry=geopandas.points_from_xy(df.longitud, df.latitud))

    ploting = gdf.plot(ax=ploting,column=columnColor,
                       categorical=True,
                       markersize=8,
                        marker='*',
                        legend=True,
                        legend_kwds={'loc': 'center left',
                                     'bbox_to_anchor':(1,0.5)})
    
    # nombre del archivo
    # ploting.set_axis_off()
    nameFile = "./results/{}_{}.png".format(name,columnColor)
    # colocamos el titulo del pngs
    ploting.set_title('{}\n{}'.format("Clustering",columnColor))
    ploting.figure.savefig(nameFile)
    plt.cla()
    plt.clf()
    plt.close()