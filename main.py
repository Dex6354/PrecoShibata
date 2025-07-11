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

    # Monta o html para preço
    preco_html = ""
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
            preco_html = f"""
                <div style="line-height:1.3; margin-top: 0px;">
                    <p style="font-size:0.85em; margin:0;">
                        <b>R$ {preco_original_str}{unidade_str}</b> 
                        <span style="color:red;">-{desconto}% OFF</span>
                    </p>
                </div>
            """
        else:
            preco_oferta_exibe = f"R$ {preco_oferta_str}{unidade_str}"
            preco_antigo_exibe = f"R$ {preco_antigo_str}{unidade_str}"
            preco_html = f"""
                <div style="line-height:1.3; margin-top: 0px;">
                    <p style="font-size:0.85em; margin:0;">
                        <b style="color: white;">{preco_oferta_exibe}</b> 
                        <span style="color:red;">-{desconto}% OFF</span>
                    </p>
                    <p style="font-size:0.85em; color:gray; text-decoration: line-through; margin:0;">
                        {preco_antigo_exibe}
                    </p>
                </div>
            """
    elif exibe_preco_original:
        preco_principal = f"R$ {preco:.2f}".replace('.', ',')
        preco_principal = f"{preco_principal}/{unidade}" if unidade else preco_principal
        preco_html = f"<p style='font-size:0.85em; margin:0; margin-top: 0px; color: white;'><b>{preco_principal}</b></p>"
    else:
        preco_principal = f"R$ {preco:.2f}".replace('.', ',')
        preco_principal = f"{preco_principal}/{unidade}" if unidade else preco_principal
        preco_html = f"<p style='font-size:0.85em; margin:0; margin-top: 0px; color: white;'><b>{preco_principal}</b></p>"

    # Exibe tudo junto, lado a lado, sem quebra mesmo em telas pequenas
    st.markdown(f"""
        <div style="
            display: flex; 
            flex-wrap: nowrap; 
            align-items: center; 
            gap: 12px; 
            background-color: #222; 
            padding: 8px; 
            border-radius: 6px;
        ">
            <img src="{imagem_url}" width="100" style="flex-shrink: 0; border-radius: 4px;" />
            <div style="color: white; min-width: 0;">
                <div style="font-weight: bold; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                    {descricao}
                </div>
                {preco_html}
            </div>
        </div>
    """, unsafe_allow_html=True)
