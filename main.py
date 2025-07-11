import streamlit as st
import requests
import unicodedata

TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJ2aXBjb21tZXJjZSIsImF1ZCI6ImFwaS1hZG1pbiIsInN1YiI6IjZiYzQ4NjdlLWRjYTktMTFlOS04NzQyLTAyMGQ3OTM1OWNhMCIsInZpcGNvbW1lcmNlQ2xpZW50ZUlkIjpudWxsLCJpYXQiOjE3NTE5MjQ5MjgsInZlciI6MSwiY2xpZW50IjpudWxsLCJvcGVyYXRvciI6bnVsbCwib3JnIjoiMTYxIn0.yDCjqkeJv7D3wJ0T_fu3AaKlX9s5PQYXD19cESWpH-j3F_Is-Zb-bDdUvduwoI_RkOeqbYCuxN0ppQQXb1ArVg"
ORG_ID = "161"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "organizationid": ORG_ID,
    "sessao-id": "4ea572793a132ad95d7e758a4eaf6b09",
    "domainkey": "loja.shibata.com.br",
    "User-Agent": "Mozilla/5.0"
}

def remover_acentos(texto):
    if not texto:
        return ""
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower()

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

        /* Bordas arredondadas nas imagens */
        .product-image img {
            border-radius: 8px;
        }

        .product-info {
            flex-grow: 1;
            min-width: 150px;
        }

        hr.product-separator {
            border: none;
            border-top: 1px solid #ccc;
            margin: 10px 0;
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

            if em_oferta and preco_oferta and preco_antigo and unidade == 'kg':
                preco_original_val = float(p.get('preco_original') or 0)
                preco_oferta_val = float(preco_oferta)
                preco_antigo_val = float(preco_antigo)
                desconto = round(100 * (preco_antigo_val - preco_oferta_val) / preco_antigo_val) if preco_antigo_val else 0
                preco_html = f"<b>R$ {preco_original_val:.2f}".replace('.', ',') + f"/{unidade} <span style='color:red;'>-{desconto}% OFF</span></b>"
            else:
                if em_oferta and preco_oferta and preco_antigo:
                    unidade_str = f"/{unidade}" if unidade else ""
                    preco_oferta_val = float(preco_oferta)
                    preco_antigo_val = float(preco_antigo)
                    desconto = round(100 * (preco_antigo_val - preco_oferta_val) / preco_antigo_val) if preco_antigo_val else 0
                    preco_oferta_str = f"R$ {preco_oferta_val:.2f}".replace('.', ',') + unidade_str
                    preco_antigo_str = f"R$ {preco_antigo_val:.2f}".replace('.', ',') + unidade_str

                    preco_html = f"""
                        <b>{preco_oferta_str}</b> <span style='color:red;'>-{desconto}% OFF</span><br>
                        <span style='color:gray; text-decoration: line-through;'>{preco_antigo_str}</span>
                    """
                elif exibe_preco_original:
                    preco_principal = f"R$ {preco:.2f}".replace('.', ',')
                    preco_principal = f"{preco_principal}/{unidade}" if unidade else preco_principal
                    preco_html = f"<b>{preco_principal}</b>"
                else:
                    preco_principal = f"R$ {preco:.2f}".replace('.', ',')
                    preco_principal = f"{preco_principal}/{unidade}" if unidade else preco_principal
                    preco_html = f"<b>{preco_principal}</b>"

            st.markdown(f"""
                <div class='product-container'>
                    <div class='product-image'>
                        <img src='{imagem_url}' width='80'/>
                    </div>
                    <div class='product-info'>
                        <div style='margin-bottom: 4px;'><b>{descricao}</b></div>
                        <div style='font-size:0.85em;'>{preco_html}</div>
                    </div>
                </div>
                <hr class='product-separator' />
            """, unsafe_allow_html=True)

    else:
        st.error("Erro ao buscar produtos. Verifique o termo de busca ou a conexão.")
