from matplotlib import pyplot as plt
import pandas as pd
import seaborn as sns
import os

def corr(corr,nameSource,xlabel,ylabel,fol):
    f, ax = plt.subplots(figsize=(15, 9))
    ax = sns.heatmap(corr, linewidths=.5, vmin=-1, vmax=1, cbar_kws={'label': 'CORRELATION'}, fmt=".2f",)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title('CORRELACION \n {}'.format(nameSource))
    plt.tight_layout()
    plt.savefig("./{}/{}".format(fol,nameSource),format="png",dpi=400)
    plt.cla()
    plt.close()
    
    
df1 = pd.read_csv("/home/usuario/Descargas/BD_INP/Suicidios/Suic_Medio_Derhab_tasasporsexo.csv")
ecnomi = pd.read_csv("/home/usuario/Descargas/BD_INP/Macroeconomicas/Macroeconomicas 2000_2020.csv")
df1 = df1.fillna(0)
columnsSuic = list(df1.columns)

# print(columnsSuic)

columnsSuciCorr = ['suicAhogamiento', 'suicAhorcamiento', 'suicArma_fuego', 'suicEnvenenamiento', 'suicOtro', 
                   'suicderhabNE', 'suicSinDerhab', 'suicDerehab', 'suic10_14', 'suic15_19', 'suic20_24', 'suic25_29', 
                   'suic30_34', 'suic35_39', 'suic40_44', 'suic45_49', 'suic50_54', 'suic55_59', 'suic5_9', 
                   'suic60_64', 'suicNE_NA', 'pob_00_04', 'pob_05_09', 'pob_10_14', 'pob_15_19', 'pob_20_24', 
                   'pob_25_29', 'pob_30_34', 'pob_35_39', 'pob_40_44', 'pob_45_49', 'pob_50_54', 'pob_55_59', 
                   'pob_60_64', 'pob_65_mm', 'tasa_suic5_9', 'tasa_suic10_14', 'tasa_suic15_19', 
                   'tasa_suic20_24', 'tasa_suic25_29', 'tasa_suic30_34', 'tasa_suic35_39', 'tasa_suic40_44', 
                   'tasa_suic45_49', 'tasa_suic50_54', 'tasa_suic55_59', 'tasa_suic60_64', 'suic65_mas', 'tasa_suic65_mas',
                   'tot_pob', 'total_suic', 'tasa_suic']


anios = [2000,2005,2010,2015,2020]
folders = ["Suic2"]
for x in range(len(anios)):
    print("-- {}".format(anios[x]))
    fol = folders[0]
    if (not os.path.exists("./{}".format(fol))):
        os.mkdir("./{}".format(fol))
        
    ecnomi_aux = ecnomi[ecnomi["anio"]==anios[x]]
    if (x ==0):
        df1_aux = df1[df1["anio"]<=anios[x]]
    else:
        df1_aux = df1[df1["anio"]>anios[x-1]] 
        df1_aux = df1[df1["anio"]<=anios[x]]
        
    result = df1_aux.merge(ecnomi_aux, how="inner", left_on=["cve_ent_mun"], right_on=["cve_ent_mun"])
    result.to_csv("merge_{}.csv".format(anios[x]), index=False)
    
    print("------ {}".format(df1_aux.shape))
    print("------ {}".format(ecnomi_aux.shape))
    print("------ {}".format(result.shape))
    resultColumns = set(result.columns)
    # print(len(resultColumns))
    countL = 0
    result = result.dropna(1)
    corrs = result.corr()
    corrs = corrs[columnsSuciCorr]
    corrs = corrs.drop(columnsSuciCorr, axis=0)
    
    corrs.to_csv("./{}/fusion_{}.csv".format(fol,anios[x]))
    corr(corrs,"Suic_{}".format(anios[x]),"Variables Suicidios", "Variables Macroeconomicas",fol)


