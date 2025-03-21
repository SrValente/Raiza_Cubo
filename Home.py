import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Raiza - Gestão Escolar",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# URL do vídeo hospedado
video_url = "URL_DO_SEU_VIDEO_OTIMIZADO"

# CSS personalizado para o vídeo de fundo e texto sobreposto
st.markdown(f"""
    <style>
        .video-container {{
            position: relative;
            width: 100%;
            height: 60vh;
            overflow: hidden;
        }}
        .video-container video {{
            position: absolute;
            top: 50%;
            left: 50%;
            min-width: 100%;
            min-height: 100%;
            width: auto;
            height: auto;
            z-index: -1;
            transform: translate(-50%, -50%);
            background-size: cover;
        }}
        .video-overlay {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: white;
            font-size: 3rem;
            font-weight: bold;
            text-align: center;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.7);
        }}
    </style>
    <div class="video-container">
        <video autoplay loop muted playsinline>
            <source src="{video_url}" type="video/mp4">
            Seu navegador não suporta o elemento de vídeo.
        </video>
        <div class="video-overlay">Bem-vindo à Raiza</div>
    </div>
""", unsafe_allow_html=True)

# Conteúdo adicional da página
st.write("Conteúdo adicional abaixo do vídeo de boas-vindas.")


# Seção 1: Registro de Ocorrências e Gestão de Notas
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="card">
        <div class="card-content">
            <div class="card-title">🗉️ Registro de Ocorrências</div>
            <div class="card-description">
                Registre e acompanhe incidentes escolares:<br><br>
                • Histórico completo de alunos<br>
                • Lançamento de ocorrências<br>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Acessar Módulo", key="btn_ocorrencias"):
        st.switch_page("pages/1_📋_Ocorrências.py")

with col2:
    st.markdown("""
    <div class="card">
        <div class="card-content">
            <div class="card-title">✏️ Gestão de Notas</div>
            <div class="card-description">
                Sistema completo de avaliação:<br><br>
                • Lançamento por disciplina<br>
                • Análise de desempenho
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Acessar Módulo", key="btn_notas"):
        st.switch_page("pages/4_✏️_Notas.py")

# Seção 2: Grade Horária, Gestão de Frequência e Consulta de Planos
col3, col4, col5 = st.columns(3)

with col3:
    st.markdown("""
    <div class="card">
        <div class="card-content">
            <div class="card-title">🕒 Grade Horária</div>
            <div class="card-description">
                Gestão inteligente de horários:<br><br>
                • Visualização integrada<br>
                • Exportação automática
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Acessar Módulo", key="btn_grade"):
        st.switch_page("pages/2_🕒_Grade_Horária.py")

with col4:
    st.markdown("""
    <div class="card">
        <div class="card-content">
            <div class="card-title">🗓 Gestão de Frequência</div>
            <div class="card-description">
                Controle de presenças integrado:<br><br>
                • Lançamento em massa<br>
                • Lançamento retroativo
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Acessar Módulo", key="btn_faltas"):
        st.switch_page("pages/3_📅_Lançamento_Faltas.py")

with col5:
    st.markdown("""
    <div class="card">
        <div class="card-content">
            <div class="card-title">🛂 Consulta de Planos</div>
            <div class="card-description">
                Acesse informações sobre planos educacionais:<br><br>
                • Visualização dos alunos aderentes<br>
                • Exportação de listas
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Acessar Módulo", key="btn_planos"):
        st.switch_page("pages/5_🗂️_Consulta_Planos.py")

# Seção 3: Central do Aluno
st.markdown("""
<div class="card">
    <div class="card-content">
        <div class="card-title">💎 Central do Aluno (EM BREVE)</div>
        <div class="card-description">
            Portal completo para gestão de informações estudantis:<br><br>
            • Consulta de dados cadastrais<br>
            • Histórico escolar completo<br>
            • Notas online atualizadas<br>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

if st.button("Acessar Central do Aluno", key="btn_central"):
    st.switch_page("pages/0_👤_Central_Aluno.py")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 20px; color: #6b7280;">
    <p style="font-size: 0.9rem;">
        🚀 Versão 2.0 | Desenvolvido por <strong>BI</strong><br>
        📧 bi@raizaeducacao.com.br | 📞 (21) 98905-9301
    </p>
</div>
""", unsafe_allow_html=True)
