from cProfile import label
from matplotlib import pyplot as plt
import pandas as pd
import seaborn as sns
import os
import  algo_clustering as clus
from sklearn import metrics
import numpy as np



def corr_plot(corr,nameSource,xlabel,ylabel,fol,algo="pearson"):
    if (not os.path.exists("./{}/{}".format(fol,algo))):
        os.mkdir("./{}/{}".format(fol,algo))
    
    f, ax = plt.subplots(figsize=(15, 9))
    ax = sns.heatmap(corr, linewidths=.5, vmin=-1, vmax=1, cbar_kws={'label': 'CORRELATION'}, fmt=".2f",)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title('CORRELACION \n {}'.format(nameSource))
    plt.tight_layout()
    plt.savefig("./{}/{}/{}".format(fol,algo,nameSource),format="png",dpi=400)
    plt.cla()
    plt.close()
    
def corr(result, columns, sex, algo="pearson"):
    print("----- {}".format(algo))
    corrs = result.corr(method=algo)
    corrs = corrs[columns]
    corrs = corrs.drop(columns, axis=0)
    corrs.to_csv("./{}/CORR/fusion_{}_{}_{}.csv".format(fol,anios[x],algo,sex))
    return corrs
    
    
seedFolder = "/home/moringas/Descargas/BD_INP/"
# seedFolder = "/home/usuario/Descargas/BD_INP/"

df1 = pd.read_csv("{}Suicidios/Suic_Medio_Derhab_tasasporsexo.csv".format(seedFolder))
ecnomi = pd.read_csv("{}/Macroeconomicas/Macroeconomicas 2000_2020.csv".format(seedFolder))
df1 = df1.fillna(0)
columnsSuic = list(df1.columns)

# print(columnsSuic)

columnsSuciCorr = ['suicAhogamiento', 'suicAhorcamiento', 'suicArma_fuego', 'suicEnvenenamiento', 'suicOtro', 
                   'suicderhabNE', 'suicSinDerhab', 'suicDerehab', 'suic10_14', 'suic15_19', 'suic20_24', 
                   'suic25_29', 'suic30_34', 'suic35_39', 'suic40_44', 'suic45_49', 'suic50_54', 'suic55_59', 
                   'suic5_9', 'suic60_64', 'suicNE_NA', 
                #    'tasa_suic5_9', 'tasa_suic10_14', 'tasa_suic15_19', 
                #    'tasa_suic20_24', 'tasa_suic25_29', 'tasa_suic30_34', 'tasa_suic35_39', 'tasa_suic40_44', 
                #    'tasa_suic45_4tres_car_soc_min,prop_ing_inf_lpob,ing_inf_lpob,prop_ing_inf_lpob_ext,ing_inf_lpob_ext', 'tasa_suic50_54', 'tasa_suic55_59', 'tasa_suic60_64', 
                   'suic65_mas', 
                #    'tasa_suic65_mas', 'tot_pob', 
                   'total_suic', 
                #    'tasa_suic',
                #    'prop_pob',
                    'p_12ymas','psinder','pcon_limi','psind_lim','graproes','pea','pe_inac','pocupada','prom_ocup',
                    'pro_ocup_c', 'tothog','hogjef_m','hogjef_f','rel_h_m','prom_hnv','graproes_m','graproes_f',
                    'p_12ymas_m','p_12ymas_f','pea_m','pea_f','pe_inac_m','pe_inac_f','pocupada_m','pocupada_f',
                    'pdesocup','pdesocup_m','pdesocup_f','propsinss','propea','propea_H','propea_M','propdesoc',
                    'propdesoc_H','propdesoc_M','propocup','propocup_H','propocup_M','propslim','proconlim',
                    'prop_M','prop_H','prop_hojef_M','prop_hojef_H','prop_pe_inac','prop_pein_M','prop_pein_H',
                   ]



anios = [2000,2005,2010,2015,2020]
folders = ["Suic2"]
for x in range(len(anios)):
    print("-- {}".format(anios[x]))
    fol = folders[0]
    if (not os.path.exists("./{}".format(fol))):
        os.mkdir("./{}".format(fol))
        os.mkdir("./{}/CSV".format(fol))
        os.mkdir("./{}/CORR".format(fol))
        
    ecnomi_aux = ecnomi[ecnomi["anio"]==anios[x]]
    
    if (x ==0):
        df1_aux = df1[df1["anio"]<=anios[x]]
    else:
        df1_aux = df1[df1["anio"]>anios[x-1]]
        df1_aux = df1_aux[df1_aux["anio"]<=anios[x]]
    
    result = df1_aux.merge(ecnomi_aux, how="inner", left_on=["cve_ent_mun"], right_on=["cve_ent_mun"])
    
    
    # print("------ {}".format(df1_aux.shape))
    # print("------ {}".format(ecnomi_aux.shape))
    # print("------ {}".format(result.shape))
    resultColumns = set(result.columns)
    
    # ----------------------------- Correlacion
    
    # result = result.dropna(axis=1)
    sexos = result["sexo"].unique()
    for sex in sexos:
        
        data_aux = result[result["sexo"]==sex]
        
        corrs = corr(result=data_aux,
                    columns=columnsSuciCorr,sex=sex)
        corr_plot(corrs,"Suic_{}_{}".format(sex,anios[x]),"Variables Suicidios", "Variables Macroeconomicas",fol)
        corrs_spearman = corr(result=data_aux,
                            algo="spearman",
                            columns=columnsSuciCorr,sex=sex)
        corr_plot(corrs,"Suic_{}_{}".format(sex,anios[x]),"Variables Suicidios", "Variables Macroeconomicas",fol,"spearman")
        corrs_spearman = corr(result=data_aux,
                            algo="kendall",
                            columns=columnsSuciCorr,sex=sex)
        corr_plot(corrs,"Suic_{}_{}".format(sex,anios[x]),"Variables Suicidios", "Variables Macroeconomicas",fol,"kendall")

    # ----------------------------- Clustering

    # print(result.columns)
    
    # Clustering
    algorithm = "MixtureModel"
    # df_numerics = result.select_dtypes(include=np.number)
    # colClus = df_numerics.columns
    # scoreSil = list()
    # sourceClusG = "./{}/{}".format(fol,algorithm)
    # if (not os.path.exists(sourceClusG)):
    #     os.mkdir(sourceClusG)
        
        
    # if (not os.path.exists("{}/{}".format(sourceClusG,anios[x]))):
    #     os.mkdir("{}/{}".format(sourceClusG,anios[x]))
    
    
    # sexos = result["sexo"].unique()
    # for sex in sexos:
        
    #     sourceClusG = "{}/{}".format(sourceClusG,sex.replace("/","_"))
    #     if (not os.path.exists(sourceClusG)):
    #             os.mkdir("{}".format(sourceClusG))
    #     if (not os.path.exists("{}/{}".format(sourceClusG,anios[x]))):
    #         os.mkdir("{}/{}".format(sourceClusG,anios[x]))
        
    #     data_aux = result[result["sexo"]==sex]
    #     dataClus = data_aux[colClus]
        
    #     for k in range(3,12):       
    #         sourceClus = "{}/{}/K{}".format(sourceClusG,anios[x],k)
    #         if (not os.path.exists(sourceClus)):
    #             os.mkdir("{}".format(sourceClus))
    #         # clustering
            
            
    #         # Kmeans
    #         # labels_cluus = clus.K_means(k=k,data=dataClus)
            
    #         # Gaussian Mixture
    #         labels_cluus = clus.MixtureModel(k=k,data=dataClus)
            
    #         columname="{}{}K{}".format(algorithm,sex.replace("/","_"),k)
            
    #         dataClus.insert(len(dataClus.columns),columname,labels_cluus)
    #         # dataClus[columname] = labels_cluus
            
    #         # mapa png
    #         clus.mapingMX(df=dataClus,
    #                     columnColor=columname,
    #                     sourcePath="{}".format(sourceClus))
            
    #         # silhouete score
            
    #         # sil = metrics.silhouette_score(dataClus, ls)
    #         # scoreSil.append(('K{}'.format(k),sil))
            
    #         # mapa html
    #         mapa_base = clus.mapa_html(dataClus,columname,k)
    #         mapa_base.save("{}/{}.html".format(sourceClus,columname))
            
    #         print("K{}".format(k))
    #         # print("K{} \t\t Sil={}".format(k,sil))
    #     sourceClusG = "./{}/{}".format(fol,algorithm)
        # Silhouete
        # print(clus.plotingSilhouete(scoreSil,
                            #    algorithm,
                            #    "{}".format(sourceClus)))
    result.to_csv("./{}/CSV/fusion_{}_{}.csv".format(fol,anios[x],algorithm), index=False)
        