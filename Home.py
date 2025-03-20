import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Raiza - Gestão Escolar",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Customizado
st.markdown("""
<style>
    .video-container {
        position: relative;
        width: 100%;
        height: 50vh;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
    }
    .video-container iframe {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .overlay-title {
        position: absolute;
        font-size: 3rem;
        font-weight: bold;
        color: white;
        text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.7);
        text-align: center;
        z-index: 2;
    }
    .card {
        background: white;
        border-radius: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        margin-bottom: 25px;
        overflow: hidden;
        border: 1px solid #ddd;
    }
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# URL direta do vídeo no Google Drive
video_url = "https://drive.google.com/uc?export=download&id=12xRaWtQxREjgYuHn6VLHaoFgM7W7qPgr"

# Exibição do vídeo com título sobreposto
st.markdown(f"""
<div class="video-container">
    <iframe src="{video_url}" frameborder="0" allowfullscreen autoplay loop muted></iframe>
    <div class="overlay-title">Bem-vindo à Raiza</div>
</div>
""", unsafe_allow_html=True)

# Conteúdo Principal
st.markdown("""
    <div style="text-align: center; margin-bottom: 40px;">
        <h3 style="color: #4b5563; font-weight: 400;">
            Sua solução Integrada de Gestão Escolar
        </h3>
    </div>
""", unsafe_allow_html=True)

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
