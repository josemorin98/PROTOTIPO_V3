
# Librerias
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
import matplotlib.pyplot as plt
import os
import geopandas as gpd
import geopandas


def read_CSV(name):
    return pd.read_csv(name)


def trueOrFalse(val):
    trueList = ['True','true','1','TRUE','t','T',1]
    if (val in trueList):
        return True
    else: 
        return False
        
# Clustering-------------------------
def K_means(k,data,nameSource):
    # X_clima = data_clima.iloc[:,[7,8,9,10]]
    try:
        kmeans = KMeans(n_clusters=k).fit(data)
        labels = kmeans.predict(data)
        return labels
    except Exception:
        return np.zeros(data.shape[0])

def plotingSilhouete(scoreSil,algo,sourcePath):
    try:
        
        scoreSil.sort(key=lambda x: x[1], reverse=True) # sort 

        cluster = list(zip(*scoreSil))[0] # labels
        score = list(zip(*scoreSil))[1] #scores
        # timesSil = list(zip(*scoreSil))[2]
        # mediaTimesSil = np.mean(timesSil)
        x_pos = np.arange(len(cluster)) #positions

        plt.bar(x_pos, score, align='center', )


        plt.xticks(x_pos, cluster)
        for index,data in enumerate(score):
            scoreString = float("{:.2f}".format(data))
            plt.text(x=index , y =data , s=f"{scoreString}", fontdict=dict(fontsize=10))
        plt.ylabel('Silhouette Score')
        plt.title('Silhouette Scores {}'.format(algo))
        plt.xlabel('Clustering {}'.format(algo))

        nameSource = 'silhouette_score_{}.png'.format(algo)
        
        if (not os.path.exists("{}/Silhouette_Scores".format(sourcePath))):
                os.mkdir("{}/Silhouette_Scores".format(sourcePath))
        # pathSave = ".{}/{}.png".format(sourcePath,nameSource)
        pathSave = "./{}/Silhouette_Scores/{}".format(sourcePath,nameSource)
        plt.savefig(pathSave)
        plt.cla()
        return 'OK'
    except Exception as e:
        return "NO OK \n {}".format(e) 
    

def MixtureModel(k,data,nameSource):
    try:
        modelo_gmm = GaussianMixture(
                n_components    = k,
                covariance_type = 'full',
                random_state    = 123)
        modelo_gmm.fit(data)
        labels = modelo_gmm.predict(data)
        return labels
    except Exception:
        return np.zeros(data.shape[0])
    

def mapingMX(df,name,columnColor,k):
    mexicoDF = gpd.read_file("./states/Mexico_Estados.shp")
    mexicoDF["ESTADO"]=mexicoDF["ESTADO"].replace("Distrito Federal","Ciudad de Mexico")
    columnPolygon="ESTADO"
    fig, ax = plt.subplots(figsize=(7,5))
    ax.set_aspect('equal')

    ploting = mexicoDF.plot(ax=ax, color="white",edgecolor="black",linewidth=1.5)


    gdf = geopandas.GeoDataFrame(
        df, geometry=geopandas.points_from_xy(df.lon, df.lat))

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