import pandas as pd
import json
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import matplotlib.pyplot as plt
import numpy as np
import os

# Le columna de un json y la convierte en array
def readJson(nameFile, column):
    f = open(nameFile)
    # returns JSON object as
    # a dictionary
    data = json.load(f)
    # Iterating through the json
    # list
    listr = list()
    for i in data:
        listr.append(i[column])
    # Closing file
    f.close()
    return listr


def normalize(p, vars):
    scaler = MinMaxScaler()
    scaled_df = scaler.fit_transform(p)
    scaled_df = pd.DataFrame(scaled_df, columns=vars)
    return scaled_df


def trueOrFalse(val):
    trueList = ["True","true","1","TRUE","t","T",1]
    if (val in trueList):
        return True
    else: 
        return False

def regressionLineal(X, y):
    try: 
        reg = LinearRegression()
        reg.fit(X=X, y=y)
        predicts = reg.predict(X)
        R2 = r2_score(y, predicts)
        return predicts, R2
    except Exception as e:
        raise e
        return e,0
    
def plotRegression(X,y,xLabel,yLabel,predicts,sourcePath,nodeId,nameSource, namePlot, r2):
    try:
        sourcePathFig = ".{}/{}/{}".format(sourcePath, nodeId, "Plots")
        if (not os.path.exists(sourcePathFig)) :
            os.mkdir(sourcePathFig)
            
        nameFile = "{}/{}_REG_LINEAL.eps".format(sourcePathFig,nameSource)
        fig = plt.figure()
        ax = fig.add_subplot()
        plt.scatter(X, y, color="blue")
        plt.plot(X, predicts, color ="red", linewidth=3)
        ax.text(np.max(X), np.max(y), "R2={}".format(round(r2,2)), fontsize=8)
        plt.title("{}".format(nameSource))
        plt.ylabel(yLabel)
        plt.xlabel(xLabel)
        plt.savefig(nameFile, format="eps", dpi=400)
        plt.cla()
        plt.clf()
        plt.close()
        del fig, ax
        return predicts
    except Exception as e:
        raise e
        return e