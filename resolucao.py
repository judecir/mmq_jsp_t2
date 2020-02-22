from pos_processamento import nome_arquivo_log

from pre_processamento import criar_instancias

import random as rnd
                      
from pos_processamento import nome_arquivo_lp,\
                              exportar_solucao
                          
from modelos import jsp_get_dimensoes,\
                    jsp_disjuntivo_minla,\
                    jsp_disjuntivo_minla_favorito,\
                    jsp_disjuntivo_manne
    
import pandas as pd
                
def escrever_solucao(s):
    if(s.has_objective()):
        print("Cmax=",round(s.get_objective_value(), 4))
        print("Detalhes", s.solve_details)
    else: 
        print("Problema inviavel")

def resolver(modelo, m, n, prefixo=""):
    with open(nome_arquivo_log(modelo.name, m, n, prefixo), 'w') as lout:
            sol= modelo.solve(log_output=lout)
    return sol

def teste_restricoes_minla(restricoes_manne, restricoes_minla, prefix_arq = "t_rest_", tam_amostra=20, intervalo_amostra=15):
    instancias = criar_instancias()
    amostra = rnd.sample(range(1, (len(instancias))-intervalo_amostra), tam_amostra)
    
    
    solucao = []
    
    f = open("resultados.csv", "w")
    f.write("num_maquina; num_jobs; modelo; number_of_constraints; number_of_variables; best_bound; funcao_objetivo; number_of_var_values; has_hit_limit; mip_relative_gap; nb_iterations; nb_linear_nonzeros; status; time; fl_inteiro \n")
    f.close()
    
    for i in amostra: 
        for fl_inteiro in [True, False]:
        
            tempo_max=120
            id_inst = instancias[i]["id"]
            tempo = instancias[i]["tempo"]
            ordem = instancias[i]["ordem"]
            m,n = jsp_get_dimensoes(tempo)
    
            for r in range(len(restricoes_minla)):
                prefixo = "P"\
                        + "{:03d}".format(id_inst)\
                        +"M{:03d}".format(m)\
                        +"J{:03d}".format(n)\
                        +"_{:03d}".format(r)\
                        +"rest"+"_Zint"\
                        +str(fl_inteiro)
                
                print("Criando modelo: "+ prefixo)
                modelo = jsp_disjuntivo_minla(tempo,
                                             ordem, 
                                             tempo_max=tempo_max,
                                             fl_inteiro=fl_inteiro,
                                             restricoes=restricoes_manne + restricoes_minla[:r])
                print("Modelo criado!")
                #modelos.append(modelo)
                
                modelo.export(nome_arquivo_lp(modelo.name, m,n, prefixo))
                print("Resolvendo...")
                sol = resolver(modelo, m, n, prefixo)
                print("Modelo resolvido!")
                print(modelo.name, ": ")
                escrever_solucao(sol)
                exportar_solucao(sol, modelo.name, m, n, prefixo)
                solucao.append(dict({"num_maquina":m
                                     ,"num_jobs":n
                                     ,"modelo":prefixo
                                     ,"number_of_constraints":modelo.number_of_constraints
                                     ,"number_of_variables":modelo.number_of_variables
                                     ,"best_bound":sol.solve_details.best_bound
                                     ,"funcao_objetivo":sol.get_objective_value()
                                     ,"number_of_var_values":sol.number_of_var_values
                                     ,"has_hit_limit":sol.solve_details.has_hit_limit()
                                     ,"mip_relative_gap":sol.solve_details.mip_relative_gap
                                     ,"nb_iterations":sol.solve_details.nb_iterations
                                     ,"nb_linear_nonzeros":sol.solve_details.nb_linear_nonzeros
                                     ,"status":sol.solve_details.status
                                     ,"time":sol.solve_details.time
                                     ,"fl_inteiro":fl_inteiro}))
                linha = str(m)+ "; "+\
                        str(n)+ "; "+\
                        str(prefixo)+ "; "+\
                        str(modelo.number_of_constraints)+ "; "+\
                        str(modelo.number_of_variables)+ "; "+\
                        str(sol.solve_details.best_bound)+ "; "+\
                        str(sol.get_objective_value())+ "; "+\
                        str(sol.number_of_var_values)+ "; "+\
                        str(sol.solve_details.has_hit_limit())+ "; "+\
                        str(sol.solve_details.mip_relative_gap)+ "; "+\
                        str(sol.solve_details.nb_iterations)+ "; "+\
                        str(sol.solve_details.nb_linear_nonzeros)+ "; "+\
                        str(sol.solve_details.status)+ "; "+\
                        str(sol.solve_details.time)+ "; "+\
                        str(fl_inteiro)+ "; \n" 
                        
                f = open("solucoes/resultados.csv", "a")
                f.write(linha)
                f.close()
    
    
    df_sol = pd.DataFrame(solucao)
    df_sol.to_csv("info_sol"+".csv", index=False, sep=";", decimal=",")

def teste_manne_minlafav(prefix_arq = "t_minlafav_", tam_amostra=20, tempo_max=120):
    instancias = criar_instancias()
    solucao = []

    f = open("resultados_minlafav.csv", "w")
    #f.write("num_maquina; num_jobs; modelo; number_of_constraints; number_of_variables; best_bound; funcao_objetivo; number_of_var_values; has_hit_limit; mip_relative_gap; nb_iterations; nb_linear_nonzeros; status; time; fl_inteiro \n")
    f.write("problema;  modelo;  num_jobs;  num_maquina;  fl_inteiro;  best_bound;  funcao_objetivo;  mip_relative_gap; number_of_contraints; number_of_variables; number_of_var_values; nb_interations; nb_linear_nonzeros; status; time; has_hit_limit \n")
    f.close()
    
    for i in range(tam_amostra): 
        for fl_inteiro in [True, False]:
            id_inst = instancias[i]["id"]
            tempo = instancias[i]["tempo"]
            ordem = instancias[i]["ordem"]
            m,n = jsp_get_dimensoes(tempo)
    
            for mod in ["Manne", "MinLA"]:
                nome_problema = prefix_arq\
                        + "{:03d}".format(id_inst)\
                        +"M{:03d}".format(m)\
                        +"J{:03d}".format(n)
                prefixo = prefix_arq\
                        + "{:03d}".format(id_inst)\
                        +"M{:03d}".format(m)\
                        +"J{:03d}".format(n)\
                        +"_Zint"\
                        +str(fl_inteiro)\
                        +"_"+mod
                print("Criando modelo: "+ prefixo)
                if mod == "Manne":
                    modelo = jsp_disjuntivo_manne(tempo, ordem, tempo_max=tempo_max, fl_inteiro=fl_inteiro)
                else:
                    modelo = jsp_disjuntivo_minla_favorito(tempo, ordem, tempo_max=tempo_max, fl_inteiro=fl_inteiro)
                    
                print("Modelo criado!")
                #modelos.append(modelo)
                
                #modelo.export(nome_arquivo_lp(modelo.name, m,n, prefixo))
                print("Resolvendo...")
                sol = resolver(modelo, m, n, prefixo)
                print("Modelo resolvido!")
                print(modelo.name, ": ")
                escrever_solucao(sol)
                exportar_solucao(sol, modelo.name, m, n, prefixo)
                solucao.append(dict({"num_maquina":m
                                     ,"num_jobs":n
                                     ,"modelo":prefixo
                                     ,"number_of_constraints":modelo.number_of_constraints
                                     ,"number_of_variables":modelo.number_of_variables
                                     ,"best_bound":sol.solve_details.best_bound
                                     ,"funcao_objetivo":sol.get_objective_value()
                                     ,"number_of_var_values":sol.number_of_var_values
                                     ,"has_hit_limit":sol.solve_details.has_hit_limit()
                                     ,"mip_relative_gap":sol.solve_details.mip_relative_gap
                                     ,"nb_iterations":sol.solve_details.nb_iterations
                                     ,"nb_linear_nonzeros":sol.solve_details.nb_linear_nonzeros
                                     ,"status":sol.solve_details.status
                                     ,"time":sol.solve_details.time
                                     ,"fl_inteiro":fl_inteiro}))
    
                linha = nome_problema + "; "+\
                        str(prefixo)+ "; "+\
                        str(m)+ "; "+\
                        str(n)+ "; "+\
                        str(fl_inteiro)+ "; " +\
                        str(sol.solve_details.best_bound)+ "; "+\
                        str(sol.get_objective_value())+ "; "+\
                        str(sol.solve_details.mip_relative_gap)+ "; "+\
                        str(modelo.number_of_constraints)+ "; "+\
                        str(modelo.number_of_variables)+ "; "+\
                        str(sol.number_of_var_values)+ "; "+\
                        str(sol.solve_details.nb_iterations)+ "; "+\
                        str(sol.solve_details.nb_linear_nonzeros)+ "; "+\
                        str(sol.solve_details.status)+ "; "+\
                        str(sol.solve_details.time)+ "; "+\
                        str(sol.solve_details.has_hit_limit())+ "; "+\
                        " \n"
                        
                f = open("resultados_minlafav.csv", "a")
                f.write(linha)
                f.close()
    
    
    df_sol = pd.DataFrame(solucao)
    df_sol.to_csv("df_resultados_minlafav"+".csv", index=False, sep=";", decimal=",")
    
    return df_sol