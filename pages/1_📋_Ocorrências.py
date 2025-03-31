import streamlit as st
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title="Consulta de Ocorrências - TOTVS", layout="wide")

# Configurações do Gmail
GMAIL_USER = "bi@raizeducacao.com.br"
GMAIL_PASSWORD = "jqby exvy ripr ptwd"

def enviar_email(destinatarios, assunto, corpo):
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = ", ".join(destinatarios)
        msg['Subject'] = assunto
        msg.attach(MIMEText(corpo, 'plain'))
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"❌ Falha no envio do e-mail: {e}")
        return False

USERNAME = "p_heflo"
PASSWORD = "Q0)G$sW]rj"
SOAP_URL = "https://raizeducacao160286.rm.cloudtotvs.com.br:8051/wsDataServer/IwsDataServer"
BASE_URL = "https://raizeducacao160286.rm.cloudtotvs.com.br:8051/api/framework/v1/consultaSQLServer/RealizaConsulta"

st.title("🔍 Consulta de Ocorrências - TOTVS")

# Listagem de filiais
filiais = [
    {"NOMEFANTASIA": "COLÉGIO E CURSO AO CUBO BARRA", "CODCOLIGADA": 5, "CODFILIAL": 2},
    {"NOMEFANTASIA": "COLÉGIO E CURSO AO CUBO BOTAFOGO", "CODCOLIGADA": 5, "CODFILIAL": 5},
]

filiais_opcoes = {f"{f['NOMEFANTASIA']} ({f['CODFILIAL']})": (f['CODCOLIGADA'], f['CODFILIAL']) for f in filiais}
filial_escolhida = st.selectbox("Selecione a Filial:", list(filiais_opcoes.keys()))
codcoligada, codfilial = filiais_opcoes.get(filial_escolhida, (None, None))

def consultar_api(codigo, codcoligada=None, codfilial=None, ra=None, codperlet=None, ra_nome=None):
    if codigo == "RAIZA.0008":
        parametros = f"CODCOLIGADA={codcoligada};CODFILIAL={codfilial};CODPERLET={codperlet}"
    elif codigo == "RAIZA.0001":
        parametros = f"CODCOLIGADA={codcoligada};CODFILIAL={codfilial};RA={ra}"
    elif codigo == "RAIZA.0002":
        ra_nome = "%" if not ra_nome else ra_nome
        parametros = f"CODCOLIGADA={codcoligada};CODFILIAL={codfilial};RA_NOME={ra_nome}"
    elif codigo == "RAIZA.0017":
        parametros = f"CODCOLIGADA={codcoligada};CODFILIAL={codfilial};RA={ra}"
    else:
        parametros = ""

    url = f"{BASE_URL}/{codigo}/0/S"
    try:
        response = requests.get(
            url,
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            params={"parameters": parametros},
            verify=False
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"❌ Erro na requisição: {e}")
        return None

# Buscar IDPERLET
id_perlet = None
if codcoligada and codfilial:
    perlet_info = consultar_api("RAIZA.0008", codcoligada=codcoligada, codfilial=codfilial, codperlet=2025)
    id_perlet = perlet_info[0].get("IDPERLET") if perlet_info else None

# Selecionar Aluno
ra_aluno = None
if codcoligada and codfilial:
    alunos = consultar_api("RAIZA.0002", codcoligada=codcoligada, codfilial=codfilial, ra_nome="%")
    if alunos:
        alunos_opcoes = {a["RA_NOME"]: a["RA"] for a in alunos if "RA" in a and "RA_NOME" in a}
        if alunos_opcoes:
            aluno_selecionado = st.selectbox("Selecione o Aluno (RA - Nome):", list(alunos_opcoes.keys()))
            ra_aluno = alunos_opcoes[aluno_selecionado]

# Consulta de Ocorrências
if ra_aluno and codcoligada and codfilial:
    if st.button("🔎 Consultar Ocorrências"):
        ocorrencias = consultar_api("RAIZA.0001", codcoligada=codcoligada, codfilial=codfilial, ra=ra_aluno)
        if ocorrencias:
            st.success("✅ Consulta realizada com sucesso!")
            st.dataframe(pd.DataFrame(ocorrencias))
        else:
            st.warning("⚠ Nenhuma ocorrência encontrada.")

    if st.button("➕ Nova Ocorrência"):
        st.session_state["nova_ocorrencia"] = True

    if "nova_ocorrencia" in st.session_state:
        st.markdown("### 📝 Registrar Nova Ocorrência")
        descricao_tipo = st.selectbox("Selecione o Tipo de Ocorrência:", ["Advertência", "Suspensão", "Outros"])
        observacoes_input = st.text_area("Observações*", placeholder="Descreva os detalhes da ocorrência...")
        observacoes_internas_input = st.text_area("Observações Internas", placeholder="Registro para uso exclusivo da equipe pedagógica")
        enviar_email_check = st.checkbox("✉️ Enviar notificação por e-mail aos responsáveis")
        cod_ocorrencia_tipo = 30

        if st.button("✅ Concluir Inclusão da Ocorrência") and id_perlet:
            xml_data = f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tot="http://www.totvs.com/">
   <soapenv:Header/>
   <soapenv:Body>
      <tot:SaveRecord>
         <tot:DataServerName>EduOcorrenciaAlunoData</tot:DataServerName>
         <tot:XML><![CDATA[<EduOcorrenciaAluno>
   <SOcorrenciaAluno>
         <CODCOLIGADA>{codcoligada}</CODCOLIGADA>
         <IDOCORALUNO>-1</IDOCORALUNO>
         <RA>{ra_aluno}</RA>
         <CODOCORRENCIAGRUPO>4</CODOCORRENCIAGRUPO>
         <CODOCORRENCIATIPO>{cod_ocorrencia_tipo}</CODOCORRENCIATIPO>
         <IDPERLET>{id_perlet}</IDPERLET>
         <CODPERLET>2025</CODPERLET>
         <DATAOCORRENCIA>{datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")}</DATAOCORRENCIA>
         <DESCGRUPOOCOR>Grupo Comportamental</DESCGRUPOOCOR>
         <DESCTIPOOCOR>{descricao_tipo}</DESCTIPOOCOR>
         <CODTIPOCURSO>1</CODTIPOCURSO>
         <DISPONIVELWEB>0</DISPONIVELWEB>
         <RESPONSAVELCIENTE>0</RESPONSAVELCIENTE>
         <OBSERVACOES>{escape(observacoes_input)}</OBSERVACOES>
         <OBSERVACOESINTERNAS>{escape(observacoes_internas_input)}</OBSERVACOESINTERNAS>
         <POSSUIARQUIVO>N</POSSUIARQUIVO>
   </SOcorrenciaAluno>
</EduOcorrenciaAluno>]]></tot:XML>
         <tot:Contexto>CODCOLIGADA={codcoligada}</tot:Contexto>
      </tot:SaveRecord>
   </soapenv:Body>
</soapenv:Envelope>"""

            response = requests.post(
                SOAP_URL,
                data=xml_data.encode('utf-8'),
                headers={"Content-Type": "text/xml; charset=utf-8", "SOAPAction": "http://www.totvs.com/IwsDataServer/SaveRecord"},
                auth=HTTPBasicAuth(USERNAME, PASSWORD),
                verify=False
            )

            if response.status_code == 200:
                st.success("✅ Ocorrência registrada com sucesso!")
                del st.session_state["nova_ocorrencia"]

                if enviar_email_check:
                    emails_responsaveis = consultar_api("RAIZA.0017", codcoligada=codcoligada, codfilial=codfilial, ra=ra_aluno)
                    if emails_responsaveis:
                        destinatarios = set()
                        for linha in emails_responsaveis:
                            for campo in ["EMAIL_RESP_FIN", "EMAIL_RESP_ACAD", "EMAIL_PAI_1", "EMAIL_PAI_2", "EMAIL_MAE_1", "EMAIL_MAE_2"]:
                                if linha.get(campo):
                                    destinatarios.add(linha[campo].strip())
                        
                        if destinatarios:
                            corpo_email = f"""
                            COMUNICADO OFICIAL - RAÍZ EDUCAÇÃO

                            Prezado Responsável,

                            Comunicamos que foi registrada uma ocorrência referente ao(a) aluno(a): 
                            {aluno_selecionado}

                            Detalhes:
                            - Tipo de Ocorrência: {descricao_tipo}
                            - Data do Registro: {datetime.now().strftime('%d/%m/%Y %H:%M')}
                            - Observações: 
                            {observacoes_input}

                            Este registro tem como objetivo manter a transparência e o acompanhamento 
                            do desenvolvimento do aluno em nosso ambiente educacional.

                            Atenciosamente,
                            Coordenação Pedagógica
                            RAÍZ EDUCAÇÃO
                            """
                            
                            if enviar_email(destinatarios, "Registro de Ocorrência - RAÍZ EDUCAÇÃO", corpo_email):
                                st.success(f"📧 Notificação enviada para: {', '.join(destinatarios)}")
            else:
                st.error(f"❌ Erro ao registrar ocorrência: {response.text}")
