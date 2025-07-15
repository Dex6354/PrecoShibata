import streamlit as st
import requests
import unicodedata
import re

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

def calcular_precos_papel(descricao, preco_total):
    desc_minus = descricao.lower()

    match_leve = re.search(r'leve\s*(\d+)', desc_minus)
    if match_leve:
        q_rolos = int(match_leve.group(1))
    else:
        match_rolos = re.search(r'(\d+)\s*(rolos|unidades|uni|pacotes|pacote)', desc_minus)
        q_rolos = int(match_rolos.group(1)) if match_rolos else None

    match_metros = re.search(r'(\d+(?:[\.,]\d+)?)\s*m(?:etros)?', desc_minus)
    m_rolos = float(match_metros.group(1).replace(',', '.')) if match_metros else None

    if q_rolos and m_rolos:
        preco_por_metro = preco_total / (q_rolos * m_rolos)
        return preco_por_metro, f"R$ {preco_por_metro:.3f}".replace('.', ',') + "/m"
    return None, None

def calcular_preco_unidade(descricao, preco_total):
    desc_minus = remover_acentos(descricao)

    match_kg = re.search(r'(\d+(?:[\.,]\d+)?)\s*(kg|quilo)', desc_minus)
    if match_kg:
        peso = float(match_kg.group(1).replace(',', '.'))
        return preco_total / peso, f"R$ {preco_total / peso:.2f}".replace('.', ',') + "/kg"

    match_g = re.search(r'(\d+(?:[\.,]\d+)?)\s*(g|gramas?)', desc_minus)
    if match_g:
        peso = float(match_g.group(1).replace(',', '.')) / 1000
        return preco_total / peso, f"R$ {preco_total / peso:.2f}".replace('.', ',') + "/kg"

    match_l = re.search(r'(\d+(?:[\.,]\d+)?)\s*(l|litros?)', desc_minus)
    if match_l:
        litros = float(match_l.group(1).replace(',', '.'))
        return preco_total / litros, f"R$ {preco_total / litros:.2f}".replace('.', ',') + "/L"

    match_ml = re.search(r'(\d+(?:[\.,]\d+)?)\s*(ml|mililitros?)', desc_minus)
    if match_ml:
        litros = float(match_ml.group(1).replace(',', '.')) / 1000
        return preco_total / litros, f"R$ {preco_total / litros:.2f}".replace('.', ',') + "/L"

    return None, None

st.set_page_config(page_title="Preço Shibata", page_icon="https://raw.githubusercontent.com/Dex6354/PrecoShibata/refs/heads/main/logo-shibata.png")

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
    <h5 style="display:flex; align-items:center;">
    <div style="padding: 05px; background-color: white; border-radius: 4px; display: inline-block; margin-right: 8px;">
        <img src="https://raw.githubusercontent.com/Dex6354/PrecoShibata/refs/heads/main/logo-shibata.png" width="85" style="display: block;"/>
    </div>
    Preço Shibata
</h5>
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

        produtos_processados = []

        for p in produtos_filtrados:
            preco = float(p.get('preco_original') or p.get('preco') or 0)
            em_oferta = p.get('em_oferta', False)
            oferta_info = p.get('oferta') or {}
            preco_oferta = oferta_info.get('preco_oferta')
            preco_total = float(preco_oferta) if em_oferta and preco_oferta else preco
            descricao = p.get('descricao', '')

            preco_unidade_val, preco_unidade_str = calcular_preco_unidade(descricao, preco_total)
            p['preco_unidade_val'] = preco_unidade_val if preco_unidade_val else float('inf')
            p['preco_unidade_str'] = preco_unidade_str or ""

            produtos_processados.append(p)

        produtos_ordenados = sorted(produtos_processados, key=lambda x: x['preco_unidade_val'])

        st.markdown(f"<small>🔎 {len(produtos_ordenados)} produto(s) encontrado(s).</p>", unsafe_allow_html=True)

        if not produtos_ordenados:
            st.warning("Nenhum produto encontrado com esse nome.")

        for p in produtos_ordenados:
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
            preco_total = float(preco_oferta) if em_oferta and preco_oferta else preco

            preco_html = ""
            unidade_str = f"/{unidade}" if unidade else ""

            # Preço principal (com ou sem desconto)
            if em_oferta and preco_oferta and preco_antigo:
                preco_oferta_val = float(preco_oferta)
                preco_antigo_val = float(preco_antigo)
                desconto = round(100 * (preco_antigo_val - preco_oferta_val) / preco_antigo_val) if preco_antigo_val else 0

                preco_oferta_str = f"R$ {preco_oferta_val:.2f}".replace('.', ',')
                preco_antigo_str = f"R$ {preco_antigo_val:.2f}".replace('.', ',')

                preco_html = f"""
                    <div><b style='color:green;'>{preco_oferta_str}{unidade_str}</b> <span style='color:red;'>({desconto}% OFF)</span></div>
                    <div><span style='color:gray; text-decoration: line-through;'>Preço original: {preco_antigo_str}{unidade_str}</span></div>
                """
            else:
                preco_principal = f"R$ {preco:.2f}".replace('.', ',')
                preco_html = f"<div><b>{preco_principal}{unidade_str}</b></div>"

            # Preços adicionais
            preco_por_metro_str = None
            if 'papel higiênico' in descricao.lower() or 'papel higienico' in descricao.lower():
                _, preco_por_metro_str = calcular_precos_papel(descricao, preco_total)

            preco_por_unidade = p.get('preco_unidade_str')

            preco_info_extra = ""
            if preco_por_metro_str:
                preco_info_extra += f"<div style='color:gray; font-size:0.75em;'>{preco_por_metro_str}</div>"
            if preco_por_unidade:
                preco_info_extra += f"<div style='color:gray; font-size:0.75em;'>{preco_por_unidade}</div>"


            st.markdown(f"""
                <div class='product-container'>
                    <div class='product-image'>
                        <img src='{imagem_url}' width='80'/>
                    </div>
                    <div class='product-info'>
                        <div style='margin-bottom: 4px;'><b>{descricao}</b></div>
                        <div style='font-size:0.85em;'>{preco_html}</div>
                        <div style='font-size:0.85em;'>{preco_info_extra}</div>
                    </div>
                </div>
                <hr class='product-separator' />
            """, unsafe_allow_html=True)

    else:
        st.error("Erro ao buscar produtos. Verifique o termo de busca ou a conexão.")
