import pandas as pd
import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import urllib3
import logging
import time

# ======================================
# Configurações iniciais
# ======================================
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.DEBUG)  # Logging para debug

USERNAME = "p_heflo"
PASSWORD = "Q0)G$sW]rj"
BASE_URL = "https://raizeducacao160286.rm.cloudtotvs.com.br:8051/api/framework/v1/consultaSQLServer/RealizaConsulta"

# ======================================
# Lista de filiais
# ======================================
filiais = [
    {"NOMEFANTASIA": "COLÉGIO E CURSO AO CUBO BARRA",       "CODCOLIGADA": 5,  "CODFILIAL": 2},
    {"NOMEFANTASIA": "COLÉGIO E CURSO AO CUBO BOTAFOGO",     "CODCOLIGADA": 5,  "CODFILIAL": 2},
]

# ======================================
# Funções de consulta
# ======================================
def obter_turmas(codcoligada, codfilial):
    """
    Consulta RAIZA.0005 e retorna as turmas disponíveis.
    """
    url = f"{BASE_URL}/RAIZA.0005/0/S"
    params = {
        "parameters": f"CODCOLIGADA={codcoligada};CODFILIAL={codfilial}"
    }
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD), params=params, verify=False)
    if response.status_code == 200:
        return response.json()
    logging.error(f"Erro ao obter turmas: {response.status_code} - {response.text}")
    return []

def obter_alunos_turma(codcoligada, codfilial, codturma):
    """
    Consulta RAIZA.0009 para obter a lista de alunos da turma.
    """
    url = f"{BASE_URL}/RAIZA.0009/0/S"
    params = {
        "parameters": f"CODCOLIGADA={codcoligada};CODFILIAL={codfilial};CODTURMA={codturma}"
    }
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD), params=params, verify=False)
    if response.status_code == 200:
        return response.json()
    logging.error(f"Erro ao obter alunos da turma: {response.status_code} - {response.text}")
    return []

def obter_faltas_por_aluno(codcoligada, codfilial, codturma, alunos, dia_semana, data):
    """
    Para cada aluno, consulta RAIZA.0010 para saber os horários que devem receber falta.
    """
    url = f"{BASE_URL}/RAIZA.0010/0/S"
    faltas = []
    for aluno in alunos:
        params = {
            "parameters": (
                f"CODCOLIGADA={codcoligada};CODFILIAL={codfilial};"
                f"CODTURMA={codturma};RA={aluno['RA']};"
                f"DIASEMANA={dia_semana};DATA={data.strftime('%Y-%m-%d')}"
            )
        }
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD), params=params, verify=False)
        if response.status_code == 200:
            faltas.append({
                "RA": aluno["RA"],
                "NOME": aluno["NOME"],
                "HORARIOS": response.json()
            })
        else:
            logging.error(f"Erro ao consultar faltas para RA {aluno['RA']}: {response.status_code} - {response.text}")
    return faltas

# ======================================
# Geração de dados e XML
# ======================================
def organizar_dados_para_xml(faltas, data, codcoligada, codfilial, codturma, dia_semana):
    """
    Converte a lista de faltas (aluno, horários) em um DataFrame adequado para gerar o XML.
    """
    dados = []
    for falta in faltas:
        for horario in falta["HORARIOS"]:
            dados.append({
                "CODCOLIGADA": codcoligada,
                "CODFILIAL": codfilial,
                "DATA": data.strftime('%Y-%m-%dT%H:%M:%S'),
                "CODTURMA": codturma,
                "DIADASEMANA": dia_semana,
                "RA": falta["RA"],
                "IDHORARIOTURMA": horario.get("IDHORARIOTURMA"),
                "IDTURMADISC":   horario.get("IDTURMADISC")
            })
    return pd.DataFrame(dados)

def gerar_xml(row):
    """
    Gera o SOAP Envelope (XML) para lançar a falta no TOTVS via EduFrequenciaDiariaWSData.
    """
    return f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tot="http://www.totvs.com/">
    <soapenv:Header/>
    <soapenv:Body>
        <tot:SaveRecord>
            <tot:DataServerName>EduFrequenciaDiariaWSData</tot:DataServerName>
            <tot:XML><![CDATA[
                <EduFrequenciaDiaria>
                    <SFREQUENCIA>
                        <CODCOLIGADA>{row['CODCOLIGADA']}</CODCOLIGADA>
                        <IDHORARIOTURMA>{row['IDHORARIOTURMA']}</IDHORARIOTURMA>
                        <IDTURMADISC>{row['IDTURMADISC']}</IDTURMADISC>
                        <RA>{row['RA']}</RA>
                        <DATA>{row['DATA']}</DATA>
                        <PRESENCA>A</PRESENCA>
                    </SFREQUENCIA>
                    <PARAMS>
                        <CODCOLIGADA>{row['CODCOLIGADA']}</CODCOLIGADA>
                        <IDTURMADISC>{row['IDTURMADISC']}</IDTURMADISC>
                        <CODETAPA>1</CODETAPA>
                    </PARAMS>
                </EduFrequenciaDiaria>
            ]]></tot:XML>
            <tot:Contexto>CODCOLIGADA={row['CODCOLIGADA']}</tot:Contexto>
        </tot:SaveRecord>
    </soapenv:Body>
</soapenv:Envelope>"""

# ======================================
# Função de registro de faltas
# ======================================
def registrar_faltas(tabela_dados):
    """
    Envia um XML por vez ao TOTVS, registrando a falta (PRESENCA=A).
    """
    logging.debug("Iniciando a função registrar_faltas")
    erros = []
    xmls_enviados = []
    
    for idx, row in tabela_dados.iterrows():
        logging.debug(f"Iniciando o processamento para RA {row['RA']}")
        try:
            envelope = gerar_xml(row)
            logging.debug(f"Envelope gerado para RA {row['RA']}: {envelope[:100]}...")

            response = requests.post(
                "https://raizeducacao160286.rm.cloudtotvs.com.br:8051/wsDataServer/IwsDataServer",
                data=envelope.encode("utf-8"),
                headers={
                    "Content-Type": "text/xml; charset=utf-8",
                    "SOAPAction": "http://www.totvs.com/IwsDataServer/SaveRecord"
                },
                auth=HTTPBasicAuth(USERNAME, PASSWORD),
                verify=False
            )
            logging.debug(f"Resposta HTTP para RA {row['RA']}: {response.status_code}")

            if response.status_code not in (200, 202):
                error_msg = f"Erro RA {row['RA']}: {response.status_code} - {response.text}"
                logging.error(error_msg)
                erros.append(error_msg)
            else:
                xmls_enviados.append(envelope)
                logging.debug(f"XML enviado com sucesso para RA {row['RA']}")
        
        except Exception as e:
            error_msg = f"Falha crítica RA {row['RA']}: {str(e)}"
            logging.exception(error_msg)
            erros.append(error_msg)

        # Pequeno delay para evitar sobrecarregar o servidor TOTVS
        time.sleep(0.5)
    
    logging.debug("Finalização da função registrar_faltas")
    return erros, xmls_enviados

# ======================================
# Interface Streamlit
# ======================================
st.title("📋 Lançamento de Faltas")

# Seleção da filial
filial_selecionada = st.selectbox(
    "🏫 Filial:",
    [f"{f['NOMEFANTASIA']} (Filial {f['CODFILIAL']})" for f in filiais]
)
filial_info = next(
    (f for f in filiais if f"Filial {f['CODFILIAL']}" in filial_selecionada),
    None
)

if filial_info:
    codcoligada = filial_info["CODCOLIGADA"]
    codfilial   = filial_info["CODFILIAL"]

    # Consulta turmas
    turmas = obter_turmas(codcoligada, codfilial)
    if isinstance(turmas, list) and len(turmas) > 0:
        # Data e cálculo do dia da semana
        data_selecionada = st.date_input("📅 Data:", datetime.today())
        dia_semana = data_selecionada.weekday() + 2  # Python: seg=0 => TOTVS: seg=2, etc

        # Selecionar turmas
        turmas_selecionadas = st.multiselect(
            "🎯 Turmas:",
            [t["CODTURMA"] for t in turmas]
        )

        # Se há turmas selecionadas, buscar alunos
        if turmas_selecionadas:
            alunos_por_turma = {}
            for codturma in turmas_selecionadas:
                alunos_turma = obter_alunos_turma(codcoligada, codfilial, codturma)
                if alunos_turma:
                    alunos_por_turma[codturma] = alunos_turma

            # Exibir lista de alunos com checkboxes
            st.markdown("### 👩‍🎓 Alunos por Turma")
            alunos_faltosos = []
            for codturma, lista_alunos in alunos_por_turma.items():
                st.subheader(f"Turma {codturma}")
                for aluno in lista_alunos:
                    label_aluno = f"{aluno['NOME']} - {aluno['RA']}"
                    if st.checkbox(label_aluno, key=f"{codturma}_{aluno['RA']}"):
                        alunos_faltosos.append(aluno)

            # Botão para lançar faltas
            if st.button("🚀 Lançar Faltas"):
                if alunos_faltosos:
                    # Observação: se o usuário selecionou múltiplas turmas, o ideal
                    # seria laçar as faltas turma a turma ou mesclar os dados.
                    # Exemplo simplificado: processa faltas para a PRIMEIRA turma
                    # do array "turmas_selecionadas".
                    codturma_para_faltas = turmas_selecionadas[0]

                    faltas = obter_faltas_por_aluno(
                        codcoligada, codfilial,
                        codturma_para_faltas,
                        alunos_faltosos,
                        dia_semana,
                        data_selecionada
                    )
                    tabela_dados = organizar_dados_para_xml(
                        faltas,
                        data_selecionada,
                        codcoligada,
                        codfilial,
                        codturma_para_faltas,
                        dia_semana
                    )
                    erros, xmls = registrar_faltas(tabela_dados)
                    
                    if erros:
                        st.error("❌ Erros encontrados:\n" + "\n".join(erros))
                    else:
                        st.success(f"✅ {len(xmls)} faltas registradas com sucesso!")
                        st.download_button(
                            "📥 Baixar XMLs",
                            "\n\n".join(xmls),
                            file_name="xmls_enviados.txt"
                        )
                else:
                    st.warning("⚠️ Nenhum aluno selecionado!")
        else:
            st.warning("⚠️ Nenhuma turma selecionada.")
    else:
        st.warning("⚠️ Nenhuma turma encontrada nesta filial.")
else:
    st.warning("⚠️ Selecione uma filial válida.")