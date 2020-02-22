import numpy as np

from docplex.mp.model import Model
from pre_processamento import jsp_checar_tempo_ordem

# Auxiliares =========================================

# Monta o dicionário para que passamos para as restrições
def montar_dic_problema(m, n, Maquinas, Jobs, tempo, ordem, fl_inteiro):
    return  {"m":m
            ,"n":n
            ,"Maquinas":Maquinas
            ,"Jobs": Jobs
            ,"tempo":tempo
            ,"ordem":ordem
            ,"fl_inteiro":fl_inteiro}

# Retorna as dimensões do problema
def jsp_get_dimensoes(_tempo):
    #m,n
    return len(_tempo), len(_tempo[0])

# Expressão para o big M
def calcular_big_m(_tempo):
    # bigM
    P = sum([item for l in _tempo for item in l])
    return P

# P_j: soma de todos os tempos de um job j em todas as maquinas
def calcular_p_j(_tempo):
    return np.sum(_tempo, axis=0)

# Ordem da maquina i no job j
def ordem_maq_i_job_j(ordem, maq, job):
    return np.where(ordem[job]==maq)[0][0]
   
# P^-_ij: soma dos tempos de processamento do job j em todas 
# as maquinas anteriores a máquina i, inclusive 
def p_menos(tempo, ordem, maq, job):
    lista = [tempo[ordem[job, h], job] for h in range(ordem_maq_i_job_j(ordem, maq, job)+1)]
    return sum(lista)

# P^+_ij: soma dos tempos de processamento do job j em todas 
# as maquinas posteriores a máquina i, inclusive 
def p_mais(m, n, tempo, ordem, maq, job):
    lista= [tempo[ordem[job, h], job] for h in range(ordem_maq_i_job_j(ordem, maq, job), m)]
    return sum(lista)

#=====================================================

# Variáveis ==========================================

# x_ij: tempo de início do job j na máquina i
def jsp_manne_var_x(modelo, Problema):
    Maquinas = Problema["Maquinas"]
    Jobs = Problema["Jobs"]
    # Represanta o início do job j na máquina i
    idx = [(i,j) for i in Maquinas for j in Jobs]
    x = modelo.continuous_var_dict(idx, lb=0.0, name="x")
    return x

# z_ijk: 1 se o job j precede o job k na máquina i
def jsp_manne_var_z(modelo, Problema):
    Maquinas = Problema["Maquinas"]
    Jobs = Problema["Jobs"]
    fl_inteiro = Problema["fl_inteiro"]
    
    # Variável binária que marca 1 se o job j precede k na máquina i
    idz = [(i,j, k) for i in Maquinas for j in Jobs for k in Jobs if j<k] 
    if not fl_inteiro:
        z = modelo.continuous_var_dict(idz, lb=0.0, ub=1.0, name="z")
    else:
        z = modelo.binary_var_dict(idz,lb=0, ub=1, name="z")
    return z

# c_max: makespan
def jsp_manne_var_cmax(modelo, Problema):
    tempo = Problema["tempo"]
    # Variável para representar o makespan
    cmax = modelo.continuous_var(lb=np.max(calcular_p_j(tempo)), name="cmax")
    return cmax

# y_ij:linearizacao de uma expressao que representa o fim do job anterior a j
# na maquina i OU o fim do proprio job j na sua maquina anterior
def jsp_minla_var_y(modelo, Problema):
    Maquinas = Problema["Maquinas"]
    Jobs = Problema["Jobs"]
    # Variável de linearização
    idy = [(i,j) for i in Maquinas for j in Jobs]
    y = modelo.continuous_var_dict(idy, lb=0.0, name="y")
    return y

#=====================================================

# Função objetivo ====================================
#minimizar o makespan
def jsp_fo_makespan(modelo, x, z, cmax, y, Problema):
    modelo.minimize(cmax)
#=====================================================

# Restrições ====================================

# Garante a ordem sigma^j para cada job j
def jsp_manne_rest_ordem_maq_job(modelo, x, z, cmax, y, Problema):
    m = Problema["m"]
    Jobs = Problema["Jobs"]
    tempo = Problema["tempo"]
    ordem = Problema["ordem"]
    
    for j in Jobs:
        for h in range(1, m):
            h_maq     = ordem[j, h]
            h_maq_ant = ordem[j, (h-1)]
            modelo.add_constraint(x[h_maq, j] >= x[h_maq_ant, j] + tempo[h_maq_ant, j])

# Precedência
def jsp_manne_rest_precedencia(modelo, x, z, cmax, y, Problema):
    Maquinas 	= Problema["Maquinas"]
    Jobs 		= Problema["Jobs"]
    tempo 		= Problema["tempo"]
        
    P = calcular_big_m(tempo)
    for i in Maquinas:
        for j in Jobs:
            for k in Jobs:
                if j<k:
                    modelo.add_constraint(x[i, j] >= x[i, k] + tempo[i, k] - P*z[i, j, k])
                    modelo.add_constraint(x[i, k] >= x[i, j] + tempo[i, j] - P*(1-z[i,j, k]))

# Garante o makespan
def jsp_manne_rest_makespan(modelo, x, z, cmax, y, Problema):
    m 			= Problema["m"]
    Jobs 		= Problema["Jobs"]
    tempo 		= Problema["tempo"]
    ordem 		= Problema["ordem"]
    
    for j in Jobs:
        ult_maq_j = ordem[j, m-1]
        modelo.add_constraint(cmax >= x[ult_maq_j, j] +  tempo[ult_maq_j, j])

# Soma de z igual a 1:
def jsp_minla_rest_soma_z_1(modelo, x, z, cmax, y, Problema):
    Maquinas 	= Problema["Maquinas"]
    Jobs 		= Problema["Jobs"]
    
    for i in Maquinas:
        for j in Jobs:
            for k in Jobs:
                if j != k:
                    modelo.add_constraint(z[i,j,k]+ z[i,k,j] == 1) #um arco eh maior que outro
                   
# Desigualdade triangular
def jsp_minla_rest_desig_triang(modelo, x, z, cmax, y, Problema):
    Maquinas 	= Problema["Maquinas"]
    Jobs 		= Problema["Jobs"]
    for i in Maquinas:
        for j in Jobs:
            for k in Jobs:
                if j != k:
                    modelo.add_constraint(z[i,j,k]+ z[i,k,j] == 1) #um arco eh maior que outro
                    for u in Jobs:
                        if u!=j and u != k:
                            modelo.add_constraint(z[i,j,k]+ z[i,k,u] + z[i,u,j] <= 2) #desigualdade triangular

# Garante a permutação 
def jsp_minla_rest_permut(modelo, x, z, cmax, y, Problema):
    n 			= Problema["n"]
    Maquinas 	= Problema["Maquinas"]
    Jobs 		= Problema["Jobs"]
    for i in Maquinas:
        for j in Jobs:
            for k in Jobs:
                if j < k:
                    modelo.add_constraint(-n*(1-z[i, j, k])+1 <= modelo.sum(z[i, u, k] for u in Jobs if u<k)
                                                              +modelo.sum((1-z[i, k, u]) for u in Jobs if u>k) 
                                                              -modelo.sum(z[i, u, j] for u in Jobs if u<j) 
                                                              -modelo.sum((1-z[i, j, u]) for u in Jobs if u>j)) 

# Soma dos arcos de entrada mais soma dos arcos de saída
def jsp_minla_rest_arc_in_out(modelo, x, z, cmax, y, Problema):
    n 			= Problema["n"]
    Maquinas 	= Problema["Maquinas"]
    Jobs 		= Problema["Jobs"]
    for i in Maquinas:
        for j in Jobs:
            modelo.add_constraint( modelo.sum(z[i, u, j] for u in Jobs if u!=j) \
                                  +modelo.sum(z[i, j, v] for v in Jobs if v!=j) \
                                  == n-1)

# Restrição Trivial
def jsp_minla_rest_soma_trivial(modelo, x, z, cmax, y, Problema):
    n 			= Problema["n"]
    Maquinas 	= Problema["Maquinas"]
    Jobs 		= Problema["Jobs"]
    for i in Maquinas:
        modelo.add_constraint( modelo.sum(z[i, u, j] + (1-z[i, u, j]) for u in Jobs for j in Jobs if u<j) == n/2*(n-1))

# Restricao primeira maquina de k comeca no maximo no tempo de termino 
# do job anterior a ele na mesma maquina
def jsp_minla_rest_1_maq_j(modelo, x, z, cmax, y, Problema):
    n 			= Problema["n"]
    Jobs 		= Problema["Jobs"]
    tempo 		= Problema["tempo"]
    ordem 		= Problema["ordem"]
    
    P = calcular_big_m(tempo)
    
    for j in Jobs:
        for k in Jobs:
            if j != k:
                maq1_k = ordem[k,0] 
                modelo.add_constraint(x[maq1_k , k] <= P*(n+1)*(1-z[maq1_k, j, k])
                                                      +P*(modelo.sum(z[maq1_k, u, k] for u in Jobs if u!=k)
                                                      -modelo.sum(z[maq1_k, u, j] for u in Jobs if u!=j)
                                                      -1) 
                                                      +x[maq1_k, j] + tempo[maq1_k, j])

# Restrição upper bound para x_ij
# Tempo de inicio do job em uma maquina sera no maximo o tempo de termino 
# desse mesmo job em sua maquina anterior ou o tempo de termino do job 
# exatamente anterior a ele na mesma maquina
def jsp_minla_rest_ub_x(modelo, x, z, cmax, y, Problema):
    m 			= Problema["m"]
    n 			= Problema["n"]
    Jobs 		= Problema["Jobs"]
    tempo 		= Problema["tempo"]
    ordem 		= Problema["ordem"]

    P = calcular_big_m(tempo)
    
    for h in range(1, m):
        for j in Jobs:
            for k in Jobs:
                if j != k:
                    h_maq_k = ordem[k, h]
                    modelo.add_constraint(x[h_maq_k , k] <= P*(n+1)*(1-z[h_maq_k, j, k]
                                                              +P*(modelo.sum(z[h_maq_k , u, k] for u in Jobs if u!=k)
                                                                  -modelo.sum(z[h_maq_k , u, j] for u in Jobs if u!=j)
                                                                  -1)
                                                              +y[h_maq_k , k]))

# Restricao linearizacao da expressao do tempo maximo entre o termino de um job
# na sua maquina anterior ou o tempo do job exatamente anterior a ele na mesma
# maquina
def jsp_minla_rest_linear_y(modelo, x, z, cmax, y, Problema):
    m 			= Problema["m"]
    Jobs 		= Problema["Jobs"]
    tempo 		= Problema["tempo"]
    ordem 		= Problema["ordem"]

    P = calcular_big_m(tempo)
    for h in range(1, m):
        for j in Jobs:
            for k in Jobs:
                if k != k:
                    h_maq_k = ordem[k, h]
                    h_menos1_maq_k = ordem[k, h-1]
                    modelo.add_constraint(y[h_maq_k , k] >= x[h_maq_k, j] + tempo[h_maq_k-1,j] - P*(1-z[h_maq_k, j, k]))   
                    modelo.add_constraint(y[h_maq_k , k] >= x[h_menos1_maq_k, k] + tempo[h_menos1_maq_k, k])
                    modelo.add_constraint(y[h_maq_k , k] <= cmax)   

# Restricao upper bound do cmax
# O makespan sera no maximo o tempo de inicio de um job na sua ultima maquina
# mais a soma de processamento de todos os jobs em sua ultima maquina
def jsp_minla_rest_ub_cmax(modelo, x, z, cmax, y, Problema):
    m 			= Problema["m"]
    n 			= Problema["n"]
    Jobs 		= Problema["Jobs"]
    tempo 		= Problema["tempo"]
    ordem 		= Problema["ordem"]
    
    P = calcular_big_m(tempo)
    for j in Jobs:
        m_maq_j = ordem[j, m-1]
        modelo.add_constraint(cmax <= P*(n-1+modelo.sum(z[m_maq_j, u, j] for u in Jobs if u!=j))
                                    + x[m_maq_j, j]
                                    + sum([tempo[ordem[it, (m-1)], it] for it in range(j)]))

# Lower-bound da 1a máquina do job j
# Um job em sua primeira maquina iniciara pelo menos na soma do tempo de
# de processamento de todos os outros jobs anteriores na mesma maquina
def jsp_minla_rest_lb_1_maq_j(modelo, x, z, cmax, y, Problema):
    Jobs 		= Problema["Jobs"]
    tempo 		= Problema["tempo"]
    ordem 		= Problema["ordem"]
    for j in Jobs:
        maq1_j = ordem[j, 0]
        modelo.add_constraint(x[maq1_j, j] >= modelo.sum(tempo[maq1_j, k]*z[maq1_j, k, j]
                                              for k in Jobs if k != j))

# Restricao lower bound para x_ik
# Um job iniciara em uma maquina pelo menos no tempo de soma de todos os jobs 
# anteriores a ele nessa maquina
def jsp_minla_rest_lb_xik(modelo, x, z, cmax, y, Problema):
    Maquinas    = Problema["Maquinas"]
    Jobs        = Problema["Jobs"]
    tempo       = Problema["tempo"]
    for i in Maquinas:
        for k in Jobs:
            modelo.add_constraint(x[i,k] >= modelo.sum(z[i,j,k]*tempo[i,j] for j in Jobs if j<k)
                                            +modelo.sum((1-z[i,k,j])*tempo[i,j] for j in Jobs if j>k))

# Restricao lower bound da 1a maq de um job considerando os tempos de execucao
# Um job iniciara em sua primeira maquina pelo menos na soma de processamento
# dos jobs anteriores a ele em suas maquinas anteriores
def jsp_minla_rest_lb_1_maq_j_p_menos(modelo, x, z, cmax, y, Problema):
    Jobs 		= Problema["Jobs"]
    tempo 		= Problema["tempo"]
    ordem 		= Problema["ordem"]
    for j in Jobs:
        for k in Jobs:
            if j != k:
                maq1_j = ordem[j, 0]
                P_menos = p_menos(tempo, ordem, maq1_j, k)
                modelo.add_constraint(x[maq1_j, j]>= P_menos*z[maq1_j, k, j])

# Restricao lower bound de x_ik considerando o tempo de execucao
# Um job iniciaria em uma maquina pelo menos quando todos os jobs anteriores 
# a ele terminarem em suas maquinas anteriores
def jsp_minla_rest_lb_xik_p_menos(modelo, x, z, cmax, y, Problema):
    Maquinas    = Problema["Maquinas"]
    Jobs        = Problema["Jobs"]
    tempo       = Problema["tempo"]
    ordem       = Problema["ordem"]
    for i in Maquinas:
        for k in Jobs:
            for j in Jobs:
                if j<k:
                    P_menos_i_j = p_menos(tempo, ordem, i, j)
                    P_menos_i_k = p_menos(tempo, ordem, i, k)
                    modelo.add_constraint(x[i,k] >=     z[i, j, k]*P_menos_i_j)
                    modelo.add_constraint(x[i,j] >= (1-z[i, j, k])*P_menos_i_k)

# Restricao lower bound makespan considerando o tempo de execucao
# O makespan sera o inicio de um job k que precede outro job j em sua ultima 
# maquina mais o tempo de processamento desse job k em suas maquinas posteriores
def jsp_minla_rest_lb_cmax_p_mais(modelo, x, z, cmax, y, Problema):
    m 			= Problema["m"]
    n 			= Problema["n"]
    Jobs 		= Problema["Jobs"]
    tempo 		= Problema["tempo"]
    ordem 		= Problema["ordem"]

    for j in Jobs:
        for k in Jobs:
            if j != k:                
                maqM_j = ordem[j, m-1]
                P_mais =  p_mais(m, n, tempo, ordem, maqM_j, j)
                modelo.add_constraint(cmax>= x[maqM_j, k]+ P_mais *z[maqM_j, k, j])

# Restricao lower bound makespan considerando x_ik
# o makespan sera pelo menos o tempo de inicio de um job em uma maquina
# mais o tempo de processamento dele em suas maquinas posteriores
def jsp_minla_rest_lb_cmax_x_p_mais(modelo, x, z, cmax, y, Problema):
    m 			= Problema["m"]
    n 			= Problema["n"]
    Maquinas 	= Problema["Maquinas"]
    Jobs 		= Problema["Jobs"]
    tempo 		= Problema["tempo"]
    ordem 		= Problema["ordem"]
    for i in Maquinas:
        for j in Jobs:
            P_mais = p_mais(m, n, tempo, ordem, i, j)
            modelo.add_constraint(cmax>= x[i,j] + P_mais)

# Restricao lower bound makespan considerando p mais
# O makespan sera pelo menos o inicio de um job em uma maquina mais a soma de 
# do tempo de processamento em um determinado job em suas maquinas posteriores
def jsp_minla_rest_lb_cmax_x_p_mais_k(modelo, x, z, cmax, y, Problema):
    m 			= Problema["m"]
    n 			= Problema["n"]
    Maquinas 	= Problema["Maquinas"]
    Jobs 		= Problema["Jobs"]
    tempo 		= Problema["tempo"]
    ordem 		= Problema["ordem"]
    for i in Maquinas:
        for j in Jobs:
            for k in Jobs:
                if j<k:
                    P_mais_i_k = p_mais(m, n, tempo, ordem, i, k)
                    P_mais_i_j = p_mais(m, n, tempo, ordem, i, j)
                    modelo.add_constraint(cmax>= x[i,j] + tempo[i,j] + z[i, j, k]*P_mais_i_k)
                    modelo.add_constraint(cmax>= x[i,k] + tempo[i,k] + (1-z[i, j, k])*P_mais_i_j)
# ====================================================

# Modelos ============================================

# Modelo Disjuntivo de Manne
def jsp_disjuntivo_manne(tempo, ordem, tempo_max = 3600, fl_inteiro=True):
    if not jsp_checar_tempo_ordem(tempo, ordem):
        print("Matrizes de TEMPO e ORDEM incorretas!")
    
    # Criando parâmetros ######################################################
    # Número de máquinas e jobs
    m,n = jsp_get_dimensoes(tempo)
    
    
    # Criando conjunto de máquinas e jobs
    Maquinas = range(m)
    Jobs = range(n)
    ###########################################################################
    
    # Criando dicionario do Problema ##########################################
    Problema = montar_dic_problema(m, n, Maquinas, Jobs, tempo, ordem, fl_inteiro)
    ###########################################################################
   
    # Criando instancia do modelo #############################################
    modelo = Model(name='disjuntivo_manne')
    modelo.parameters.timelimit = tempo_max
    ###########################################################################
    
    # Criando variáveis de decisão ############################################
    x    = jsp_manne_var_x(modelo, Problema) # início do job j na máquina i
    z    = jsp_manne_var_z(modelo, Problema) # 1 se j precede a k na máquina i
    cmax = jsp_manne_var_cmax(modelo, Problema) # makespan
    y    = None
    ###########################################################################
    
 
    # Restrições ##############################################################
    jsp_manne_rest_ordem_maq_job(modelo, x, z, cmax, y, Problema)
    jsp_manne_rest_precedencia(modelo, x, z, cmax, y, Problema)
    jsp_manne_rest_makespan(modelo, x, z, cmax, y, Problema)
    ###########################################################################
    
    # Função objetivo:
    jsp_fo_makespan(modelo, x, z, cmax, y, Problema)
    ###########################################################################
    
    return modelo

# Modelo de Manne com restrições do MinLA
def jsp_disjuntivo_minla(tempo, ordem, tempo_max=3600, fl_inteiro=True, restricoes=[jsp_manne_rest_ordem_maq_job, jsp_manne_rest_precedencia, jsp_manne_rest_makespan]):
    if not jsp_checar_tempo_ordem(tempo, ordem):
        print("Matrizes de TEMPO e ORDEM incorretas!")
    
    # Criando parâmetros ######################################################
    # Número de máquinas e jobs
    m,n = jsp_get_dimensoes(tempo)
    
    # Criando conjunto de máquinas e jobs
    Maquinas = range(m)
    Jobs = range(n)
    ###########################################################################
    
    # Criando dicionario do Problema ##########################################
    Problema = montar_dic_problema(m, n, Maquinas, Jobs, tempo, ordem, fl_inteiro)
    ###########################################################################
    
    # Criando instancia do modelo #############################################
    modelo = Model(name='model', )
    modelo.parameters.timelimit = tempo_max
    ###########################################################################
    
    # Criando variáveis de decisão ############################################
    x    = jsp_manne_var_x(modelo, Problema) # início do job j na máquina i
    z    = jsp_manne_var_z(modelo, Problema) # 1 se j precede a k na máquina i
    cmax = jsp_manne_var_cmax(modelo, Problema) # makespan
    y    = jsp_minla_var_y(modelo, Problema)
    ###########################################################################
    

    
    # Restrições ##############################################################
    """
    jsp_manne_rest_ordem_maq_job(modelo, x, z, cmax, y, Problema)
    jsp_manne_rest_precedencia(modelo, x, z, cmax, y, Problema)
    jsp_manne_rest_makespan(modelo, x, z, cmax, y, Problema)
    
    jsp_minla_rest_soma_z_1(modelo, x, z, cmax, y, Problema)
    jsp_minla_rest_desig_triang(modelo, x, z, cmax, y, Problema)
    jsp_minla_rest_permut(modelo, x, z, cmax, y, Problema)
    jsp_minla_rest_arc_in_out(modelo, x, z, cmax, y, Problema)
    jsp_minla_rest_soma_trivial(modelo, x, z, cmax, y, Problema)
    jsp_minla_rest_1_maq_j(modelo, x, z, cmax, y, Problema)
    jsp_minla_rest_ub_x(modelo, x, z, cmax, y, Problema)
    jsp_minla_rest_linear_y(modelo, x, z, cmax, y, Problema)
    jsp_minla_rest_ub_cmax(modelo, x, z, cmax, y, Problema)
    
    jsp_minla_rest_lb_1_maq_j(modelo, x, z, cmax, y, Problema)
    jsp_minla_rest_lb_1_maq_j_p_menos(modelo, x, z, cmax, y, Problema)
    jsp_minla_rest_lb_cmax_p_mais(modelo, x, z, cmax, y, Problema)
    jsp_minla_rest_lb_cmax_x_p_mais(modelo, x, z, cmax, y, Problema)
    """
    for r in restricoes:
        r(modelo, x, z, cmax, y, Problema)
    ###########################################################################
    
    # Função objetivo:
    jsp_fo_makespan(modelo, x, z, cmax, y, Problema)
    ###########################################################################
    
    return modelo

# Modelo de Manne com as melhores restrições do MinLA
def jsp_disjuntivo_minla_favorito(tempo, ordem, tempo_max=3600, fl_inteiro=True):
    if not jsp_checar_tempo_ordem(tempo, ordem):
        print("Matrizes de TEMPO e ORDEM incorretas!")
    
    # Criando parâmetros ######################################################
    # Número de máquinas e jobs
    m,n = jsp_get_dimensoes(tempo)
    
    # Criando conjunto de máquinas e jobs
    Maquinas = range(m)
    Jobs = range(n)
    ###########################################################################
    
    # Criando dicionario do Problema ##########################################
    Problema = montar_dic_problema(m, n, Maquinas, Jobs, tempo, ordem, fl_inteiro)
    ###########################################################################
    
    # Criando instancia do modelo #############################################
    modelo = Model(name='model', )
    modelo.parameters.timelimit = tempo_max
    ###########################################################################
    
    # Criando variáveis de decisão ############################################
    x    = jsp_manne_var_x(modelo, Problema) # início do job j na máquina i
    z    = jsp_manne_var_z(modelo, Problema) # 1 se j precede a k na máquina i
    cmax = jsp_manne_var_cmax(modelo, Problema) # makespan
    y = None
    ###########################################################################
    

    
    # Restrições ##############################################################
    
    jsp_manne_rest_ordem_maq_job(modelo, x, z, cmax, y, Problema)
    #jsp_manne_rest_precedencia(modelo, x, z, cmax, y, Problema)
    #jsp_manne_rest_makespan(modelo, x, z, cmax, y, Problema)
    
    # baseadas nas sugestoes do prof. Christophe
    jsp_minla_rest_lb_xik(modelo, x, z, cmax, y, Problema)
    jsp_minla_rest_lb_xik_p_menos(modelo, x, z, cmax, y, Problema)

    jsp_minla_rest_lb_cmax_x_p_mais_k(modelo, x, z, cmax, y, Problema)
    jsp_minla_rest_lb_cmax_x_p_mais(modelo, x, z, cmax, y, Problema)

    # Função objetivo:
    jsp_fo_makespan(modelo, x, z, cmax, y, Problema)
    ###########################################################################
    
    return modelo
    # ====================================================