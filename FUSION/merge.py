import json
import pandas as pd
from flask import Flask, request
from flask import jsonify

app = Flask(__name__)
app.debug = True
app.config['PROPAGATE_EXCEPTIONS'] = True

dockerPort = 5000
sourcePath = "/home/usuario/Escritorio/PROTOTIPO_V3/FUSION/"

@app.route('/analytics/fusion', methods = ['POST'])
def fusion():
    # nodes = nodeLocal.getNodes()                                # GUARDAMOS LA INFO DE LOS NODOS TRABAJADORES
    # numberEvent = nodeLocal.getNumberEvents()                   # CANTIDAD DE EVENTOS GENERADOS AL MOMENTO
    requestJson = request.get_json()                              # RECIBIR LOS PARAMETROS
    startRequestTime = requestJson["startRequestTime"]            # TIEMPO DE INICIO DE SOLICITUD (startRequestTime)
    cubes = requestJson["cubes"]                                  # CUBOS DE ENTRADA   
    for posSource,source in enumerate(cubes.keys()):
        
        df = pd.read_csv("{}{}".format(sourcePath,cubes[source]['nameFile']))
        if (posSource != 0):
			#left = column in df_aux
			#rigt = column in df
            column_right = cubes[source]['Tranformation']['Fusion']['columnFusion']
            df_aux = df_aux.merge(df, how="inner", 
						left_on=[source_aux['Tranformation']['Fusion']['columnFusion']],
						right_on=[column_right])	
        else:
            df_aux = df.copy()
            source_aux = cubes[source]
            print(source_aux)
            
    df_aux.to_csv("./fusion.csv", index=False)
    return "OK"
        

if __name__ == '__main__':
    app.run(host= '0.0.0.0',port=dockerPort)