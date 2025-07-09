import streamlit as st
import requests
from bs4 import BeautifulSoup

# Configuração da página
st.set_page_config(page_title="Busca de Produtos Nagumo", page_icon="🛒")

# CSS para remover espaço superior e rodapé
st.markdown("""
    <style>
        .block-container { padding-top: 0rem; }
        footer {visibility: hidden;}
        #MainMenu {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Título
st.markdown("<h5>🛒 Preço Nagumo</h5>", unsafe_allow_html=True)

busca = st.text_input("Digite o nome do produto:")

def buscar_produto_nagumo(palavra_chave):
    palavra_chave_url = palavra_chave.strip().lower().replace(" ", "+")
    url = f"https://www.nagumo.com.br/nagumo/74b2f698-cffc-4a38-b8ce-0407f8d98de3/busca/{palavra_chave_url}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')

        product_containers = soup.find_all('div', class_='sc-c5cd0085-0 fWmXTW')

        for container in product_containers:
            nome_tag = container.find('span', class_='sc-fLlhyt hJreDe sc-14455254-0 sc-c5cd0085-4 ezNOEq clsIKA')
            if not nome_tag:
                continue

            nome_text = nome_tag.text.strip()
            search_words = set(palavra_chave.lower().split())
            product_words = set(nome_text.lower().split())
            if not search_words.intersection(product_words):
                continue

            # Verifica preço promocional
            preco_promo_tag = container.find('span', class_='sc-fLlhyt gMFJKu sc-14455254-0 sc-c5cd0085-9 ezNOEq dDNfcV')
            preco_text = preco_promo_tag.text.strip() if preco_promo_tag else None

            # Verifica preço original e desconto
            preco_antigo_tag = container.find('span', class_='sc-fLlhyt ehGA-Dk sc-14455254-0 sc-c5cd0085-12 ezNOEq bFqXWZ')
            desconto_tag = container.find('span', class_='sc-fLlhyt hJreDe sc-14455254-0 sc-c5cd0085-11 ezNOEq hoiAgS')

            if preco_promo_tag and preco_antigo_tag and desconto_tag:
                preco_text = f"{preco_promo_tag.text.strip()} ({preco_antigo_tag.text.strip()} {desconto_tag.text.strip()})"
            elif preco_promo_tag:
                preco_text = preco_promo_tag.text.strip()
            else:
                # Verifica preço normal (usando a classe original)
                preco_normal_tag = container.find('span', class_='sc-fLlhyt fKrYQk sc-14455254-0 sc-c5cd0085-9 ezNOEq dDNfcV')
                if preco_normal_tag:
                    preco_text = preco_normal_tag.text.strip()
                else:
                    # Busca genérica por qualquer span dentro da div de preço
                    preco_container = container.find('div', class_='sc-c5cd0085-7')
                    if preco_container:
                        preco_fallback_tag = preco_container.find('span', class_=lambda x: x and 'sc-fLlhyt' in x and 'ezNOEq' in x)
                        preco_text = preco_fallback_tag.text.strip() if preco_fallback_tag else "Preço não encontrado"
                    else:
                        preco_text = "Preço não encontrado"

            descricao_tag = container.find('span', class_='sc-fLlhyt dPLwZv sc-14455254-0 sc-c5cd0085-10 ezNOEq krnAMj')
            descricao_text = descricao_tag.text.strip() if descricao_tag else "Descrição não encontrada"

            imagem_url = "Imagem não encontrada"
            noscript_tag = container.find('noscript')
            if noscript_tag:
                nosoup = BeautifulSoup(noscript_tag.decode_contents(), 'html.parser')
                img_tag = nosoup.find('img')
                if img_tag and img_tag.get('src'):
                    imagem_url = img_tag['src']

            return nome_text, preco_text, descricao_text, imagem_url

        return "Nome não encontrado", "Preço não encontrado", "Descrição não encontrada", "Imagem não encontrada"

    except Exception as e:
        return "Erro na busca", "", "", str(e)

if busca:
    nome, preco, descricao, imagem = buscar_produto_nagumo(busca)
    st.write(f"**Produto:** {nome}")
    st.write(f"**Preço:** {preco}")
    st.write(f"**Descrição:** {descricao}")
    if imagem != "Imagem não encontrada":
        st.image(imagem, width=200)
