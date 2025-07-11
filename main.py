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

st.markdown("""
    <style>
        .block-container { padding-top: 0rem; }
        footer {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        div, span, strong, small { font-size: 0.75rem !important; }
        img { max-width: 100px; height: auto; }

        .product-container {
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: nowrap;
        }

        .product-image {
            min-width: 80px;
            max-width: 80px;
            flex-shrink: 0;
        }

        .product-info {
            flex-grow: 1;
            min-width: 150px;
        }

        @media (max-width: 768px) {
            .product-container {
                flex-direction: row;
                align-items: center;
                flex-wrap: nowrap;
            }
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h5>🛒 Preço Nagumo</h5>", unsafe_allow_html=True)
""", unsafe_allow_html=True)

termo = st.text_input("🛒Digite o nome do produto:", "").strip().lower()

if termo:
    url = f"https://services.vipcommerce.com.br/api-admin/v1/org/{ORG_ID}/filial/1/centro_distribuicao/1/loja/buscas/produtos/termo/{termo}?page=1"
    response = requests.get(url, headers=HEADERS, timeout=10)

    if response.status_code == 200:
        data = response.json().get('data', {}).get('produtos', [])

        termo_sem_acento = remover_acentos(termo)
        palavras_termo = termo_sem_acento.split()

        produtos_filtrados = [p for p in data if all(palavra in remover_acentos(p.get('descricao', '')) for palavra in palavras_termo)]

        def obter_preco(p):
            oferta_info = p.get('oferta') or {}
            preco_oferta = oferta_info.get('preco_oferta')
            return float(preco_oferta) if preco_oferta else float(p.get('preco_original') or p.get('preco') or 0)

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

            preco_html = ""

            if em_oferta and preco_oferta and preco_antigo:
                preco_oferta_val = float(preco_oferta)
                preco_antigo_val = float(preco_antigo)
                unidade_str = f"/{unidade}" if unidade else ""
                desconto = round(100 * (preco_antigo_val - preco_oferta_val) / preco_antigo_val) if preco_antigo_val else 0
                preco_oferta_str = f"{preco_oferta_val:.2f}".replace('.', ',')
                preco_antigo_str = f"{preco_antigo_val:.2f}".replace('.', ',')

                preco_html = f"""
                    <div style='line-height:1.3;'>
                        <p style='font-size:0.85em; margin:0;'>
                            <b>R$ {preco_oferta_str}{unidade_str}</b>
                            <span style='color:red;'>-{desconto}% OFF</span>
                        </p>
                        <p style='font-size:0.85em; color:gray; text-decoration: line-through; margin:0;'>
                            R$ {preco_antigo_str}{unidade_str}
                        </p>
                    </div>
                """

            elif exibe_preco_original:
                preco_principal = f"R$ {preco:.2f}".replace('.', ',')
                preco_principal = f"{preco_principal}/{unidade}" if unidade else preco_principal
                preco_html = f"<p style='font-size:0.85em; margin:0;'><b>{preco_principal}</b></p>"

            else:
                preco_principal = f"R$ {preco:.2f}".replace('.', ',')
                preco_principal = f"{preco_principal}/{unidade}" if unidade else preco_principal
                preco_html = f"<p style='font-size:0.85em; margin:0;'><b>{preco_principal}</b></p>"

            st.markdown(f"""
                <div class='product-container'>
                    <div class='product-image'>
                        <img src='{imagem_url}' width='80'/>
                    </div>
                    <div class='product-info'>
                        <div style='margin-bottom: 4px;'><b>{descricao}</b></div>
                        {preco_html}
                    </div>
                </div>
            """, unsafe_allow_html=True)

    else:
        st.error("Erro ao buscar produtos. Verifique o termo de busca ou a conexão.")
