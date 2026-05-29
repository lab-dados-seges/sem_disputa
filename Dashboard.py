import os
import math
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Dashboard Compras Sem Disputa", layout="wide")


def formata_numero(valor, prefixo=""):
    if pd.isna(valor):
        return "-"
    for unidade in ["", "mil", "milhoes", "bilhoes"]:
        if abs(valor) < 1000:
            if unidade == "":
                return f"{prefixo} {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f"{prefixo} {valor:,.2f} {unidade}".replace(",", "X").replace(".", ",").replace("X", ".")
        valor /= 1000
    return f"{prefixo} {valor:,.2f} trilhoes".replace(",", "X").replace(".", ",").replace("X", ".")


def pagina_fatia(df, tamanho, pagina):
    inicio = (pagina - 1) * tamanho
    fim = inicio + tamanho
    return df.iloc[inicio:fim]


@st.cache_data
def carregar_dados(caminho_csv):
    dados = pd.read_csv(caminho_csv, low_memory=False)
    colunas_numericas = ["QTD_ITEM", "VLR_UNITARIO_ESTIMADO", "VLR_TOTAL", "VALOR_TOTAL_HOMOLOGADO"]
    for coluna in colunas_numericas:
        dados[coluna] = pd.to_numeric(dados[coluna], errors="coerce")
    dados["DTH_ATUALIZACAO"] = pd.to_datetime(dados["DTH_ATUALIZACAO"], errors="coerce")
    return dados


st.title("Dashboard de Compras Sem Disputa")
st.caption("Fonte: dados/compras_sem_disputa(2).csv")

arquivo_padrao = Path(__file__).parent / "dados" / "compras_sem_disputa(2).csv"
arquivo_personalizado = os.getenv("DASHBOARD_DATASET_PATH")
caminho = Path(arquivo_personalizado) if arquivo_personalizado else arquivo_padrao
if not caminho.exists():
    st.error(f"Arquivo nao encontrado: {caminho}")
    st.stop()

dados_base = carregar_dados(caminho)

st.sidebar.title("Filtros")
pagina = st.sidebar.radio("Pagina", ["Visao Geral", "Itens", "Compradores", "Dados Brutos"])

esferas = sorted(dados_base["NOM_ESFERA"].dropna().unique().tolist())
modalidades = sorted(dados_base["NOM_MODALIDADE"].dropna().unique().tolist())

filtro_esfera = st.sidebar.multiselect("Esfera", esferas, default=esferas)
filtro_modalidade = st.sidebar.multiselect("Modalidade", modalidades, default=modalidades)

apenas_compra_direta = st.sidebar.checkbox("Somente compra direta (Dispensa/Inexigibilidade)", value=True)

dados = dados_base.copy()
if filtro_esfera:
    dados = dados[dados["NOM_ESFERA"].isin(filtro_esfera)]
if filtro_modalidade:
    dados = dados[dados["NOM_MODALIDADE"].isin(filtro_modalidade)]
if apenas_compra_direta:
    dados = dados[dados["COD_MODALIDADE"].isin([8, 9])]

if dados.empty:
    st.warning("Nenhum registro encontrado com os filtros selecionados.")
    st.stop()

resumo_itens = (
    dados.groupby("DSC_ITEM", as_index=False)
    .agg(
        quantidade_total=("QTD_ITEM", "sum"),
        valor_total_homologado=("VALOR_TOTAL_HOMOLOGADO", "sum"),
        compras=("COD_IDENTIFICADOR_COMPRA", "count"),
    )
    .sort_values(["quantidade_total", "valor_total_homologado"], ascending=False)
)

resumo_uasg = (
    dados.groupby(["COD_UASG", "NOM_UASG"], as_index=False)
    .agg(
        quantidade_total_itens=("QTD_ITEM", "sum"),
        valor_total_homologado=("VALOR_TOTAL_HOMOLOGADO", "sum"),
        compras=("COD_IDENTIFICADOR_COMPRA", "count"),
    )
    .sort_values("valor_total_homologado", ascending=False)
)

compras_por_mes = (
    dados.dropna(subset=["DTH_ATUALIZACAO"])
    .set_index("DTH_ATUALIZACAO")
    .groupby(pd.Grouper(freq="M"))
    .agg(valor_total_homologado=("VALOR_TOTAL_HOMOLOGADO", "sum"), quantidade_itens=("QTD_ITEM", "sum"))
    .reset_index()
)

tamanho_pagina = 20
max_pag_itens = max(1, math.ceil(len(resumo_itens) / tamanho_pagina))
max_pag_uasg = max(1, math.ceil(len(resumo_uasg) / tamanho_pagina))

pag_itens = st.sidebar.number_input("Pagina de itens (20 por pagina)", min_value=1, max_value=max_pag_itens, value=1)
pag_uasg = st.sidebar.number_input("Pagina de UASG (20 por pagina)", min_value=1, max_value=max_pag_uasg, value=1)

itens_paginados = pagina_fatia(resumo_itens, tamanho_pagina, pag_itens)
uasg_paginados = pagina_fatia(resumo_uasg, tamanho_pagina, pag_uasg)

if pagina == "Visao Geral":
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Valor total homologado", formata_numero(dados["VALOR_TOTAL_HOMOLOGADO"].sum(), "R$"))
    c2.metric("Quantidade total de itens", formata_numero(dados["QTD_ITEM"].sum()))
    c3.metric("Compras diretas", formata_numero(float(dados["COD_IDENTIFICADOR_COMPRA"].nunique())))
    c4.metric("UASG unicas", formata_numero(float(dados["COD_UASG"].nunique())))

    col1, col2 = st.columns(2)

    with col1:
        top_itens = resumo_itens.head(20)
        fig_combo = go.Figure()
        fig_combo.add_bar(
            x=top_itens["DSC_ITEM"],
            y=top_itens["valor_total_homologado"],
            name="Valor total homologado",
            marker_color="#1f77b4",
        )
        fig_combo.add_scatter(
            x=top_itens["DSC_ITEM"],
            y=top_itens["quantidade_total"],
            name="Quantidade de itens",
            yaxis="y2",
            mode="lines+markers",
            line=dict(color="#ff7f0e", width=3),
        )
        fig_combo.update_layout(
            title="Top 20 itens: barras (valor homologado) + linha (quantidade de itens)",
            xaxis=dict(title="Descricao do item", tickangle=-45),
            yaxis=dict(title="Valor total homologado (R$)"),
            yaxis2=dict(title="Quantidade de itens", overlaying="y", side="right"),
            legend=dict(orientation="h", y=1.1),
            margin=dict(b=140),
        )
        st.plotly_chart(fig_combo, use_container_width=True)

    with col2:
        fig_mes = px.line(
            compras_por_mes,
            x="DTH_ATUALIZACAO",
            y="valor_total_homologado",
            markers=True,
            title="Evolucao mensal do valor total homologado",
        )
        fig_mes.update_layout(xaxis_title="Mes", yaxis_title="Valor homologado (R$)")
        st.plotly_chart(fig_mes, use_container_width=True)

    st.dataframe(
        itens_paginados,
        use_container_width=True,
        hide_index=True,
    )

elif pagina == "Itens":
    st.subheader("Maiores itens comprados")
    st.caption(f"Pagina {pag_itens} de {max_pag_itens} (20 itens por pagina)")

    fig_itens_qtd = px.bar(
        itens_paginados,
        x="DSC_ITEM",
        y="quantidade_total",
        text_auto=True,
        title="X: itens mais comprados | Y: quantidade total",
    )
    fig_itens_qtd.update_layout(xaxis_title="Item", yaxis_title="Quantidade total", xaxis_tickangle=-45, margin=dict(b=140))
    st.plotly_chart(fig_itens_qtd, use_container_width=True)

    fig_itens_valor = px.bar(
        itens_paginados,
        x="DSC_ITEM",
        y="valor_total_homologado",
        text_auto=True,
        title="Valor total homologado por item (pagina atual)",
    )
    fig_itens_valor.update_layout(xaxis_title="Item", yaxis_title="Valor homologado (R$)", xaxis_tickangle=-45, margin=dict(b=140))
    st.plotly_chart(fig_itens_valor, use_container_width=True)

    st.dataframe(itens_paginados, use_container_width=True, hide_index=True)

elif pagina == "Compradores":
    st.subheader("Maiores compradores")
    st.caption(f"Pagina {pag_uasg} de {max_pag_uasg} (20 UASG por pagina)")

    fig_uasg_valor = px.bar(
        uasg_paginados,
        x="NOM_UASG",
        y="valor_total_homologado",
        text_auto=True,
        title="X: maiores compradores | Y: valor total comprado (compra direta)",
    )
    fig_uasg_valor.update_layout(xaxis_title="Comprador (UASG)", yaxis_title="Valor homologado (R$)", xaxis_tickangle=-45, margin=dict(b=140))
    st.plotly_chart(fig_uasg_valor, use_container_width=True)

    fig_uasg_qtd = px.bar(
        uasg_paginados,
        x="NOM_UASG",
        y="quantidade_total_itens",
        text_auto=True,
        title="Quantidade total de itens por comprador (pagina atual)",
    )
    fig_uasg_qtd.update_layout(xaxis_title="Comprador (UASG)", yaxis_title="Quantidade de itens", xaxis_tickangle=-45, margin=dict(b=140))
    st.plotly_chart(fig_uasg_qtd, use_container_width=True)

    st.dataframe(uasg_paginados, use_container_width=True, hide_index=True)

else:
    st.subheader("Dados brutos filtrados")
    st.dataframe(dados, use_container_width=True, hide_index=True)
         
