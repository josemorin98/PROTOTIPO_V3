import pandas as pd
import json
from sklearn.preprocessing import MinMaxScaler
import time
import matplotlib.pyplot as plt
import seaborn as sns
import os

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
    scaled_df = scaler.fit_transform(p)
    scaled_df = pd.DataFrame(scaled_df, columns=vars)
    return scaled_df


def trueOrFalse(val):
    trueList = ["True","true","1","TRUE","t","T",1]
    if (val in trueList):
        return True
    else: 
        return False


def getMaxTuplesCorrs(df, n=5):
    au_corr = df.corr().unstack()
    pairsDelete = deleteDuplcatePairs(df)
    au_corr = au_corr.drop(labels=pairsDelete).sort_values(ascending=False)
    return list(au_corr.index[0:n])

def deleteDuplcatePairs(df):
    pairsDelete = set()                             # CONJUNTO DE PARES A ELIMINAR
    cols = df.columns
    for i in range(0, df.shape[1]):                 # SE RECORRE LA MATRIX (COLS)
        for j in range(0, i+1):                     # SE RECORRE LA MATRIX (ROWS)
            pairsDelete.add((cols[i], cols[j]))     # SE AÑADE LA DIAGONAL Y LA PARTE INFERIOR
    del df                                          # ELIMINAMOS DE MEMORIA EL DF
    return pairsDelete


def correlationPlot(corr,sourcePath,algorithm,nameSource,nodeId):
    try:
        sourcePathFig = ".{}/{}/{}".format(sourcePath, nodeId, algorithm)
        if (not os.path.exists(sourcePathFig)) :
            os.mkdir(sourcePathFig)
        nameFile = "{}/{}_CORR_{}.eps".format(sourcePathFig,nameSource, algorithm)
        plt.figure()
        f, ax = plt.subplots(figsize=(15, 9))
        ax = sns.heatmap(corr, linewidths=.5, vmin=-1, vmax=1, annot=True,cbar_kws={'label': 'CORRELATION {}'.format(algorithm)})
        plt.title('CORRELATION {}\n {}'.format(algorithm, nameSource))
        plt.savefig(nameFile,format="eps",dpi=400)
        plt.cla()
        plt.clf()
        plt.close()
        del ax
        del f
        return "CORRELATION-{} {} FIGURE SAVE  - OK".format(algorithm, nameSource)
    except Exception as e:
        return e