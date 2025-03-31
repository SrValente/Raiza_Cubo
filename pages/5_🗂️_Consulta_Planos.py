import streamlit as st
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import urllib3

# Desabilitar avisos SSL (para ambientes de teste)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# -------------------------------
# Configurações e Credenciais
# -------------------------------
USERNAME = "p_heflo"
PASSWORD = "Q0)G$sW]rj"
BASE_URL = "https://raizeducacao160286.rm.cloudtotvs.com.br:8051/api/framework/v1/consultaSQLServer/RealizaConsulta"
# Filtro fixo para o campo CODPERLET (não há seleção de período letivo)
CODPERLET = 2024

# -------------------------------
# Função para obter as filiais
# -------------------------------
def obter_filiais():
    return [
    {"NOMEFANTASIA": "COLÉGIO E CURSO AO CUBO BARRA",       "CODCOLIGADA": 5,  "CODFILIAL": 2},
    {"NOMEFANTASIA": "COLÉGIO E CURSO AO CUBO BOTAFOGO",     "CODCOLIGADA": 5,  "CODFILIAL": 5},
]

# -------------------------------
# Consulta de Planos de Pagamento (RAIZA.0015)
# -------------------------------
def obter_planos_pagamento(codcoligada, codfilial):
    url = f"{BASE_URL}/RAIZA.0015/0/S"
    # Parâmetros fixos: CODPERLET, CODCOLIGADA e CODFILIAL
    parametros = f"CODPERLET={CODPERLET};CODCOLIGADA={codcoligada};CODFILIAL={codfilial}"
    params = {"parameters": parametros}
    resp = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD), params=params, verify=False)
    if resp.status_code == 200:
        dados = resp.json()
        if isinstance(dados, list):
            # Supõe-se que a query retorne o campo "NOME_PGTO"
            planos = [item.get("NOME_PGTO") for item in dados if item.get("NOME_PGTO")]
            return sorted(list(set(planos)))
    st.error(f"Erro ao obter planos de pagamento: {resp.status_code}")
    return []

# -------------------------------
# Consulta de Dados Detalhados (RAIZA.0014)
# -------------------------------
def obter_dados_pagamento(codcoligada, codfilial, nome_pgto):
    url = f"{BASE_URL}/RAIZA.0014/0/S"
    # Inclui o filtro fixo CODPERLET e filtra pelo plano (NOME_PGTO)
    parametros = f"CODPERLET={CODPERLET};CODCOLIGADA={codcoligada};CODFILIAL={codfilial};NOME_PGTO={nome_pgto}"
    params = {"parameters": parametros}
    resp = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD), params=params, verify=False)
    if resp.status_code == 200:
        return resp.json()
    st.error(f"Erro ao obter dados de pagamento (RAIZA.0014): {resp.status_code}")
    return []

# -------------------------------
# Aplicação Principal
# -------------------------------
def main():
    st.title("Central de Pagamento - Consulta TOTVS")
    
    # Seleção de Filial
    filiais = obter_filiais()
    opcoes_filial = {f"{f['NOMEFANTASIA']} (Filial {f['CODFILIAL']})": f for f in filiais}
    filial_selecionada = st.selectbox("Selecione a Filial:", list(opcoes_filial.keys()))
    f_info = opcoes_filial.get(filial_selecionada)
    if not f_info:
        st.error("Filial não selecionada ou inválida.")
        st.stop()
    codcoligada = f_info["CODCOLIGADA"]
    codfilial = f_info["CODFILIAL"]
    
    st.markdown("---")
    st.subheader("Planos de Pagamento")
    planos = obter_planos_pagamento(codcoligada, codfilial)
    if not planos:
        st.error("Nenhum plano de pagamento encontrado.")
        st.stop()
    plano_selecionado = st.selectbox("Selecione o Plano de Pagamento:", planos)
    
    st.markdown("---")
    st.subheader("Dados Detalhados de Pagamento")
    dados = obter_dados_pagamento(codcoligada, codfilial, plano_selecionado)
    if dados:
        df = pd.DataFrame(dados)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Nenhum dado encontrado para o plano selecionado.")

if __name__ == "__main__":
    main()
