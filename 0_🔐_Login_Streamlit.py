# 0_🔐_Login_Streamlit.py

import streamlit as st
import streamlit_authenticator as stauth
import uuid
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.mime.text import MIMEText

# 🔹 Configurações do SMTP para envio do token (Google Workspace)
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = 'bi@raizeducacao.com.br'
SMTP_PASSWORD = 'jqby exvy ripr ptwd'

# 🔹 ID da planilha do Google Sheets e nome da aba
SHEET_ID = '12WKci7NEdQgDP9lJeZP6c18hWVlE6SQpjC9LDbv_6HM'
ABA = 'usuarios'

# 🔹 Conecta ao Google Sheets
@st.cache_resource
def conectar_planilha():
    escopo = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credenciais = ServiceAccountCredentials.from_json_keyfile_name('credenciais.json', escopo)
    cliente = gspread.authorize(credenciais)
    return cliente.open_by_key(SHEET_ID).worksheet(ABA)

# 🔹 Carrega usuários da planilha
def carregar_usuarios():
    aba = conectar_planilha()
    dados = aba.get_all_records()
    return {linha['email']: linha['senha_hash'] for linha in dados}

# 🔹 Adiciona novo usuário na planilha
def salvar_usuario(email, senha_hash):
    aba = conectar_planilha()
    aba.append_row([email, senha_hash])

# 🔹 Lista de e-mails autorizados (pode ser separada em aba própria se desejar)
emails_autorizados = ['joao@empresa.com', 'maria@empresa.com', 'ana@empresa.com']

st.set_page_config(page_title="Login - Raiz Educação", page_icon="🔐")
st.title("🔐 Acesso ao Sistema")

if "etapa" not in st.session_state:
    st.session_state.etapa = "email"

usuarios = carregar_usuarios()

# 🔹 Etapa 1: Email
if st.session_state.etapa == "email":
    email = st.text_input("Digite seu e-mail institucional")
    if st.button("Continuar"):
        if email not in emails_autorizados:
            st.error("E-mail não autorizado")
        elif email in usuarios:
            st.session_state.email = email
            st.session_state.etapa = "login"
        else:
            token = str(uuid.uuid4())[:6].upper()
            st.session_state.token_gerado = token
            st.session_state.email = email
            st.session_state.etapa = "verificacao"

            # Envia e-mail com token via Gmail Workspace
            msg = MIMEText(f"Olá!\n\nSeu código de verificação é: {token}\n\nEquipe Raiz Educação")
            msg['Subject'] = 'Código de Verificação - Acesso Raiz'
            msg['From'] = SMTP_USER
            msg['To'] = email

            try:
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    server.starttls()
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.send_message(msg)
                st.success("Código enviado para o e-mail")
            except Exception as e:
                st.error(f"Erro ao enviar e-mail: {str(e)}")

# 🔹 Etapa 2: Verificação de token e criação de senha
elif st.session_state.etapa == "verificacao":
    st.info(f"Um código foi enviado para: {st.session_state.email}")
    token_digitado = st.text_input("Digite o código recebido")
    nova_senha = st.text_input("Crie sua senha", type="password")
    confirmar_senha = st.text_input("Confirme sua senha", type="password")

    if st.button("Criar acesso"):
        if token_digitado != st.session_state.token_gerado:
            st.error("Código inválido")
        elif nova_senha != confirmar_senha:
            st.error("As senhas não coincidem")
        else:
            senha_hash = stauth.Hasher([nova_senha]).generate()[0]
            salvar_usuario(st.session_state.email, senha_hash)
            st.success("Senha criada com sucesso. Faça o login.")
            st.session_state.etapa = "login"
            usuarios = carregar_usuarios()

# 🔹 Etapa 3: Login com authenticator
elif st.session_state.etapa == "login":
    emails = list(usuarios.keys())
    senhas = list(usuarios.values())
    nomes = [e.split('@')[0].capitalize() for e in emails]

    authenticator = stauth.Authenticate(nomes, emails, senhas, 'raiz_cookie', 'raiz_sig', 30)
    nome, status, username = authenticator.login("Login", "main")

    if status:
        st.success(f"Bem-vindo, {nome}!")
        # Aqui vai o conteúdo protegido
        st.markdown("---")
        st.header("🎓 Painel da Raiz Educação")
        st.write("Conteúdo confidencial...")

    elif status is False:
        st.error("Senha incorreta")
    elif status is None:
        st.warning("Digite suas credenciais para continuar")
