import streamlit as st
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import urllib3
import xml.etree.ElementTree as ET

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

USERNAME = "p_heflo"
PASSWORD = "Q0)G$sW]rj"
SOAP_URL = "https://raizeducacao160286.rm.cloudtotvs.com.br:8051/wsDataServer/IwsDataServer"
BASE_URL = "https://raizeducacao160286.rm.cloudtotvs.com.br:8051/api/framework/v1/consultaSQLServer/RealizaConsulta"

# Lista de Filiais
filiais = [
    {"NOMEFANTASIA": "COLÉGIO E CURSO AO CUBO BARRA",       "CODCOLIGADA": 5,  "CODFILIAL": 2},
    {"NOMEFANTASIA": "COLÉGIO E CURSO AO CUBO BOTAFOGO",     "CODCOLIGADA": 5,  "CODFILIAL": 5},
]

# ---------------------------------------------------------------------------------
# Funções de consulta TOTVS (RAIZA.0005, RAIZA.0009, RAIZA.0012, RAIZA.0011, etc.)
# ---------------------------------------------------------------------------------
def obter_turmas(codcoligada, codfilial):
    url = f"{BASE_URL}/RAIZA.0005/0/S"
    params = {"parameters": f"CODCOLIGADA={codcoligada};CODFILIAL={codfilial}"}
    resp = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD), params=params, verify=False)
    return resp.json() if resp.status_code == 200 else []

def obter_alunos_turma(codcoligada, codfilial, codturma):
    url = f"{BASE_URL}/RAIZA.0009/0/S"
    params = {"parameters": f"CODCOLIGADA={codcoligada};CODFILIAL={codfilial};CODTURMA={codturma}"}
    resp = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD), params=params, verify=False)
    return resp.json() if resp.status_code == 200 else []

def obter_etapas(codcoligada, codfilial, codturma, ra):
    url = f"{BASE_URL}/RAIZA.0012/0/S"
    params_str = f"CODCOLIGADA={codcoligada};CODFILIAL={codfilial};CODTURMA={codturma};RA={ra}"
    resp = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD), params={"parameters": params_str}, verify=False)
    return resp.json() if resp.status_code == 200 else []

def obter_provas(codcoligada, codfilial, codturma, ra, codeetapa):
    """
    Chama RAIZA.0011 com PROVA=% para descobrir as provas disponíveis
    naquele contexto (coligada, filial, turma, ra, codeetapa).
    """
    url = f"{BASE_URL}/RAIZA.0011/0/S"
    param_str = (
        f"CODCOLIGADA={codcoligada};CODFILIAL={codfilial};"
        f"CODTURMA={codturma};RA={ra};CODETAPA={codeetapa};PROVA=%"
    )
    resp = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD),
                        params={"parameters": param_str}, verify=False)
    if resp.status_code == 200:
        dados = resp.json() or []
        df_temp = pd.DataFrame(dados)
        if "PROVA" in df_temp.columns:
            return sorted(df_temp["PROVA"].dropna().unique().tolist())
    return []

def obter_notas(codcoligada, codfilial, codturma, ra, codeetapa, prova):
    """
    RAIZA.0011 com :PROVA para filtrar e retornar as colunas,
    mas no Python exibiremos só DISCIPLINA/PROVA/NOTAPROVA.
    """
    url = f"{BASE_URL}/RAIZA.0011/0/S"
    param_str = (
        f"CODCOLIGADA={codcoligada};CODFILIAL={codfilial};"
        f"CODTURMA={codturma};RA={ra};CODETAPA={codeetapa};PROVA={prova}"
    )
    resp = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD),
                        params={"parameters": param_str}, verify=False)
    return resp.json() if resp.status_code == 200 else []

# ---------------------------------------------------------------------------------
# Funções de geração e envio de XML
# ---------------------------------------------------------------------------------
def gerar_xml_envelope_edunotas(row):
    """
    Gera envelope SOAP. Precisamos de:
    - CODCOLIGADA, RA, CODETAPA, CODPROVA => PrimaryKey 
    - NOTAPROVA => valor
    """
    codcoligada = row["CODCOLIGADA"]
    ra = row["RA"]
    codeetapa = row["CODETAPA"]
    codprova = row["CODPROVA"]
    nota = row["NOTAPROVA"]
    data_hoje = "2025-03-13"  # Exemplo fixo

    xml_env = f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tot="http://www.totvs.com/">
  <soapenv:Header/>
  <soapenv:Body>
    <tot:SaveRecord>
      <tot:DataServerName>EduNotasData</tot:DataServerName>
      <tot:PrimaryKey>{codcoligada};{ra};{codeetapa};{codprova}</tot:PrimaryKey>
      <tot:Contexto>CODCOLIGADA={codcoligada};CODFILIAL=1;CODTIPOCURSO=1;CODSISTEMA=S</tot:Contexto>
      <tot:XML><![CDATA[
        <NotasAvaliacao>
          <CODCOLIGADA>{codcoligada}</CODCOLIGADA>
          <RA>{ra}</RA>
          <CODETAPA>{codeetapa}</CODETAPA>
          <CODPROVA>{codprova}</CODPROVA>
          <NOTA>{nota}</NOTA>
          <DATAAVALIACAO>{data_hoje}</DATAAVALIACAO>
        </NotasAvaliacao>
      ]]></tot:XML>
    </tot:SaveRecord>
  </soapenv:Body>
</soapenv:Envelope>"""
    return xml_env

def enviar_xml_soap(xml_envelope):
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "http://www.totvs.com/IwsDataServer/SaveRecord"
    }
    resp = requests.post(
        SOAP_URL,
        data=xml_envelope.encode("utf-8"),
        headers=headers,
        auth=HTTPBasicAuth(USERNAME, PASSWORD),
        verify=False
    )
    if resp.status_code == 200:
        try:
            root = ET.fromstring(resp.content)
            fault = root.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Fault')
            if fault is not None:
                faultstring = fault.find('faultstring').text
                return (False, f"SOAP Fault: {faultstring}")
            else:
                return (True, "OK")
        except ET.ParseError:
            return (False, f"Erro parse do XML TOTVS:\n{resp.text}")
    else:
        return (False, f"HTTP {resp.status_code} - {resp.text}")

# ---------------------------------------------------------------------------------
# Aplicação principal
# ---------------------------------------------------------------------------------
def main():
    st.title("Edição de Notas Sem Fechar a Tabela ao Editar")

    # 1) Selecionar Filial
    filial_nome = st.selectbox(
        "Selecione a Filial:",
        [f"{f['NOMEFANTASIA']} (Filial {f['CODFILIAL']})" for f in filiais]
    )
    filial_info = next((f for f in filiais if f"Filial {f['CODFILIAL']}" in filial_nome), None)
    if not filial_info:
        return
    codcoligada = filial_info["CODCOLIGADA"]
    codfilial   = filial_info["CODFILIAL"]

    # 2) Turma
    turmas_data = obter_turmas(codcoligada, codfilial)
    lista_turmas = sorted({t["CODTURMA"] for t in turmas_data if "CODTURMA" in t})
    turma_sel = st.selectbox("Selecione a Turma:", lista_turmas)
    if not turma_sel:
        return

    # 3) Aluno
    alunos_data = obter_alunos_turma(codcoligada, codfilial, turma_sel)
    lista_alunos = [
        f"{a['RA']} - {a['NOME']}"
        for a in alunos_data if "RA" in a and "NOME" in a
    ]
    aluno_sel = st.selectbox("Selecione o Aluno:", lista_alunos)
    if not aluno_sel:
        return
    ra_puro = aluno_sel.split(" - ")[0]

    # 4) Etapa
    etapas_data = obter_etapas(codcoligada, codfilial, turma_sel, ra_puro)
    if not etapas_data:
        st.warning("Nenhuma etapa encontrada.")
        return
    etapa_dict = {
        f"{item['ETAPA']} (Cod {item['CODETAPA']})": item["CODETAPA"]
        for item in etapas_data if "ETAPA" in item and "CODETAPA" in item
    }
    etapa_exibida = st.selectbox("Selecione a Etapa:", list(etapa_dict.keys()))
    if not etapa_exibida:
        return
    codeetapa = etapa_dict[etapa_exibida]

    # 5) Buscar provas
    if st.button("Buscar Provas"):
        provas_list = obter_provas(codcoligada, codfilial, turma_sel, ra_puro, codeetapa)
        if not provas_list:
            st.warning("Nenhuma prova encontrada para esse contexto.")
            return
        # Guardamos as provas no session_state
        st.session_state["provas_list"] = provas_list

    # Exibir selectbox de provas, se já buscou
    if "provas_list" in st.session_state:
        prova_sel = st.selectbox("Selecione a Prova:", st.session_state["provas_list"])
        if prova_sel:
            # Botão "Consultar Notas"
            if st.button("Consultar Notas"):
                dados_notas = obter_notas(codcoligada, codfilial, turma_sel, ra_puro, codeetapa, prova_sel)
                if not dados_notas:
                    st.warning("Nenhuma nota encontrada.")
                    return

                df_full = pd.DataFrame(dados_notas)
                if df_full.empty:
                    st.warning("Retorno vazio da consulta.")
                    return

                # Guardamos df_full no session_state
                st.session_state["df_original"] = df_full.copy()
                st.session_state["mostrar_tabela"] = True

                # Montar df_exibir
                # Exibir só DISCIPLINA, PROVA e NOTAPROVA
                colunas_necessarias = ["DISCIPLINA", "PROVA", "NOTAPROVA"]
                # Check se df_full tem estas colunas
                if not all(col in df_full.columns for col in colunas_necessarias):
                    st.error("O retorno não contém colunas DISCIPLINA, PROVA e NOTAPROVA.")
                    return

                df_exibir = df_full[colunas_necessarias].copy()
                # Guardamos no session_state
                st.session_state["df_exibir"] = df_exibir

    # Se a tabela foi consultada e guardada
    if st.session_state.get("mostrar_tabela"):
        if "df_exibir" not in st.session_state:
            st.warning("Não há tabela para exibir. Clique em 'Consultar Notas'.")
            return

        df_exibir_local = st.session_state["df_exibir"]
        st.info("Edite SOMENTE a coluna NOTAPROVA. As outras são fixas.")
        df_editado = st.data_editor(
            df_exibir_local,
            key="data_editor_notas",
            column_config={
                "DISCIPLINA": st.column_config.Column(disabled=True),
                "PROVA": st.column_config.Column(disabled=True),
                "NOTAPROVA": st.column_config.Column(
                    disabled=False,
                    help="Edite apenas a nota"
                ),
            },
            hide_index=True,
            use_container_width=True
        )
        # Atualizar o df_exibir no session_state a cada re-run
        st.session_state["df_exibir"] = df_editado

        # Botão "Salvar Alterações"
        if st.button("Salvar Alterações"):
            if "df_original" not in st.session_state:
                st.error("df_original não encontrado no session_state.")
                return

            df_original_local = st.session_state["df_original"]
            # Merge por (DISCIPLINA, PROVA)
            merged = df_original_local.merge(
                df_editado,
                on=["DISCIPLINA", "PROVA"],
                suffixes=("_old", "_new"),
                how="left"
            )
            # Filtra diferenças em NOTAPROVA
            df_alteradas = merged.loc[
                merged["NOTAPROVA_old"] != merged["NOTAPROVA_new"]
            ].copy()
            if df_alteradas.empty:
                st.info("Nenhuma alteração de nota.")
                return

            sucesso, falhas = 0, 0
            for _, row in df_alteradas.iterrows():
                # Montamos dict com as colunas-chaves e a NOTAPROVA nova
                dict_row = {
                    "CODCOLIGADA": row["CODCOLIGADA"],
                    "RA": row["RA"],
                    "CODETAPA": row["CODETAPA"],
                    "CODPROVA": row.get("CODPROVA", ""),  # se existe no DF
                    "NOTAPROVA": row["NOTAPROVA_new"]
                }
                xml_env = gerar_xml_envelope_edunotas(dict_row)
                ok, msg = enviar_xml_soap(xml_env)
                if ok:
                    sucesso += 1
                else:
                    falhas += 1
                    st.error(f"Erro salvando {row['DISCIPLINA']}: {msg}")

            if falhas == 0:
                st.success(f"Tudo certo! {sucesso} notas salvas.")
            else:
                st.warning(f"{sucesso} salvas, {falhas} falharam.")

if __name__ == "__main__":
    main()
