import streamlit as st
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import urllib3
import pyodbc
import io
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(page_title="Central do Aluno", layout="wide")

# ------------------------------------------------------------------------------
# CONFIGURAÇÕES GERAIS
# ------------------------------------------------------------------------------
USERNAME = "p_heflo"
PASSWORD = "Q0)G$sW]rj"
BASE_URL = "https://raizeducacao160286.rm.cloudtotvs.com.br:8051/api/framework/v1/consultaSQLServer/RealizaConsulta"
SOAP_URL = "https://raizeducacao160286.rm.cloudtotvs.com.br:8051/wsDataServer/IwsDataServer"

ANO_LETIVO = 2023  # Ajuste conforme precisar
PERLET_COD = 2025  # Exemplo: 2025
TIPO_CURSO = 1     # Exemplo fixo

# ------------------------------------------------------------------------------
# FUNÇÕES (FILIAIS, TURMAS, ALUNOS, NOTAS, OCORRÊNCIAS, etc.)
# ------------------------------------------------------------------------------
def obter_filiais():
    return [
    {"NOMEFANTASIA": "COLÉGIO E CURSO AO CUBO BARRA",       "CODCOLIGADA": 5,  "CODFILIAL": 2},
    {"NOMEFANTASIA": "COLÉGIO E CURSO AO CUBO BOTAFOGO",     "CODCOLIGADA": 5,  "CODFILIAL": 2},
]

def obter_turmas(codcoligada, codfilial):
    url = f"{BASE_URL}/RAIZA.0005/0/S"
    params = {"parameters": f"CODCOLIGADA={codcoligada};CODFILIAL={codfilial}"}
    resp = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD), params=params, verify=False)
    if resp.status_code == 200:
        return resp.json()
    return []

def obter_alunos_turma(codcoligada, codfilial, codturma):
    url = f"{BASE_URL}/RAIZA.0009/0/S"
    params = {"parameters": f"CODCOLIGADA={codcoligada};CODFILIAL={codfilial};CODTURMA={codturma}"}
    resp = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD), params=params, verify=False)
    if resp.status_code == 200:
        return resp.json()
    return []

def obter_notas_aluno(codcoligada, codfilial, codturma, ra):
    url = f"{BASE_URL}/RAIZA.0011/0/S"
    params_str = (
        f"CODCOLIGADA={codcoligada};CODFILIAL={codfilial};"
        f"CODTURMA={codturma};RA={ra};CODETAPA=%;PROVA=%"
    )
    resp = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD),
                        params={"parameters": params_str}, verify=False)
    if resp.status_code == 200:
        return resp.json()
    return []

def obter_ocorrencias_aluno(codcoligada, codfilial, ra):
    """
    Consulta RAIZA.0001 com CODCOLIGADA, CODFILIAL e RA.
    Retorna lista de ocorrências do aluno.
    """
    url = f"{BASE_URL}/RAIZA.0001/0/S"
    params_str = f"CODCOLIGADA={codcoligada};CODFILIAL={codfilial};RA={ra}"
    resp = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD),
                        params={"parameters": params_str}, verify=False)
    if resp.status_code == 200:
        return resp.json()
    return []

def obter_informacoes_complementares_aluno(codcoligada, codfilial, ra, anoletivo):
    """
    Chama RAIZA.0013, que deve retornar dados como Grade, Data Nasc, Pai/Mãe etc.
    Ajuste conforme sua configuração do TOTVS.
    """
    url = f"{BASE_URL}/RAIZA.0013/0/S"
    params_str = (
        f"CODCOLIGADA={codcoligada};CODFILIAL={codfilial};ANOLETIVO={anoletivo};RA={ra}"
    )
    resp = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD),
                        params={"parameters": params_str}, verify=False)
    if resp.status_code == 200:
        return resp.json()
    return []

# ------------------------------------------------------------------------------
# SOAP: Incluir Nova Ocorrência
# ------------------------------------------------------------------------------
def incluir_ocorrencia_soap(codcoligada, ra, idperlet, codperlet, grupo_ocorrencia, cod_ocorrencia_tipo,
                            data_ocorrencia_str, desc_grupo_ocor, desc_tipo_ocor,
                            tipo_curso, observacoes="", observacoes_internas=""):
    """
    Monta o XML e faz POST no TOTVS via SOAP (wsDataServer).
    Retorna (sucesso=True, msg=...) ou (False, msg=...).
    """

    obs_escapado = escape(observacoes)
    obs_int_escapado = escape(observacoes_internas)

    xml_data = f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tot="http://www.totvs.com/">
   <soapenv:Header/>
   <soapenv:Body>
      <tot:SaveRecord>
         <tot:DataServerName>EduOcorrenciaAlunoData</tot:DataServerName>
         <tot:XML><![CDATA[<EduOcorrenciaAluno>
   <SOcorrenciaAluno>
         <CODCOLIGADA>{codcoligada}</CODCOLIGADA>
         <IDOCORALUNO>-1</IDOCORALUNO>
         <RA>{ra}</RA>
         <CODOCORRENCIAGRUPO>{grupo_ocorrencia}</CODOCORRENCIAGRUPO>
         <CODOCORRENCIATIPO>{cod_ocorrencia_tipo}</CODOCORRENCIATIPO>
         <IDPERLET>{idperlet}</IDPERLET>
         <CODPERLET>{codperlet}</CODPERLET>
         <DATAOCORRENCIA>{data_ocorrencia_str}</DATAOCORRENCIA>
         <DESCGRUPOOCOR>{desc_grupo_ocor}</DESCGRUPOOCOR>
         <DESCTIPOOCOR>{desc_tipo_ocor}</DESCTIPOOCOR>
         <CODTIPOCURSO>{tipo_curso}</CODTIPOCURSO>
         <DISPONIVELWEB>0</DISPONIVELWEB>
         <RESPONSAVELCIENTE>0</RESPONSAVELCIENTE>
         <OBSERVACOES>{obs_escapado}</OBSERVACOES>
         <OBSERVACOESINTERNAS>{obs_int_escapado}</OBSERVACOESINTERNAS>
         <POSSUIARQUIVO>N</POSSUIARQUIVO>
   </SOcorrenciaAluno>
</EduOcorrenciaAluno>]]></tot:XML>
         <tot:Contexto>CODCOLIGADA={codcoligada}</tot:Contexto>
      </tot:SaveRecord>
   </soapenv:Body>
</soapenv:Envelope>"""

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "http://www.totvs.com/IwsDataServer/SaveRecord"
    }

    try:
        response = requests.post(
            SOAP_URL,
            data=xml_data.encode('utf-8'),
            headers=headers,
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            verify=False
        )
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            fault = root.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Fault')
            if fault is not None:
                faultstring = fault.find('faultstring').text
                return (False, f"Erro TOTVS (SOAP Fault): {faultstring}")
            else:
                return (True, "Ocorrência registrada com sucesso!")
        else:
            return (False, f"Erro HTTP ao enviar a requisição: {response.status_code}\n{response.text}")
    except Exception as e:
        return (False, f"Exceção ao chamar SOAP TOTVS: {e}")

# ------------------------------------------------------------------------------
# Exemplo para obter IDPERLET (caso seja necessário)
# ------------------------------------------------------------------------------
def obter_id_perlet(codcoligada, codfilial, codperlet):
    codigo = "RAIZA.0008"
    url = f"{BASE_URL}/{codigo}/0/S"
    params_str = f"CODCOLIGADA={codcoligada};CODFILIAL={codfilial};CODPERLET={codperlet}"
    resp = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD),
                        params={"parameters": params_str}, verify=False)
    if resp.status_code == 200:
        dados = resp.json() or []
        if len(dados) > 0:
            return dados[0].get("IDPERLET")
    return None

# ------------------------------------------------------------------------------
# PyODBC para foto
# ------------------------------------------------------------------------------
import pyodbc

def conectar_banco():
    conn = pyodbc.connect(
        "DRIVER={SQL Server};"
        "SERVER=RAIZDB01;"
        "DATABASE=PBI_RAIZ;"
        "UID=bi.raiz;"
        "PWD=PbI#2023;"
    )
    return conn

def obter_foto_aluno(codcoligada, codfilial, ra):
    conn = conectar_banco()
    query = f"""
    SELECT FOTO.IMAGEM AS FOTO
    FROM TOTVS.[C3U7RQ_160286_RM_PD].[dbo].SALUNO A (NOLOCK)
    INNER JOIN (
        SELECT A.RA, I.IMAGEM
        FROM TOTVS.[C3U7RQ_160286_RM_PD].[dbo].SALUNO A (NOLOCK)
        INNER JOIN TOTVS.[C3U7RQ_160286_RM_PD].[dbo].PPESSOA P (NOLOCK)
            ON A.CODPESSOA = P.CODIGO
        LEFT JOIN TOTVS.[C3U7RQ_160286_RM_PD].[dbo].GIMAGEM I (NOLOCK)
            ON P.IDIMAGEM = I.ID
    ) FOTO ON FOTO.RA = A.RA
    WHERE A.RA = '{ra}'
    """
    try:
        df = pd.read_sql(query, conn)
        conn.close()
        if not df.empty and df.iloc[0]["FOTO"] is not None:
            return df.iloc[0]["FOTO"]
    except Exception as e:
        st.error(f"Erro ao obter foto: {e}")
    return None

# ------------------------------------------------------------------------------
# CONTROLE DE TELA
# ------------------------------------------------------------------------------
if "tela" not in st.session_state:
    st.session_state["tela"] = "selecao"
    st.session_state["dados_aluno"] = {}
    st.session_state["ocorrencia_form"] = False

def voltar_para_selecao():
    st.session_state["tela"] = "selecao"
    st.session_state["dados_aluno"] = {}
    st.session_state["ocorrencia_form"] = False
    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

# ------------------------------------------------------------------------------
# TELA DE SELEÇÃO
# ------------------------------------------------------------------------------
def tela_selecao():
    st.title("Central do Aluno - Seleção")

    filiais_data = obter_filiais()
    filial_nomes = [f"{f['NOMEFANTASIA']} (Filial {f['CODFILIAL']})" for f in filiais_data]
    filial_sel = st.selectbox("Selecione a Filial:", filial_nomes)
    if not filial_sel:
        st.stop()

    f_info = next((f for f in filiais_data if f"{f['NOMEFANTASIA']} (Filial {f['CODFILIAL']})" == filial_sel), None)
    codcoligada = f_info["CODCOLIGADA"]
    codfilial = f_info["CODFILIAL"]

    turmas = obter_turmas(codcoligada, codfilial)
    if not turmas:
        st.warning("Nenhuma turma encontrada.")
        st.stop()
    lista_turmas = sorted({t["CODTURMA"] for t in turmas if "CODTURMA" in t})
    turma_sel = st.selectbox("Selecione a Turma:", lista_turmas)
    if not turma_sel:
        st.stop()

    alunos = obter_alunos_turma(codcoligada, codfilial, turma_sel)
    if not alunos:
        st.warning("Nenhum aluno encontrado.")
        st.stop()
    lista_alunos = [f"{a['RA']} - {a['NOME']}" for a in alunos]
    aluno_sel = st.selectbox("Selecione o Aluno:", lista_alunos)
    if not aluno_sel:
        st.stop()

    if st.button("Carregar Central do Aluno"):
        ra_escolhido = aluno_sel.split(" - ")[0]
        st.session_state["dados_aluno"] = {
            "codcoligada": codcoligada,
            "codfilial": codfilial,
            "filial_nome": filial_sel,
            "turma": turma_sel,
            "ra": ra_escolhido,
            "nome_aluno": aluno_sel.split(" - ")[1]
        }
        st.session_state["tela"] = "detalhes"
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()

# ------------------------------------------------------------------------------
# TELA DE DETALHES
# ------------------------------------------------------------------------------
def tela_detalhes():
    dados = st.session_state.get("dados_aluno", {})
    if not dados:
        st.warning("Nenhum aluno selecionado.")
        voltar_para_selecao()
        st.stop()

    st.title("Central do Aluno - Detalhes")
    if st.button("Voltar"):
        voltar_para_selecao()

    codcoligada = dados["codcoligada"]
    codfilial = dados["codfilial"]
    turma = dados["turma"]
    ra = dados["ra"]
    nome_aluno = dados["nome_aluno"]
    filial_exib = dados["filial_nome"]

    # Exibe 3 colunas: Foto, Dados do Aluno, (vazio ou complementares)
    col1, col2, col3 = st.columns([1,2,2])
    with col1:
        foto_bin = obter_foto_aluno(codcoligada, codfilial, ra)
        if foto_bin:
            st.image(foto_bin, caption=f"Foto de {nome_aluno}", width=200)
        else:
            st.info("Sem foto cadastrada.")
    with col2:
        st.markdown(f"**Nome:** {nome_aluno}")
        st.markdown(f"**RA:** {ra}")
        st.markdown(f"**Filial:** {filial_exib}")
        st.markdown(f"**Turma:** {turma}")

        # Exemplo de dados complementares
        info_compl = obter_informacoes_complementares_aluno(codcoligada, codfilial, ra, ANO_LETIVO)
        df_compl = pd.DataFrame(info_compl)
        if not df_compl.empty:
            row = df_compl.iloc[0]
            grade_val = row.get("GRADE", "")
            st.markdown(f"**Grade:** {grade_val}")
        else:
            st.markdown("**Grade:** -")

    st.markdown("---")

    # == NOTAS DO ALUNO
    st.subheader("Notas do Aluno")
    notas_data = obter_notas_aluno(codcoligada, codfilial, turma, ra)
    df_notas = pd.DataFrame(notas_data)

    if df_notas.empty:
        st.warning("Nenhuma nota encontrada.")
    else:
        if "NOTAPROVA" in df_notas.columns:
            df_notas["NOTAPROVA"] = pd.to_numeric(df_notas["NOTAPROVA"], errors="coerce").fillna(0)
        df_sum = df_notas.groupby(["DISCIPLINA", "ETAPA"], as_index=False)["NOTAPROVA"].sum()
        pivot_sum = df_sum.pivot(index="DISCIPLINA", columns="ETAPA", values="NOTAPROVA").fillna(0)

        st.markdown("#### Visão Geral (Soma das Notas por Disciplina e Etapa)")
        st.dataframe(pivot_sum, use_container_width=True)

        st.markdown("#### Detalhes por Disciplina (Provas)")
        disciplinas_unicas = sorted(df_notas["DISCIPLINA"].unique())
        for disc in disciplinas_unicas:
            df_disc = df_notas[df_notas["DISCIPLINA"] == disc].copy()
            if df_disc.empty:
                continue
            with st.expander(f"Disciplina: {disc}", expanded=False):
                pivot_det = df_disc.pivot_table(
                    index="ETAPA",
                    columns="PROVA",
                    values="NOTAPROVA",
                    aggfunc="sum"
                ).fillna(0)
                st.dataframe(pivot_det, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 2 Disciplinas com Menores Notas (Média) - somente 'prova'")
        df_only_provas = df_notas[df_notas["PROVA"].str.contains("prova", case=False, na=False)]
        if df_only_provas.empty:
            st.info("Não há nenhuma linha com 'prova' no nome para calcular as menores médias.")
        else:
            if "PROFESSOR" in df_only_provas.columns:
                df_medias = df_only_provas.groupby(["DISCIPLINA", "PROFESSOR"], as_index=False)["NOTAPROVA"].mean()
                df_medias = df_medias.loc[df_medias["NOTAPROVA"] > 0]
                if df_medias.empty:
                    st.info("Não há notas > 0 para destacar (somente 'prova').")
                else:
                    df_menores = df_medias.nsmallest(2, "NOTAPROVA")
                    for _, rowm in df_menores.iterrows():
                        st.write(f"**{rowm['DISCIPLINA']}** (Prof: {rowm['PROFESSOR']}) – Média: {rowm['NOTAPROVA']:.2f}")
            else:
                df_medias = df_only_provas.groupby("DISCIPLINA", as_index=False)["NOTAPROVA"].mean()
                df_medias = df_medias.loc[df_medias["NOTAPROVA"] > 0]
                if df_medias.empty:
                    st.info("Não há notas > 0 para destacar (somente 'prova').")
                else:
                    df_menores = df_medias.nsmallest(2, "NOTAPROVA")
                    for _, rowm in df_menores.iterrows():
                        st.write(f"**{rowm['DISCIPLINA']}** – Média: {rowm['NOTAPROVA']:.2f}")

    st.markdown("---")

    # == OCORRÊNCIAS DO ALUNO
    st.subheader("Ocorrências do Aluno")
    # Agora SEM botão de consulta, já carrega automaticamente:
    ocorr = obter_ocorrencias_aluno(codcoligada, codfilial, ra)
    if not ocorr:
        st.info("Nenhuma ocorrência registrada.")
    else:
        df_ocorr = pd.DataFrame(ocorr)
        if df_ocorr.empty:
            st.info("Nenhuma ocorrência registrada.")
        else:
            st.dataframe(df_ocorr, use_container_width=True)

    # Botão para exibir formulário de nova ocorrência
    if st.button("Nova Ocorrência"):
        st.session_state["ocorrencia_form"] = True

    # Se st.session_state["ocorrencia_form"] está True, exibe o formulário
    if st.session_state["ocorrencia_form"]:
        st.markdown("### Registrar Nova Ocorrência")

        # Tenta obter o IDPERLET
        id_perlet = obter_id_perlet(codcoligada, codfilial, PERLET_COD)
        if not id_perlet:
            st.error("IDPERLET não encontrado para CODPERLET=2025 (Exemplo). Regra de negócio.")
        else:
            # Campos do formulário
            desc_tipo_ocor = st.selectbox("Tipo de Ocorrência:", ["Advertência", "Suspensão", "Outros"])
            if desc_tipo_ocor == "Advertência":
                cod_ocor_tipo = 30
            elif desc_tipo_ocor == "Suspensão":
                cod_ocor_tipo = 40
            else:
                cod_ocor_tipo = 99  # Exemplos

            observacoes_input = st.text_area("Observações")
            observacoes_internas_input = st.text_area("Observações Internas")

            if st.button("Incluir Ocorrência"):
                data_atual = datetime.now().strftime("%Y-%m-%dT%H:%M:%S-03:00")
                grupo_ocorrencia = 4
                desc_grupo = "Grupo Comportamental"

                ok, msg = incluir_ocorrencia_soap(
                    codcoligada=codcoligada,
                    ra=ra,
                    idperlet=id_perlet,
                    codperlet=PERLET_COD,
                    grupo_ocorrencia=grupo_ocorrencia,
                    cod_ocorrencia_tipo=cod_ocor_tipo,
                    data_ocorrencia_str=data_atual,
                    desc_grupo_ocor=desc_grupo,
                    desc_tipo_ocor=desc_tipo_ocor,
                    tipo_curso=TIPO_CURSO,
                    observacoes=observacoes_input,
                    observacoes_internas=observacoes_internas_input
                )
                if ok:
                    st.success(msg)
                    st.session_state["ocorrencia_form"] = False
                    # Recarregar ocorrência
                    st.experimental_rerun()
                else:
                    st.error(msg)

def main():
    if st.session_state["tela"] == "selecao":
        tela_selecao()
    elif st.session_state["tela"] == "detalhes":
        tela_detalhes()

if __name__ == "__main__":
    main()