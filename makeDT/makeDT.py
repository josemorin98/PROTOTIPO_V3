import numpy as np
import json
import pandas as pd
from scipy import stats
import string


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


def dateStates(cantRows=10000,numPeriods=20, freq="Y"):
    statesList = readJson("/home/usuario/Escritorio/PROTOTIPO_V3/makeDT/states.json","name")
    numdays = 20
    # base = datetime.datetime.today()
    # date_list = [base - datetime.timedelta(days=x) for x in range(numdays)]
    # dateList = 
    dateList = pd.date_range(start="2000-01-01", periods=numdays, freq=freq)
    dateList = dateList.strftime("%Y-%m-%d %H:%M:%S").tolist()
    dates = np.random.choice(dateList,cantRows)
    states = np.random.choice(statesList,cantRows)
    return dates,states

def generator_vals(mu=5,a=1,num=8000):
  # mu, sigma = 1, 0.5 # media y desvio estandar  
    x_norm_r = stats.norm.rvs(mu,size=num)  
    x_gama_r = stats.gamma.rvs(a,loc=0,size=num)
    x_chi_r = stats.chi.rvs(mu,size=num)
    return x_norm_r, x_gama_r, x_chi_r


def dataSet(cantRows=10000, numPeriods=20, freq="Y"):
      # dias  y estados
      dates, states = dateStates(cantRows, numPeriods)
      # json
      data={"state":states,
            "fecha":dates}
      # variables
      abc = string.ascii_uppercase
      # generate variables
      cont = 0
      for x in range(3):
            d1,d2,d3=generator_vals(num=cantRows)
            data[abc[cont]] = d1
            cont += 1
            data[abc[cont]] = d2
            cont += 1
            data[abc[cont]] = d3
            cont += 1
      # print(data.keys())
      dfResult = pd.DataFrame(data)
      return dfResult


# 10k
cants = [100000,100000,100000]
for pos,c in enumerate(cants):
    df = dataSet(cantRows=c,numPeriods=30, freq="Y")
    df.to_csv("df{}_{}k.csv".format(pos,c), index=False)

