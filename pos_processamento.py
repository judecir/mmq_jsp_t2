import json
import pandas as pd


def nome_arquivo_geral(nome_modelo, m, n, prefixo=""):    
        return prefixo+"_"+nome_modelo+"_"+"{:002}".format(n)+"jobs_"+"{:002}".format(m)+"maq"

def nome_arquivo_lp(nome_modelo, m, n, prefixo=""):    
        return "lps/"+nome_arquivo_geral(nome_modelo, m, n, prefixo)+".lp"

def nome_arquivo_log(nome_modelo, m, n, prefixo=""):    
    return "logs/"+nome_arquivo_geral(nome_modelo, m, n, prefixo)+".txt"

def nome_arquivo_sol(nome_modelo, m, n, prefixo=""):    
    return "valor_variaveis/"+nome_arquivo_geral(nome_modelo, m, n, prefixo)+".json"

def exportar_solucao(solucao, nome_modelo, m, n, prefixo=""):
    with open(nome_arquivo_sol(nome_modelo, m, n, prefixo=prefixo), 'w') as lout:
        solucao.export(lout)
        
def ler_solucao(nome_modelo, m, n):
    nome_arquivo = nome_arquivo_sol(nome_modelo, m, n)
    with open(nome_arquivo) as json_file:
        data = json.load(json_file)
        solution = data["CPLEXSolution"]
        df_variable = pd.DataFrame(solution["variables"])
        print(df_variable.head())
        
        df_lincon= pd.DataFrame(solution["linearConstraints"])
        print(df_lincon.head())
        
        return df_variable, df_lincon