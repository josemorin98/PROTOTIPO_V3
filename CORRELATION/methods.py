import pandas as pd
import json
from sklearn.preprocessing import MinMaxScaler
import time
import matplotlib.pyplot as plt
import seaborn as sns

# lista de estados
stateList = list()

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
    scaled_df = scaler.fit_transform(p[vars])
    scaled_df = pd.DataFrame(scaled_df, columns=vars)
    return scaled_df


def trueOrFalse(val):
    trueList = ["True","true","1","TRUE","t","T",1]
    if (val in trueList):
        return True
    else: 
        return False

def correlationPlot(corr,sourcePath,nameSource,nodeId):
    try:
        nameFile = ".{}/{}/{}_CORR.png".format(sourcePath, nodeId, nameSource)
        f, ax = plt.subplots(figsize=(15, 9))
        ax = sns.heatmap(corr, linewidths=.5, vmin=-1, vmax=1, cbar_kws={'label': 'CORRELATION'})
        plt.title('CORRELATION \n {}'.format(nameSource))
        plt.savefig(nameFile)
        plt.cla()
        plt.close()
        return "OK"
    except Exception as e:
        return e