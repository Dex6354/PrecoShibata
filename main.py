import streamlit as st
import requests

def buscar_produto_shibata_api():
    url = "https://services.vipcommerce.com.br/api-admin/v1/org/161/filial/1/centro_distribuicao/1/loja/produtos/16286/detalhes"

    headers = {
        "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJ2aXBjb21tZXJjZSIsImF1ZCI6ImFwaS1hZG1pbiIsInN1YiI6IjZiYzQ4NjdlLWRjYTktMTFlOS04NzQyLTAyMGQ3OTM1OWNhMCIsInZpcGNvbW1lcmNlQ2xpZW50ZUlkIjpudWxsLCJpYXQiOjE3NTE5MjQ5MjgsInZlciI6MSwiY2xpZW50IjpudWxsLCJvcGVyYXRvciI6bnVsbCwib3JnIjoiMTYxIn0.yDCjqkeJv7D3wJ0T_fu3AaKlX9s5PQYXD19cESWpH-j3F_Is-Zb-bDdUvduwoI_RkOeqbYCuxN0ppQQXb1ArVg",
        "organizationid": "161",
        "sessao-id": "4ea572793a132ad95d7e758a4eaf6b09",
        "domainkey": "loja.shibata.com.br",
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        produto = response.json()['data']['produto']
        nome = produto['descricao']
        preco_total = float(produto['preco'])
        preco_por_kg = float(produto['preco_original'])
        unidade = produto['unidade_sigla']
        peso_kg = produto['quantidade_unidade_diferente']

        return {
            "nome": nome,
            "preco_total": preco_total,
            "preco_por_kg": preco_por_kg,
            "unidade": unidade,
            "peso_kg": peso_kg
        }
    else:
        return {"erro": f"Erro {response.status_code}: {response.text}"}

# ---------- INTERFACE STREAMLIT ----------

st.set_page_config(page_title="Consulta Shibata", page_icon="🛒")

st.markdown("## 🟥 Shibata")

shibata = buscar_produto_shibata_api()

if "erro" not in shibata:
    st.markdown(f"### 🛒 Produto: {shibata['nome']}")
    st.markdown(f"💰 **Preço total**: R$ {shibata['preco_total']:.2f} para {shibata['peso_kg']} {shibata['unidade']}")
    st.markdown(f"📏 **Preço por kg**: R$ {shibata['preco_por_kg']:.2f}")
else:
    st.error(shibata["erro"])
