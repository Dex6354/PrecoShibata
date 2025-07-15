import streamlit as st
import requests
import unicodedata
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

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

def calcular_preco_papel_toalha(descricao, preco_total):
    desc = descricao.lower()

    # Tenta extrair quantidade de unidades (rolos, unidades, pacotes)
    qtd_unidades = None
    match_unidades = re.search(r'(\d+)\s*(rolos|unidades|pacotes|pacote|kits?)', desc)
    if match_unidades:
        qtd_unidades = int(match_unidades.group(1))

    # Tenta extrair número de folhas por unidade (folhas, toalhas)
    folhas_por_unidade = None
    # Exemplo: "com 120 folhas cada"
    match_folhas = re.search(r'(\d+)\s*(folhas|toalhas)\s*cada', desc)
    if not match_folhas:
        # Exemplo: "Folha Dupla ... - 550 folhas"
        match_folhas = re.search(r'(\d+)\s*(folhas|toalhas)', desc)
    if match_folhas:
        folhas_por_unidade = int(match_folhas.group(1))

    # Tenta extrair "Leve 240 pague 220 folhas" — pega o maior número próximo da palavra folhas
    match_leve_pague = re.findall(r'(\d+)', desc)
    folhas_leve = None
    if 'leve' in desc and 'folhas' in desc and match_leve_pague:
        folhas_leve = max(int(n) for n in match_leve_pague)

    # Tenta extrair detalhes em texto estilo "Unidades por kit: 2 ... Quantidade de folhas por rolo: 100"
    match_unidades_kit = re.search(r'unidades por kit[:\- ]+(\d+)', desc)
    match_folhas_rolo = re.search(r'quantidade de folhas por (?:rolo|unidade)[:\- ]+(\d+)', desc)

    # Lógica para calcular total de folhas:
    if match_unidades_kit and match_folhas_rolo:
        total_folhas = int(match_unidades_kit.group(1)) * int(match_folhas_rolo.group(1))
        preco_por_folha = preco_total / total_folhas if total_folhas else None
        return total_folhas, preco_por_folha

    if qtd_unidades and folhas_por_unidade:
        total_folhas = qtd_unidades * folhas_por_unidade
        preco_por_folha = preco_total / total_folhas if total_folhas else None
        return total_folhas, preco_por_folha

    if folhas_por_unidade:
        preco_por_folha = preco_total / folhas_por_unidade if folhas_por_unidade else None
        return folhas_por_unidade, preco_por_folha

    if folhas_leve:
        preco_por_folha = preco_total / folhas_leve if folhas_leve else None
        return folhas_leve, preco_por_folha

    return None, None


def formatar_preco_unidade_personalizado(preco_total, quantidade, unidade):
    if not unidade:
        return None
    unidade = unidade.lower()
    if quantidade and quantidade != 1:
        return f"R$ {preco_total:.2f}".replace('.', ',') + f"/{str(quantidade).replace('.', ',')}{unidade.lower()}"
    else:
        return f"R$ {preco_total:.2f}".replace('.', ',') + f"/{unidade.lower()}"

def buscar_pagina(termo, pagina):
    url = f"https://services.vipcommerce.com.br/api-admin/v1/org/{ORG_ID}/filial/1/centro_distribuicao/1/loja/buscas/produtos/termo/{termo}?page={pagina}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json().get('data', {}).get('produtos', [])
            return [produto for produto in data if produto.get("disponivel", True)]  # 🔥 Filtra só produtos disponíveis
    except Exception:
        pass
    return []

st.set_page_config(page_title="Preço Shibata", page_icon="🧻")

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
    produtos_totais = []
    max_workers = 11
    max_paginas = 22

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(buscar_pagina, termo, pagina) for pagina in range(1, max_paginas + 1)]
        for future in as_completed(futures):
            produtos_totais.extend(future.result())

    termo_sem_acento = remover_acentos(termo)
    palavras_termo = termo_sem_acento.split()
    produtos_filtrados = [p for p in produtos_totais if all(palavra in remover_acentos(p.get('descricao', '')) for palavra in palavras_termo)]

    produtos_processados = []
    for p in produtos_filtrados:
        if not p.get("disponivel", True):  # 🔒 Reforço de segurança
            continue
        preco = float(p.get('preco') or 0)
        em_oferta = p.get('em_oferta', False)
        oferta_info = p.get('oferta') or {}
        preco_oferta = oferta_info.get('preco_oferta')
        preco_total = float(preco_oferta) if em_oferta and preco_oferta else preco
        descricao = p.get('descricao', '')
        quantidade_dif = p.get('quantidade_unidade_diferente')
        unidade_sigla = p.get('unidade_sigla')

        preco_unidade_str = formatar_preco_unidade_personalizado(preco_total, quantidade_dif, unidade_sigla)
        preco_unidade_val, _ = calcular_preco_unidade(descricao, preco_total)
        preco_por_metro_val, _ = calcular_precos_papel(descricao, preco_total)

        p['preco_unidade_val'] = preco_unidade_val if preco_unidade_val else float('inf')
        p['preco_unidade_str'] = preco_unidade_str or ""
        p['preco_por_metro_val'] = preco_por_metro_val if preco_por_metro_val else float('inf')
        produtos_processados.append(p)

    # Ordenação especial para papel toalha, papel higiênico e demais
    if 'papel toalha' in termo_sem_acento:
        for p in produtos_processados:
            preco_oferta = (p.get('oferta') or {}).get('preco_oferta')
            preco_atual = float(preco_oferta) if preco_oferta else float(p.get('preco') or 0)
            total_folhas, preco_por_folha = calcular_preco_papel_toalha(p.get('descricao', ''), preco_atual)
            p['preco_por_folha_val'] = preco_por_folha if preco_por_folha else float('inf')
        produtos_ordenados = sorted(produtos_processados, key=lambda x: x['preco_por_folha_val'])
    elif 'papel higienico' in termo_sem_acento:
        produtos_ordenados = sorted(produtos_processados, key=lambda x: x['preco_por_metro_val'])
    else:
        produtos_ordenados = sorted(produtos_processados, key=lambda x: x['preco_unidade_val'])

    st.markdown(f"<small>🔎 {len(produtos_ordenados)} produto(s) encontrado(s).</p>", unsafe_allow_html=True)

    if not produtos_ordenados:
        st.warning("Nenhum produto encontrado com esse nome.")

    for p in produtos_ordenados:
        preco = float(p.get('preco') or 0)
        descricao = p.get('descricao', '')
        imagem = p.get('imagem', '')
        em_oferta = p.get('em_oferta', False)
        oferta_info = p.get('oferta') or {}
        preco_oferta = oferta_info.get('preco_oferta')
        preco_antigo = oferta_info.get('preco_antigo')
        imagem_url = f"https://produtos.vipcommerce.com.br/250x250/{imagem}"
        preco_total = float(preco_oferta) if em_oferta and preco_oferta else preco

        quantidade_dif = p.get('quantidade_unidade_diferente')
        unidade_sigla = p.get('unidade_sigla')
        preco_formatado = formatar_preco_unidade_personalizado(preco_total, quantidade_dif, unidade_sigla)

        if em_oferta and preco_oferta and preco_antigo:
            preco_oferta_val = float(preco_oferta)
            preco_antigo_val = float(preco_antigo)
            desconto = round(100 * (preco_antigo_val - preco_oferta_val) / preco_antigo_val) if preco_antigo_val else 0
            preco_antigo_str = f"R$ {preco_antigo_val:.2f}".replace('.', ',')
            preco_html = f"""
                <div><b style='color:green;'>{preco_formatado}</b> <span style='color:red;'>({desconto}% OFF)</span></div>
                <div><span style='color:gray; text-decoration: line-through;'>Preço original: {preco_antigo_str}</span></div>
            """
        else:
            preco_html = f"<div><b>{preco_formatado}</b></div>"

        preco_info_extra = ""
        descricao_modificada = descricao
        total_folhas, preco_por_folha = calcular_preco_papel_toalha(descricao, preco_total)

        if total_folhas and preco_por_folha:
            descricao_modificada += f" <span style='color:gray;'>({total_folhas} folhas)</span>"
            preco_info_extra += f"<div style='color:gray; font-size:0.75em;'>R$ {preco_por_folha:.3f}/folha</div>"
        else:
            _, preco_por_metro_str = calcular_precos_papel(descricao, preco_total)
            _, preco_por_unidade_str = calcular_preco_unidade(descricao, preco_total)
            if preco_por_metro_str:
                preco_info_extra += f"<div style='color:gray; font-size:0.75em;'>{preco_por_metro_str}</div>"
            if preco_por_unidade_str:
                preco_info_extra += f"<div style='color:gray; font-size:0.75em;'>{preco_por_unidade_str}</div>"

        st.markdown(f"""
            <div class='product-container'>
                <div class='product-image'>
                    <img src='{imagem_url}' width='80'/>
                </div>
                <div class='product-info'>
                    <div style='margin-bottom: 4px;'><b>{descricao_modificada}</b></div>
                    <div style='font-size:0.85em;'>{preco_html}</div>
                    <div style='font-size:0.85em;'>{preco_info_extra}</div>
                </div>
            </div>
            <hr class='product-separator' />
        """, unsafe_allow_html=True)
else:
    st.info("Digite um termo para buscar.")
