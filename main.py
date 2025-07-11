import streamlit as st
import requests
import unicodedata

# ----------------------------------------
# CONFIGURAÇÃO
# ----------------------------------------

TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJ2aXBjb21tZXJjZSIsImF1ZCI6ImFwaS1hZG1pbiIsInN1YiI6IjZiYzQ4NjdlLWRjYTktMTFlOS04NzQyLTAyMGQ3OTM1OWNhMCIsInZpcGNvbW1lcmNlQ2xpZW50ZUlkIjpudWxsLCJpYXQiOjE3NTE5MjQ5MjgsInZlciI6MSwiY2xpZW50IjpudWxsLCJvcGVyYXRvciI6bnVsbCwib3JnIjoiMTYxIn0.yDCjqkeJv7D3wJ0T_fu3AaKlX9s5PQYXD19cESWpH-j3F_Is-Zb-bDdUvduwoI_RkOeqbYCuxN0ppQQXb1ArVg"
ORG_ID = "161"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "organizationid": ORG_ID,
    "sessao-id": "4ea572793a132ad95d7e758a4eaf6b09",
    "domainkey": "loja.shibata.com.br",
    "User-Agent": "Mozilla/5.0"
}

# ----------------------------------------
# FUNÇÃO PARA REMOVER ACENTOS
# ----------------------------------------

def remover_acentos(texto):
    if not texto:
        return ""
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower()

# ----------------------------------------
# INTERFACE STREAMLIT
# ----------------------------------------

st.set_page_config(page_title="Preço Shibata", page_icon="https://s3.amazonaws.com/shibata.com.br/files/tema/filial-1/header-site-omni.png?1752244176816")

# Remove o espaço superior padrão do Streamlit
st.markdown("""
    <style>
        main > div {
            padding-top: 0rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# Substitui o título com a imagem pequena no lugar do emoji
st.markdown("""
    <h3 style="display:flex; align-items:center;">
    <img src="https://s3.amazonaws.com/shibata.com.br/files/tema/filial-1/header-site-omni.png?1752244176816" width="100" style="margin-right:8px; background-color: white;"/>
    Preço Shibata
</h3>

""", unsafe_allow_html=True)

termo = st.text_input("🛒Digite o nome do produto:", "").strip().lower()

if termo:
    url = f"https://services.vipcommerce.com.br/api-admin/v1/org/{ORG_ID}/filial/1/centro_distribuicao/1/loja/buscas/produtos/termo/{termo}?page=1"
    response = requests.get(url, headers=HEADERS, timeout=10)

    if response.status_code == 200:
        data = response.json().get('data', {}).get('produtos', [])

        termo_sem_acento = remover_acentos(termo)
        palavras_termo = termo_sem_acento.split()

        produtos_filtrados = []
        for p in data:
            nome = remover_acentos(p.get('descricao', ''))
            if all(palavra in nome for palavra in palavras_termo):
                produtos_filtrados.append(p)

        def obter_preco(p):
            oferta_info = p.get('oferta') or {}
            preco_oferta = oferta_info.get('preco_oferta')
            if preco_oferta:
                return float(preco_oferta)
            return float(p.get('preco_original') or p.get('preco') or 0)

        data_ordenada = sorted(produtos_filtrados, key=obter_preco)

        st.markdown(f"<p style='font-size:14px;'>🔎 {len(data_ordenada)} produto(s) encontrado(s)</p>", unsafe_allow_html=True)

        if not data_ordenada:
            st.warning("Nenhum produto encontrado com esse nome.")

        for p in data_ordenada:
            preco = float(p.get('preco_original') or p.get('preco') or 0)
            unidade = p.get('unidade_sigla', '').lower()
            descricao = p.get('descricao', '')
            imagem = p.get('imagem', '')
            exibe_preco_original = p.get('exibe_preco_original', True)
            em_oferta = p.get('em_oferta', False)

            oferta_info = p.get('oferta') or {}
            preco_oferta = oferta_info.get('preco_oferta')
            preco_antigo = oferta_info.get('preco_antigo')

            imagem_url = f"https://produtos.vipcommerce.com.br/250x250/{imagem}"

            with st.container():
                col_img, col_info = st.columns([1, 3])

                with col_img:
                    st.image(imagem_url, width=100)

                with col_info:
                    st.markdown(f"<b>{descricao}</b>", unsafe_allow_html=True)

                    if em_oferta and preco_oferta and preco_antigo:
                        preco_oferta_val = float(preco_oferta)
                        preco_antigo_val = float(preco_antigo)
                        preco_original_val = float(p.get('preco_original') or preco_antigo_val)
                        unidade_str = f"/{unidade}" if unidade else ""

                        usar_preco_original = (preco_original_val > preco_antigo_val) and (unidade == 'kg')

                        try:
                            desconto = round(100 * (preco_antigo_val - preco_oferta_val) / preco_antigo_val)
                        except ZeroDivisionError:
                            desconto = 0

                        preco_oferta_str = f"{preco_oferta_val:.2f}".replace('.', ',')
                        preco_antigo_str = f"{preco_antigo_val:.2f}".replace('.', ',')
                        preco_original_str = f"{preco_original_val:.2f}".replace('.', ',')

                        if usar_preco_original:
                            st.markdown(f"""
                                <div style="line-height:1.3;">
                                    <p style="font-size:16px; margin:0;">
                                        <b>R$ {preco_original_str}{unidade_str}</b> 
                                        <span style="color:red;">-{desconto}% OFF</span>
                                    </p>
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            preco_oferta_exibe = f"R$ {preco_oferta_str}{unidade_str}"
                            preco_antigo_exibe = f"R$ {preco_antigo_str}{unidade_str}"
                            st.markdown(f"""
                                <div style="line-height:1.3;">
                                    <p style="font-size:16px; margin:0;">
                                        <b>{preco_oferta_exibe}</b> 
                                        <span style="color:red;">-{desconto}% OFF</span>
                                    </p>
                                    <p style="font-size:13px; color:gray; text-decoration: line-through; margin:0;">
                                        {preco_antigo_exibe}
                                    </p>
                                </div>
                            """, unsafe_allow_html=True)

                    elif exibe_preco_original:
                        preco_principal = f"R$ {preco:.2f}".replace('.', ',')
                        preco_principal = f"{preco_principal}/{unidade}" if unidade else preco_principal
                        st.markdown(f"<p style='font-size:16px; margin:0;'><b>{preco_principal}</b></p>", unsafe_allow_html=True)

                    else:
                        preco_principal = f"R$ {preco:.2f}".replace('.', ',')
                        preco_principal = f"{preco_principal}/{unidade}" if unidade else preco_principal
                        st.markdown(f"<p style='font-size:16px; margin:0;'><b>{preco_principal}</b></p>", unsafe_allow_html=True)

    else:
        st.error("Erro ao buscar produtos. Verifique o termo de busca ou a conexão.")
