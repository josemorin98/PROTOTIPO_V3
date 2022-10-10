from cProfile import label
from matplotlib import pyplot as plt
import pandas as pd
import seaborn as sns
import os
import  algo_clustering as clus
from sklearn import metrics
import numpy as np


# seedFolder = "/home/moringas/Descargas/BD_INP/"   # Cinvestav
seedFolder = "/home/usuario/Descargas/BD_INP/"     # Lenovo

################################################################################

# LECTURA


suicidios = pd.read_csv("{}Suicidios/Suic_Medio_Derhab_tasasporsexo.csv".format(seedFolder))
macro = pd.read_csv("{}/Macroeconomicas/Macroeconomicas 2000_2020.csv".format(seedFolder))
suicidios = suicidios.fillna(0)

################################################################################



################################################################################

# COLUMNAS SUICIDIOS

columnsSuciCorr = ['suicAhogamiento', 'suicAhorcamiento', 'suicArma_fuego', 'suicEnvenenamiento', 'suicOtro', 
                   'suicderhabNE', 'suicSinDerhab', 'suicDerehab', 'suic10_14', 'suic15_19', 'suic20_24', 
                   'suic25_29', 'suic30_34', 'suic35_39', 'suic40_44', 'suic45_49', 'suic50_54', 'suic55_59', 
                   'suic5_9', 'suic60_64','suic65_mas', 'suicNE_NA', 'total_suic', 'prop_pob',
                    'p_12ymas','psinder','pcon_limi','psind_lim','graproes','pea','pe_inac','pocupada','prom_ocup',
                    'pro_ocup_c', 'tothog','hogjef_m','hogjef_f','rel_h_m','prom_hnv','graproes_m','graproes_f',
                    'p_12ymas_m','p_12ymas_f','pea_m','pea_f','pe_inac_m','pe_inac_f','pocupada_m','pocupada_f',
                    'pdesocup','pdesocup_m','pdesocup_f','propsinss','propea','propea_H','propea_M','propdesoc',
                    'propdesoc_H','propdesoc_M','propocup','propocup_H','propocup_M','propslim','proconlim',
                    'prop_M','prop_H','prop_hojef_M','prop_hojef_H','prop_pe_inac','prop_pein_M','prop_pein_H',
                   ]

columnsSuciCorrNO = ['tasa_suic5_9', 'tasa_suic10_14', 'tasa_suic15_19', 
                'tasa_suic20_24', 'tasa_suic25_29', 'tasa_suic30_34', 
                'tasa_suic35_39', 'tasa_suic40_44', 'tasa_suic45_49', 
                'tasa_suic50_54', 'tasa_suic55_59', 'tasa_suic60_64', 
                'tasa_suic65_mas', 'tot_pob', 'tasa_suic',]
################################################################################




################################################################################

# FUSION

anios = [2000,2005,2010,2015,2020]
seedFolder = ["Suicidios_Macroeconomia"]

for seed in seedFolder:
    for index, anio in enumerate(anios):
        print("---- {} - {}".format(seed,anio))
        seedCSV = "./{}/CSV".format(seed) 
        seedCorr = "./{}/CORR".format(seed)
        if (not os.path.exists("./{}".format(seed))):
            os.mkdir("./{}".format(seed))
            # folder para guardar fusiones
            # seedCSV = "./{}/CSV".format(seed) 
            os.mkdir(seedCSV)
            # folder para guardar csv de corrleaciones e imagenes
            # seedCorr = "./{}/CORR".format(seed)
            os.mkdir(seedCorr)
        
        # macroeconomias por quinquenio
        macro_anio = macro[macro["anio"]==anio]
        
        # suicidios por quinquenio
        if (index==0):
            suic_kinke = suicidios[suicidios["anio"]<=anios[index]]
        else:
            suic_kinke = suicidios[suicidios["anio"]>anios[index-1]]
            suic_kinke = suic_kinke[suic_kinke["anio"]<=anio]
        
        # fusion
        result = suic_kinke.merge(macro_anio, 
                                  how="inner", 
                                  left_on=["cve_ent_mun"], 
                                  right_on=["cve_ent_mun"])
        
        
        result.to_csv("{}/fusion_{}.csv".format(seedCSV,anio))
        
################################################################################

################################################################################

# CORELACIONES
        

################################################################################

        # pearson
        # result = result.dropna(axis=1)
        
        
        columnsY = set(macro.select_dtypes(include=np.number).columns) - set(['cve_ent', 'cve_mun', 'anio'])
        columnsY = list(columnsY)
        corrs = clus.corr(result=result,
                        columnsX=columnsSuciCorr,
                        columnsY=columnsY,
                        columnsNo=columnsSuciCorrNO,
                        fol=seedCorr,
                        anio=anio,
                        algo="pearson")
        clus.corr_plot(corrs,
                       "correlation_{}".format(anio,"pearson"),
                       "Variables Suicidios", 
                       "Variables Macroeconomicas",
                       seedCorr,
                       anio,
                       algo="pearson")


