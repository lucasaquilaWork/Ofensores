import re

import pandas as pd
import streamlit as st

from processamento import (
    processar_carregamento,
    processar_ocorrencias,
)

from sheets import (
    salvar_carregamentos_sem_duplicar,
    carregar_dados_aba,
    salvar_ofensores_sem_duplicar,

    carregar_tratativas,
    salvar_tratativa,
    atualizar_tratativa,
    buscar_tratativa_ofensa,
    buscar_historico_tratativas_driver,
    analisar_reincidencia_pos_tratativa,
)
# ==========================================================
# CONFIGURAÇÃO
# ==========================================================

st.set_page_config(
    page_title="Controle de Ofensores",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==========================================================
# ESTADO DO MENU
# ==========================================================

if "pagina" not in st.session_state:
    st.session_state.pagina = "Carregamentos"


def mudar_pagina(pagina):
    st.session_state.pagina = pagina


# ==========================================================
# CSS
# ==========================================================

st.markdown(
    """
<style>

/* ---------------------------------------------------------
   PÁGINA
--------------------------------------------------------- */

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1500px;
}


/* ---------------------------------------------------------
   SIDEBAR
--------------------------------------------------------- */

section[data-testid="stSidebar"] {
    border-right: 1px solid rgba(255,255,255,0.08);
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem;
}


/* ---------------------------------------------------------
   BOTÕES DO MENU
--------------------------------------------------------- */

section[data-testid="stSidebar"] div[data-testid="stButton"] {
    margin-bottom: 6px;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] button {

    width: 100%;

    height: 48px;

    justify-content: flex-start;

    text-align: left;

    border-radius: 10px;

    border: 1px solid transparent;

    background: transparent;

    font-size: 15px;

    font-weight: 600;

    padding-left: 15px;

    transition: all 0.15s ease;
}


/* HOVER */

section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {

    background: rgba(255,255,255,0.07);

    border-color: rgba(255,255,255,0.08);

}


/* ---------------------------------------------------------
   MÉTRICAS
--------------------------------------------------------- */

div[data-testid="stMetric"] {

    border: 1px solid rgba(255,255,255,0.08);

    background: rgba(255,255,255,0.025);

    padding: 18px;

    border-radius: 12px;
}

</style>
""",
    unsafe_allow_html=True
)


# ==========================================================
# SIDEBAR
# ==========================================================

with st.sidebar:

    # ------------------------------------------------------
    # LOGO / CABEÇALHO
    # ------------------------------------------------------

    st.markdown(
        """
<div style="padding: 4px 4px 20px 4px;">

<div style="
font-size: 11px;
color: #8b949e;
font-weight: 700;
letter-spacing: 1.6px;
text-transform: uppercase;
">
OPERAÇÃO
</div>

<div style="
font-size: 22px;
font-weight: 750;
margin-top: 5px;
line-height: 1.25;
">
Controle de Ofensores
</div>

<div style="
font-size: 13px;
color: #8b949e;
margin-top: 7px;
">
Monitoramento de performance
</div>

</div>
""",
        unsafe_allow_html=True
    )

    # ------------------------------------------------------
    # MENU
    # ------------------------------------------------------

    st.button(
        "🚚   Carregamentos",
        use_container_width=True,
        on_click=mudar_pagina,
        args=("Carregamentos",)
    )

    st.button(
        "⚠️   Ocorrências",
        use_container_width=True,
        on_click=mudar_pagina,
        args=("Ocorrências",)
    )

    st.button(
        "📊   Histórico",
        use_container_width=True,
        on_click=mudar_pagina,
        args=("Histórico",)
    )

    st.button(
        "📝   Tratativas",
        use_container_width=True,
        on_click=mudar_pagina,
        args=("Tratativas",)
    )

    st.markdown("---")

    st.caption("Shopee • Monitoramento operacional")


# ==========================================================
# PÁGINA ATUAL
# ==========================================================

pagina = st.session_state.pagina


# ==========================================================
# CARREGAMENTOS
# ==========================================================

if pagina == "Carregamentos":

    st.title("Carregamentos")

    st.caption(
        "Importação e consolidação das cargas da operação."
    )

    st.divider()

    arquivo = st.file_uploader(
        "Selecione o arquivo Assignment Task",
        type=["csv"]
    )

    if arquivo is not None:

        try:

            try:
                df_raw = pd.read_csv(
                    arquivo,
                    encoding="utf-8"
                )

            except UnicodeDecodeError:

                arquivo.seek(0)

                df_raw = pd.read_csv(
                    arquivo,
                    encoding="latin-1"
                )

            df = processar_carregamento(df_raw)

            st.success(
                "Arquivo processado com sucesso."
            )

            # ==========================================
            # RESUMO
            # ==========================================

            total_carregamentos = df["TASK_ID"].nunique()

            total_motoristas = df["DRIVER_ID"].nunique()

            total_pacotes = int(
                df["PACOTES_CARREGADOS"].sum()
            )

            total_risco = int(
                df["PACOTES_AREA_RISCO"].sum()
            )

            percentual_risco = (
                total_risco / total_pacotes * 100
                if total_pacotes > 0
                else 0
            )

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "Carregamentos",
                total_carregamentos
            )

            c2.metric(
                "Motoristas",
                total_motoristas
            )

            c3.metric(
                "Pacotes carregados",
                total_pacotes
            )

            c4.metric(
                "Área de risco",
                f"{total_risco} ({percentual_risco:.1f}%)"
            )

            st.divider()

            # ==========================================
            # RESUMO POR TURNO
            # ==========================================

            st.subheader("Resumo por turno")

            resumo_turno = (
                df.groupby(
                    "TURNO_CARREGAMENTO",
                    dropna=False
                )
                .agg(
                    CARREGAMENTOS=("TASK_ID", "nunique"),
                    MOTORISTAS=("DRIVER_ID", "nunique"),
                    PACOTES=("PACOTES_CARREGADOS", "sum")
                )
                .reset_index()
            )

            st.dataframe(
                resumo_turno,
                use_container_width=True,
                hide_index=True
            )

            st.divider()

            # ==========================================
            # MAIORES CARGAS
            # ==========================================

            st.subheader("Maiores carregamentos")

            maiores_cargas = (
                df.sort_values(
                    "PACOTES_CARREGADOS",
                    ascending=False
                )
                .head(15)
            )

            st.dataframe(
                maiores_cargas[
                    [
                        "DRIVER_NAME",
                        "HORA_CARREGAMENTO",
                        "CLUSTER",
                        "PACOTES_CARREGADOS",
                        "PACOTES_AREA_RISCO",
                        "PERCENTUAL_AREA_RISCO"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )

            st.divider()

            # ==========================================
            # PRÉVIA
            # ==========================================

            st.subheader("Prévia dos carregamentos")

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                height=420
            )

            st.caption(
                f"{len(df)} carregamentos encontrados."
            )

            # ==========================================
            # SALVAR
            # ==========================================

            st.divider()

            if st.button(
                "Salvar carregamentos",
                type="primary",
                use_container_width=True
            ):

                with st.spinner(
                    "Salvando no Google Sheets..."
                ):

                    resultado = (
                        salvar_carregamentos_sem_duplicar(
                            df
                        )
                    )

                if resultado["salvos"] > 0:

                    st.success(
                        f'{resultado["salvos"]} carregamentos '
                        f'salvos com sucesso.'
                    )

                if resultado["duplicados"] > 0:

                    st.warning(
                        f'{resultado["duplicados"]} carregamentos '
                        f'já existiam e foram ignorados.'
                    )

                if (
                    resultado["salvos"] == 0
                    and resultado["duplicados"] > 0
                ):

                    st.info(
                        "Nenhum registro novo para salvar."
                    )

        except Exception as e:

            st.error(
                "Erro ao processar o arquivo."
            )

            st.exception(e)
# ==========================================================
# OCORRÊNCIAS
# ==========================================================

elif pagina == "Ocorrências":

    st.title("Ocorrências")

    st.caption(
        "Análise diária de ocorrências e pacotes que permanecem em aberto."
    )

    st.divider()

    # ======================================================
    # UPLOAD
    # ======================================================

    arquivo_forward = st.file_uploader(
        "Selecione o Forward Order",
        type=["csv"],
        key="forward_order"
    )

    if arquivo_forward is not None:

        try:

            # ==================================================
            # LEITURA
            # ==================================================

            try:

                df_forward = pd.read_csv(
                    arquivo_forward,
                    encoding="utf-8"
                )

            except UnicodeDecodeError:

                arquivo_forward.seek(0)

                df_forward = pd.read_csv(
                    arquivo_forward,
                    encoding="latin-1"
                )

            # ==================================================
            # CARREGAMENTOS DO SHEETS
            # ==================================================

            with st.spinner(
                "Cruzando Forward Order com os carregamentos..."
            ):

                df_carregamentos = (
                    carregar_dados_aba(
                        "DADOS DE CARREGAMENTO"
                    )
                )

                resultado = processar_ocorrencias(
                    df_forward,
                    df_carregamentos
                )

            base = resultado["base_completa"].copy()
            ofensores = resultado["ofensores"].copy()

            data_referencia = (
                resultado["data_referencia"]
            )

            # ==================================================
            # RESUMO DAS OCORRÊNCIAS
            #
            # Quando não existe motivo de OnHold,
            # mas o motorista possui pacotes em aberto,
            # exibe:
            #
            # Em aberto (86)
            #
            # Isso também será salvo no histórico.
            # ==================================================

            def ajustar_resumo_ocorrencias(row):

                resumo = row.get(
                    "RESUMO_OCORRENCIAS",
                    ""
                )

                if pd.isna(resumo):
                    resumo = ""

                resumo = str(resumo).strip()

                # ----------------------------------------------
                # Já possui motivo de OnHold
                # ----------------------------------------------

                if (
                    resumo
                    and resumo.lower()
                    not in [
                        "nan",
                        "none"
                    ]
                ):
                    return resumo

                # ----------------------------------------------
                # Em aberto da operação atual
                # ----------------------------------------------

                try:
                    abertos_d1 = int(
                        float(
                            row.get(
                                "ABERTOS_D1",
                                0
                            )
                            or 0
                        )
                    )

                except:
                    abertos_d1 = 0

                if abertos_d1 > 0:

                    return (
                        f"Em aberto ({abertos_d1})"
                    )

                # ----------------------------------------------
                # Pacotes de operações anteriores
                # ----------------------------------------------

                try:
                    permanecem = int(
                        float(
                            row.get(
                                "PERMANECEM_ABERTOS",
                                0
                            )
                            or 0
                        )
                    )

                except:
                    permanecem = 0

                if permanecem > 0:

                    return (
                        f"Em aberto ({permanecem})"
                    )

                return "-"

            # ==================================================
            # APLICA NA BASE COMPLETA
            # ==================================================

            if not base.empty:

                base[
                    "RESUMO_OCORRENCIAS"
                ] = base.apply(
                    ajustar_resumo_ocorrencias,
                    axis=1
                )

            # ==================================================
            # APLICA NOS OFENSORES
            #
            # IMPORTANTE:
            # fazemos isso aqui porque "ofensores" é o dataframe
            # enviado posteriormente para o Google Sheets.
            # ==================================================

            if not ofensores.empty:

                ofensores[
                    "RESUMO_OCORRENCIAS"
                ] = ofensores.apply(
                    ajustar_resumo_ocorrencias,
                    axis=1
                )

            # ==================================================
            # CABEÇALHO DA OPERAÇÃO
            # ==================================================

            st.success(
                "Forward Order processado com sucesso."
            )

            st.markdown(
                f"""
### Operação {data_referencia.strftime("%d/%m/%Y")}
                """
            )

            # ==================================================
            # NÚMEROS GERAIS
            # ==================================================

            total_motoristas = (
                base[
                    "DRIVER_ID"
                ].nunique()
            )

            total_ofensores = (
                ofensores[
                    "DRIVER_ID"
                ].nunique()
            )

            total_onhold = int(
                base[
                    "ONHOLD"
                ].sum()
            )

            total_abertos = int(
                base[
                    "ABERTOS_D1"
                ].sum()
            )

            total_antigos = int(
                base[
                    "PERMANECEM_ABERTOS"
                ].sum()
            )

            # ==================================================
            # PRIMEIRA LINHA DE CARDS
            # ==================================================

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "Motoristas analisados",
                total_motoristas
            )

            c2.metric(
                "Motoristas ofensores",
                total_ofensores
            )

            c3.metric(
                "Ocorrências",
                total_onhold
            )

            c4.metric(
                "Em aberto D-1",
                total_abertos
            )

            # ==================================================
            # TOTAL REAL DA OPERAÇÃO
            # ==================================================

            df_carga_metricas = (
                df_carregamentos.copy()
            )

            df_carga_metricas[
                "DATA_DT"
            ] = pd.to_datetime(
                df_carga_metricas[
                    "DATA"
                ],
                errors="coerce",
                dayfirst=True
            ).dt.date

            df_carga_dia = (
                df_carga_metricas[
                    df_carga_metricas[
                        "DATA_DT"
                    ]
                    == data_referencia
                ]
                .copy()
            )

            df_carga_dia[
                "PACOTES_CARREGADOS"
            ] = pd.to_numeric(
                df_carga_dia[
                    "PACOTES_CARREGADOS"
                ],
                errors="coerce"
            ).fillna(0)

            total_carga = int(
                df_carga_dia[
                    "PACOTES_CARREGADOS"
                ].sum()
            )

            # ==================================================
            # INDICADORES
            # ==================================================

            if total_carga > 0:

                taxa_onhold = (
                    total_onhold
                    / total_carga
                    * 100
                )

                taxa_abertos = (
                    total_abertos
                    / total_carga
                    * 100
                )

                total_sucesso = (
                    total_carga
                    - total_onhold
                    - total_abertos
                )

                d0 = (
                    total_sucesso
                    / total_carga
                    * 100
                )

            else:

                taxa_onhold = 0
                taxa_abertos = 0
                total_sucesso = 0
                d0 = 0

            # ==================================================
            # SEGUNDA LINHA DE CARDS
            # ==================================================

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "Pacotes expedidos",
                f"{total_carga:,}".replace(
                    ",",
                    "."
                )
            )

            c2.metric(
                "% ocorrência",
                f"{taxa_onhold:.2f}%"
            )

            c3.metric(
                "% em aberto",
                f"{taxa_abertos:.2f}%"
            )

            c4.metric(
                "DS - Estimado",
                f"{d0:.2f}%"
            )

            # ==================================================
            # ALERTA ANTIGOS
            # ==================================================

            if total_antigos > 0:

                st.warning(
                    f"🚨 {total_antigos} pacotes "
                    "permanecem em aberto de operações anteriores."
                )

            st.divider()

            # ==================================================
            # TOP OCORRÊNCIAS
            # ==================================================

            st.subheader(
                "⚠️ Top ocorrências"
            )

            st.caption(
                "Motoristas com mais de 5 ocorrências no dia."
            )

            top_ocorrencias = (
                ofensores[
                    ofensores[
                        "OFENSOR_OCORRENCIA"
                    ]
                ]
                .sort_values(
                    [
                        "ONHOLD",
                        "PERCENTUAL_OCORRENCIA"
                    ],
                    ascending=False
                )
            )

            if top_ocorrencias.empty:

                st.success(
                    "Nenhum motorista ultrapassou "
                    "o limite de ocorrências."
                )

            else:

                st.dataframe(
                    top_ocorrencias,
                    column_order=[
                        "DRIVER_NAME",
                        "PACOTES_CARREGADOS",
                        "ONHOLD",
                        "PERCENTUAL_OCORRENCIA",
                        "REALIZACAO_ROTA",
                        "RESUMO_OCORRENCIAS",
                        "CLUSTER",
                        "PACOTES_AREA_RISCO",
                        "PERCENTUAL_AREA_RISCO",
                        "HORA_CARREGAMENTO",
                    ],
                    column_config={

                        "DRIVER_NAME":
                            "Motorista",

                        "PACOTES_CARREGADOS":
                            "Carga",

                        "ONHOLD":
                            "Ocorrências",

                        "PERCENTUAL_OCORRENCIA":
                            st.column_config.NumberColumn(
                                "% Ocorrência",
                                format="%.1f%%"
                            ),

                        "REALIZACAO_ROTA":
                            st.column_config.ProgressColumn(
                                "Realização",
                                min_value=0,
                                max_value=100,
                                format="%.1f%%"
                            ),

                        "RESUMO_OCORRENCIAS":
                            st.column_config.TextColumn(
                                "Resumo das ocorrências",
                                width="large"
                            ),

                        "CLUSTER":
                            "Cluster",

                        "PACOTES_AREA_RISCO":
                            "Área de risco",

                        "PERCENTUAL_AREA_RISCO":
                            st.column_config.NumberColumn(
                                "% Risco",
                                format="%.1f%%"
                            ),

                        "HORA_CARREGAMENTO":
                            "Carregou",
                    },
                    use_container_width=True,
                    hide_index=True,
                    height=430
                )

            st.divider()

            # ==================================================
            # TOP ABERTOS D-1
            # ==================================================

            st.subheader(
                "📦 Top pacotes em aberto"
            )

            st.caption(
                "Motoristas com mais de 10 pacotes "
                "em aberto na operação analisada."
            )

            top_abertos = (
                ofensores[
                    ofensores[
                        "OFENSOR_ABERTO_D1"
                    ]
                ]
                .sort_values(
                    [
                        "ABERTOS_D1",
                        "PERCENTUAL_ABERTO"
                    ],
                    ascending=False
                )
            )

            if top_abertos.empty:

                st.success(
                    "Nenhum motorista ultrapassou "
                    "o limite de pacotes em aberto."
                )

            else:

                st.dataframe(
                    top_abertos,
                    column_order=[
                        "DRIVER_NAME",
                        "PACOTES_CARREGADOS",
                        "ABERTOS_D1",
                        "PERCENTUAL_ABERTO",
                        "ONHOLD",
                        "RESUMO_OCORRENCIAS",
                        "REALIZACAO_ROTA",
                        "CLUSTER",
                        "PACOTES_AREA_RISCO",
                        "PERCENTUAL_AREA_RISCO",
                        "HORA_CARREGAMENTO",
                    ],
                    column_config={

                        "DRIVER_NAME":
                            "Motorista",

                        "PACOTES_CARREGADOS":
                            "Carga",

                        "ABERTOS_D1":
                            "Em aberto",

                        "PERCENTUAL_ABERTO":
                            st.column_config.NumberColumn(
                                "% Em aberto",
                                format="%.1f%%"
                            ),

                        "ONHOLD":
                            "Ocorrências",

                        "RESUMO_OCORRENCIAS":
                            st.column_config.TextColumn(
                                "Resumo das ocorrências",
                                width="large"
                            ),

                        "REALIZACAO_ROTA":
                            st.column_config.ProgressColumn(
                                "Realização",
                                min_value=0,
                                max_value=100,
                                format="%.1f%%"
                            ),

                        "CLUSTER":
                            "Cluster",

                        "PACOTES_AREA_RISCO":
                            "Área de risco",

                        "PERCENTUAL_AREA_RISCO":
                            st.column_config.NumberColumn(
                                "% Risco",
                                format="%.1f%%"
                            ),

                        "HORA_CARREGAMENTO":
                            "Carregou",
                    },
                    use_container_width=True,
                    hide_index=True,
                    height=430
                )

            # ==================================================
            # PERMANECEM EM ABERTO
            # ==================================================

            antigos = (
                ofensores[
                    ofensores[
                        "OFENSOR_ABERTO_ANTIGO"
                    ]
                ]
                .sort_values(
                    "PERMANECEM_ABERTOS",
                    ascending=False
                )
            )

            if not antigos.empty:

                st.divider()

                st.subheader(
                    "🚨 Pacotes que permanecem em aberto"
                )

                st.caption(
                    "Mais de 10 pacotes ainda em aberto "
                    "de operações anteriores."
                )

                st.dataframe(
                    antigos,
                    column_order=[
                        "DRIVER_NAME",
                        "PERMANECEM_ABERTOS",
                        "RESUMO_OCORRENCIAS",
                        "DESDE",
                        "CLUSTER",
                    ],
                    column_config={

                        "DRIVER_NAME":
                            "Motorista",

                        "PERMANECEM_ABERTOS":
                            "Pacotes em aberto",

                        "RESUMO_OCORRENCIAS":
                            st.column_config.TextColumn(
                                "Resumo das ocorrências",
                                width="large"
                            ),

                        "DESDE":
                            "Desde",

                        "CLUSTER":
                            "Último cluster",
                    },
                    use_container_width=True,
                    hide_index=True
                )

            # ==================================================
            # TODOS OS OFENSORES
            # ==================================================

            st.divider()

            with st.expander(
                f"Ver todos os {total_ofensores} ofensores"
            ):

                st.dataframe(
                    ofensores,
                    column_order=[
                        "DRIVER_ID",
                        "DRIVER_NAME",
                        "PACOTES_CARREGADOS",
                        "ONHOLD",
                        "RESUMO_OCORRENCIAS",
                        "ABERTOS_D1",
                        "PERMANECEM_ABERTOS",
                        "DESDE",
                        "REALIZACAO_ROTA",
                        "CLUSTER",
                        "PACOTES_AREA_RISCO",
                        "PERCENTUAL_AREA_RISCO",
                        "HORA_CARREGAMENTO",
                    ],
                    column_config={

                        "DRIVER_ID":
                            "ID",

                        "DRIVER_NAME":
                            "Motorista",

                        "PACOTES_CARREGADOS":
                            "Carga",

                        "ONHOLD":
                            "Ocorrências",

                        "RESUMO_OCORRENCIAS":
                            st.column_config.TextColumn(
                                "Resumo das ocorrências",
                                width="large"
                            ),

                        "ABERTOS_D1":
                            "Em aberto D-1",

                        "PERMANECEM_ABERTOS":
                            "Permanecem em aberto",

                        "DESDE":
                            "Desde",

                        "REALIZACAO_ROTA":
                            st.column_config.ProgressColumn(
                                "Realização",
                                min_value=0,
                                max_value=100,
                                format="%.1f%%"
                            ),

                        "CLUSTER":
                            "Cluster",

                        "PACOTES_AREA_RISCO":
                            "Área de risco",

                        "PERCENTUAL_AREA_RISCO":
                            st.column_config.NumberColumn(
                                "% Risco",
                                format="%.1f%%"
                            ),

                        "HORA_CARREGAMENTO":
                            "Carregou",
                    },
                    use_container_width=True,
                    hide_index=True,
                    height=500
                )

        except Exception as e:

            st.error(
                "Erro ao analisar o Forward Order."
            )

            st.exception(e)

        # ======================================================
        # SALVAR ANÁLISE
        # ======================================================

        st.divider()

        st.subheader(
            "Salvar análise"
        )

        st.caption(
            "Grava os motoristas ofensores desta operação "
            "na base histórica."
        )

        if ofensores.empty:

            st.info(
                "Nenhum motorista atingiu os critérios "
                "de ofensa nesta operação."
            )

        else:

            if st.button(
                "💾 Salvar ofensores",
                use_container_width=True,
                type="primary"
            ):

                try:

                    with st.spinner(
                        "Salvando ofensores..."
                    ):

                        resultado_salvamento = (
                            salvar_ofensores_sem_duplicar(
                                ofensores
                            )
                        )

                    salvos = (
                        resultado_salvamento[
                            "salvos"
                        ]
                    )

                    duplicados = (
                        resultado_salvamento[
                            "duplicados"
                        ]
                    )

                    if salvos > 0:

                        st.success(
                            f"{salvos} ofensores "
                            "salvos com sucesso."
                        )

                    if duplicados > 0:

                        st.info(
                            f"{duplicados} registros já existiam "
                            "para esta data e motorista."
                        )

                except Exception as e:

                    st.error(
                        "Erro ao salvar os ofensores."
                    )

                    st.exception(e)



# ==========================================================
# HISTÓRICO
# ==========================================================

elif pagina == "Histórico":

    st.title("Histórico de Ofensores")

    st.caption(
        "Análise de reincidência, persistência e comportamento "
        "operacional dos motoristas."
    )

    st.divider()

    try:

        # ======================================================
        # CARREGAR BASES
        # ======================================================

        with st.spinner(
            "Carregando histórico e dados de carregamento..."
        ):

            df_historico = carregar_dados_aba(
                "DADOS DE OFENSORES"
            )

            df_carregamentos_hist = carregar_dados_aba(
                "DADOS DE CARREGAMENTO"
            )

        if df_historico.empty:

            st.info(
                "Ainda não existem registros no histórico."
            )

        else:

            # ==================================================
            # CÓPIAS
            # ==================================================

            df_historico = (
                df_historico.copy()
            )

            df_carregamentos_hist = (
                df_carregamentos_hist.copy()
            )

            # ==================================================
            # GARANTIR COLUNAS HISTÓRICO
            # ==================================================

            colunas_padrao = {

                "DATA": "",

                "DRIVER_ID": "",

                "DRIVER_NAME": "",

                "CARREGAMENTOS": 0,

                "PACOTES_CARREGADOS": 0,

                "ONHOLD": 0,

                "PERCENTUAL_OCORRENCIA": 0,

                "ABERTOS_D1": 0,

                "PERCENTUAL_ABERTO": 0,

                "PERMANECEM_ABERTOS": 0,

                "DESDE": "",

                "RESUMO_OCORRENCIAS": "",

                "CLUSTER": "",

                "HORA_CARREGAMENTO": "",

                "PACOTES_AREA_RISCO": 0,

                "PERCENTUAL_AREA_RISCO": 0,

                "REALIZACAO_ROTA": 0,
            }

            for (
                coluna,
                valor_padrao
            ) in colunas_padrao.items():

                if (
                    coluna
                    not in df_historico.columns
                ):

                    df_historico[
                        coluna
                    ] = valor_padrao

            # ==================================================
            # GARANTIR COLUNAS CARREGAMENTO
            # ==================================================

            colunas_carga_padrao = {

                "TASK_ID": "",

                "DRIVER_ID": "",

                "DRIVER_NAME": "",

                "DATA": "",

                "CLUSTER": "",

                "PACOTES_CARREGADOS": 0,

                "PACOTES_AREA_RISCO": 0,
            }

            for (
                coluna,
                valor_padrao
            ) in colunas_carga_padrao.items():

                if (
                    coluna
                    not in
                    df_carregamentos_hist.columns
                ):

                    df_carregamentos_hist[
                        coluna
                    ] = valor_padrao

            # ==================================================
            # DATAS HISTÓRICO
            # ==================================================

            df_historico[
                "DATA_DT"
            ] = pd.to_datetime(
                df_historico[
                    "DATA"
                ],
                errors="coerce",
                dayfirst=True
            )

            df_historico[
                "DESDE_DT"
            ] = pd.to_datetime(
                df_historico[
                    "DESDE"
                ],
                errors="coerce",
                dayfirst=True
            )

            df_historico = (
                df_historico[
                    df_historico[
                        "DATA_DT"
                    ].notna()
                ]
                .copy()
            )

            # ==================================================
            # DATA CARREGAMENTO
            # ==================================================

            df_carregamentos_hist[
                "DATA_DT"
            ] = pd.to_datetime(
                df_carregamentos_hist[
                    "DATA"
                ],
                errors="coerce",
                dayfirst=True
            )

            df_carregamentos_hist = (
                df_carregamentos_hist[
                    df_carregamentos_hist[
                        "DATA_DT"
                    ].notna()
                ]
                .copy()
            )

            # ==================================================
            # NUMÉRICOS HISTÓRICO
            # ==================================================

            colunas_numericas = [

                "CARREGAMENTOS",

                "PACOTES_CARREGADOS",

                "ONHOLD",

                "PERCENTUAL_OCORRENCIA",

                "ABERTOS_D1",

                "PERCENTUAL_ABERTO",

                "PERMANECEM_ABERTOS",

                "PACOTES_AREA_RISCO",

                "PERCENTUAL_AREA_RISCO",

                "REALIZACAO_ROTA",
            ]

            for coluna in (
                colunas_numericas
            ):

                df_historico[
                    coluna
                ] = (
                    pd.to_numeric(
                        df_historico[
                            coluna
                        ],
                        errors="coerce"
                    )
                    .fillna(0)
                )

            # ==================================================
            # NUMÉRICOS CARREGAMENTO
            # ==================================================

            for coluna in [
                "PACOTES_CARREGADOS",
                "PACOTES_AREA_RISCO",
            ]:

                df_carregamentos_hist[
                    coluna
                ] = (
                    pd.to_numeric(
                        df_carregamentos_hist[
                            coluna
                        ],
                        errors="coerce"
                    )
                    .fillna(0)
                )

            # ==================================================
            # NORMALIZAR DRIVER HISTÓRICO
            # ==================================================

            df_historico[
                "DRIVER_ID"
            ] = (
                df_historico[
                    "DRIVER_ID"
                ]
                .astype(str)
                .str.replace(
                    r"\.0$",
                    "",
                    regex=True
                )
                .str.strip()
            )

            df_historico[
                "DRIVER_NAME"
            ] = (
                df_historico[
                    "DRIVER_NAME"
                ]
                .fillna("")
                .astype(str)
                .str.strip()
            )

            # ==================================================
            # NORMALIZAR DRIVER CARREGAMENTO
            # ==================================================

            df_carregamentos_hist[
                "DRIVER_ID"
            ] = (
                df_carregamentos_hist[
                    "DRIVER_ID"
                ]
                .astype(str)
                .str.replace(
                    r"\.0$",
                    "",
                    regex=True
                )
                .str.strip()
            )

            df_carregamentos_hist[
                "DRIVER_NAME"
            ] = (
                df_carregamentos_hist[
                    "DRIVER_NAME"
                ]
                .fillna("")
                .astype(str)
                .str.strip()
            )

            # ==================================================
            # CLUSTER
            # ==================================================

            df_historico[
                "CLUSTER"
            ] = (
                df_historico[
                    "CLUSTER"
                ]
                .fillna("")
                .astype(str)
                .str.strip()
            )

            df_carregamentos_hist[
                "CLUSTER"
            ] = (
                df_carregamentos_hist[
                    "CLUSTER"
                ]
                .fillna("")
                .astype(str)
                .str.strip()
            )

            # ==================================================
            # TASK ID
            # ==================================================

            df_carregamentos_hist[
                "TASK_ID"
            ] = (
                df_carregamentos_hist[
                    "TASK_ID"
                ]
                .astype(str)
                .str.replace(
                    r"\.0$",
                    "",
                    regex=True
                )
                .str.strip()
            )

            # ==================================================
            # RESUMO PARA EXIBIÇÃO
            #
            # Exemplos:
            #
            # Comércio fechado (8)
            #
            # Em aberto (86)
            #
            # Disaster (7), Cliente ausente (1), Em aberto (14)
            # ==================================================

            def ajustar_resumo_historico(
                row
            ):

                resumo = row.get(
                    "RESUMO_OCORRENCIAS",
                    ""
                )

                if pd.isna(
                    resumo
                ):

                    resumo = ""

                resumo = str(
                    resumo
                ).strip()

                # ==============================================
                # ABERTOS D-1
                # ==============================================

                try:

                    abertos = int(
                        float(
                            row.get(
                                "ABERTOS_D1",
                                0
                            )
                            or 0
                        )
                    )

                except:

                    abertos = 0

                # ==============================================
                # PERSISTENTES
                # ==============================================

                try:

                    persistentes = int(
                        float(
                            row.get(
                                "PERMANECEM_ABERTOS",
                                0
                            )
                            or 0
                        )
                    )

                except:

                    persistentes = 0

                # ==============================================
                # TEM RESUMO
                # ==============================================

                possui_resumo = (
                    resumo
                    and resumo.lower()
                    not in [
                        "nan",
                        "none",
                        "-"
                    ]
                )

                if possui_resumo:

                    # Remove Em aberto já existente para
                    # não duplicar o texto.

                    resumo_sem_aberto = (
                        re.sub(
                            r",?\s*Em aberto\s*\(\d+\)",
                            "",
                            resumo,
                            flags=re.IGNORECASE
                        )
                        .strip(
                            " ,"
                        )
                    )

                    # ------------------------------------------
                    # ONHOLD + ABERTO D-1
                    # ------------------------------------------

                    if abertos > 0:

                        return (
                            f"{resumo_sem_aberto}, "
                            f"Em aberto ({abertos})"
                        )

                    # ------------------------------------------
                    # ONHOLD + PERSISTÊNCIA
                    # ------------------------------------------

                    if persistentes > 0:

                        return (
                            f"{resumo_sem_aberto}, "
                            f"Em aberto ({persistentes})"
                        )

                    return (
                        resumo_sem_aberto
                    )

                # ==============================================
                # SOMENTE ABERTO
                # ==============================================

                if abertos > 0:

                    return (
                        f"Em aberto ({abertos})"
                    )

                if persistentes > 0:

                    return (
                        f"Em aberto ({persistentes})"
                    )

                return "-"

            df_historico[
                "RESUMO_EXIBICAO"
            ] = (
                df_historico.apply(
                    ajustar_resumo_historico,
                    axis=1
                )
            )

            # ==================================================
            # CLASSIFICAÇÃO
            # ==================================================

            df_historico[
                "NOVA_OFENSA"
            ] = (
                (
                    df_historico[
                        "CARREGAMENTOS"
                    ]
                    > 0
                )
                &
                (
                    (
                        df_historico[
                            "ONHOLD"
                        ]
                        > 5
                    )
                    |
                    (
                        df_historico[
                            "ABERTOS_D1"
                        ]
                        > 10
                    )
                )
            )

            df_historico[
                "PERSISTENCIA_ABERTO"
            ] = (
                df_historico[
                    "PERMANECEM_ABERTOS"
                ]
                > 10
            )

            # ==================================================
            # TIPO DE REGISTRO
            # ==================================================

            df_historico[
                "TIPO_REGISTRO"
            ] = "-"

            df_historico.loc[
                df_historico[
                    "NOVA_OFENSA"
                ],
                "TIPO_REGISTRO"
            ] = (
                "Nova ofensa"
            )

            df_historico.loc[
                (
                    ~df_historico[
                        "NOVA_OFENSA"
                    ]
                )
                &
                (
                    df_historico[
                        "PERSISTENCIA_ABERTO"
                    ]
                ),
                "TIPO_REGISTRO"
            ] = (
                "Persistência"
            )

            df_historico.loc[
                (
                    df_historico[
                        "NOVA_OFENSA"
                    ]
                )
                &
                (
                    df_historico[
                        "PERSISTENCIA_ABERTO"
                    ]
                ),
                "TIPO_REGISTRO"
            ] = (
                "Nova ofensa + persistência"
            )

            # ==================================================
            # DIAS DE PERSISTÊNCIA
            # ==================================================

            df_historico[
                "DIAS_PERSISTENCIA"
            ] = 0

            possui_desde = (
                df_historico[
                    "DESDE_DT"
                ].notna()
            )

            df_historico.loc[
                possui_desde,
                "DIAS_PERSISTENCIA"
            ] = (
                (
                    df_historico.loc[
                        possui_desde,
                        "DATA_DT"
                    ]
                    -
                    df_historico.loc[
                        possui_desde,
                        "DESDE_DT"
                    ]
                )
                .dt.days
                .clip(
                    lower=0
                )
            )

            # ==================================================
            # PERÍODO DISPONÍVEL
            # ==================================================

            data_minima = (
                df_historico[
                    "DATA_DT"
                ]
                .min()
                .date()
            )

            data_maxima = (
                df_historico[
                    "DATA_DT"
                ]
                .max()
                .date()
            )

            # ==================================================
            # FILTROS
            # ==================================================

            st.subheader(
                "Filtros"
            )

            col_periodo, col_driver = (
                st.columns(
                    [2, 1]
                )
            )

            # ==================================================
            # PERÍODO
            # ==================================================

            with col_periodo:

                periodo = (
                    st.date_input(
                        "Período de análise",
                        value=(
                            data_minima,
                            data_maxima
                        ),
                        min_value=(
                            data_minima
                        ),
                        max_value=(
                            data_maxima
                        ),
                        format=(
                            "DD/MM/YYYY"
                        ),
                        key=(
                            "periodo_historico"
                        )
                    )
                )

            if (
                isinstance(
                    periodo,
                    (tuple, list)
                )
                and len(
                    periodo
                ) == 2
            ):

                data_inicio = (
                    periodo[0]
                )

                data_fim = (
                    periodo[1]
                )

            elif (
                isinstance(
                    periodo,
                    (tuple, list)
                )
                and len(
                    periodo
                ) == 1
            ):

                data_inicio = (
                    periodo[0]
                )

                data_fim = (
                    periodo[0]
                )

            else:

                data_inicio = (
                    periodo
                )

                data_fim = (
                    periodo
                )

            # ==================================================
            # BUSCA DRIVER
            # ==================================================

            with col_driver:

                busca_driver = (
                    st.text_input(
                        "Motorista",
                        placeholder=(
                            "ID ou nome"
                        ),
                        key=(
                            "filtro_driver_historico"
                        )
                    )
                )

            # ==================================================
            # FILTRAR HISTÓRICO PELO PERÍODO
            # ==================================================

            df_periodo = (
                df_historico[
                    (
                        df_historico[
                            "DATA_DT"
                        ].dt.date
                        >= data_inicio
                    )
                    &
                    (
                        df_historico[
                            "DATA_DT"
                        ].dt.date
                        <= data_fim
                    )
                ]
                .copy()
            )

            # ==================================================
            # FILTRAR CARREGAMENTOS PELO MESMO PERÍODO
            #
            # ESSA BASE É USADA PARA CONTAR EXPEDIÇÕES REAIS
            # ==================================================

            df_carga_periodo = (
                df_carregamentos_hist[
                    (
                        df_carregamentos_hist[
                            "DATA_DT"
                        ].dt.date
                        >= data_inicio
                    )
                    &
                    (
                        df_carregamentos_hist[
                            "DATA_DT"
                        ].dt.date
                        <= data_fim
                    )
                ]
                .copy()
            )

            # ==================================================
            # BUSCA DRIVER
            # ==================================================

            if busca_driver:

                busca = (
                    busca_driver
                    .strip()
                    .lower()
                )

                # ----------------------------------------------
                # HISTÓRICO
                # ----------------------------------------------

                df_periodo = (
                    df_periodo[
                        (
                            df_periodo[
                                "DRIVER_ID"
                            ]
                            .str.lower()
                            .str.contains(
                                busca,
                                na=False,
                                regex=False
                            )
                        )
                        |
                        (
                            df_periodo[
                                "DRIVER_NAME"
                            ]
                            .str.lower()
                            .str.contains(
                                busca,
                                na=False,
                                regex=False
                            )
                        )
                    ]
                    .copy()
                )

                # ----------------------------------------------
                # CARREGAMENTOS
                #
                # Dessa forma, ao filtrar um motorista,
                # "Expedições" passa a representar as
                # expedições daquele motorista.
                # ----------------------------------------------

                df_carga_periodo = (
                    df_carga_periodo[
                        (
                            df_carga_periodo[
                                "DRIVER_ID"
                            ]
                            .str.lower()
                            .str.contains(
                                busca,
                                na=False,
                                regex=False
                            )
                        )
                        |
                        (
                            df_carga_periodo[
                                "DRIVER_NAME"
                            ]
                            .str.lower()
                            .str.contains(
                                busca,
                                na=False,
                                regex=False
                            )
                        )
                    ]
                    .copy()
                )

            # ==================================================
            # CLUSTERS DISPONÍVEIS
            # ==================================================

            clusters_disponiveis = (
                set()
            )

            for valor in (
                df_historico[
                    "CLUSTER"
                ]
                .fillna("")
            ):

                for cluster in str(
                    valor
                ).split(","):

                    cluster = (
                        cluster.strip()
                    )

                    if (
                        cluster
                        and cluster.lower()
                        not in [
                            "nan",
                            "none",
                            "-"
                        ]
                    ):

                        clusters_disponiveis.add(
                            cluster
                        )

            # Também considera os clusters
            # existentes na base de carregamento.

            for valor in (
                df_carregamentos_hist[
                    "CLUSTER"
                ]
                .fillna("")
            ):

                for cluster in str(
                    valor
                ).split(","):

                    cluster = (
                        cluster.strip()
                    )

                    if (
                        cluster
                        and cluster.lower()
                        not in [
                            "nan",
                            "none",
                            "-"
                        ]
                    ):

                        clusters_disponiveis.add(
                            cluster
                        )

            clusters_disponiveis = (
                sorted(
                    clusters_disponiveis
                )
            )

            # ==================================================
            # SEGUNDA LINHA DE FILTROS
            # ==================================================

            col_cluster, col_tipo = (
                st.columns(2)
            )

            with col_cluster:

                filtro_clusters = (
                    st.multiselect(
                        "Cluster",
                        options=(
                            clusters_disponiveis
                        ),
                        placeholder=(
                            "Todos os clusters"
                        ),
                        key=(
                            "filtro_cluster_historico"
                        )
                    )
                )

            with col_tipo:

                filtro_tipo = (
                    st.multiselect(
                        "Tipo de registro",
                        options=[
                            "Nova ofensa",
                            "Persistência",
                            (
                                "Nova ofensa "
                                "+ persistência"
                            ),
                        ],
                        placeholder=(
                            "Todos os tipos"
                        ),
                        key=(
                            "filtro_tipo_historico"
                        )
                    )
                )

            # ==================================================
            # FUNÇÃO FILTRO CLUSTER
            # ==================================================

            def registro_tem_cluster(
                valor,
                clusters_filtro
            ):

                clusters_registro = [
                    x.strip()
                    for x
                    in str(
                        valor
                    ).split(",")
                ]

                return any(
                    cluster
                    in clusters_registro
                    for cluster
                    in clusters_filtro
                )

            # ==================================================
            # APLICAR CLUSTER
            # ==================================================

            if filtro_clusters:

                df_periodo = (
                    df_periodo[
                        df_periodo[
                            "CLUSTER"
                        ].apply(
                            lambda valor:
                            registro_tem_cluster(
                                valor,
                                filtro_clusters
                            )
                        )
                    ]
                    .copy()
                )

                df_carga_periodo = (
                    df_carga_periodo[
                        df_carga_periodo[
                            "CLUSTER"
                        ].apply(
                            lambda valor:
                            registro_tem_cluster(
                                valor,
                                filtro_clusters
                            )
                        )
                    ]
                    .copy()
                )

            # ==================================================
            # APLICAR TIPO
            # ==================================================

            if filtro_tipo:

                df_periodo = (
                    df_periodo[
                        df_periodo[
                            "TIPO_REGISTRO"
                        ].isin(
                            filtro_tipo
                        )
                    ]
                    .copy()
                )

            # ==================================================
            # FILTROS ATIVOS
            # ==================================================

            filtros_ativos = []

            if busca_driver:

                filtros_ativos.append(
                    f"Motorista: "
                    f"{busca_driver}"
                )

            if filtro_clusters:

                filtros_ativos.append(
                    "Cluster: "
                    + ", ".join(
                        filtro_clusters
                    )
                )

            if filtro_tipo:

                filtros_ativos.append(
                    "Tipo: "
                    + ", ".join(
                        filtro_tipo
                    )
                )

            if filtros_ativos:

                st.caption(
                    " • ".join(
                        filtros_ativos
                    )
                )

            st.divider()

            # ==================================================
            # SEM REGISTROS
            # ==================================================

            if df_periodo.empty:

                st.warning(
                    "Nenhum registro de ofensor encontrado "
                    "com os filtros selecionados."
                )

            else:

                st.caption(
                    f"Período analisado: "
                    f"{data_inicio.strftime('%d/%m/%Y')} "
                    f"até "
                    f"{data_fim.strftime('%d/%m/%Y')}"
                )

                # ==================================================
                # SEGREGAR
                # ==================================================

                df_novas_ofensas = (
                    df_periodo[
                        df_periodo[
                            "NOVA_OFENSA"
                        ]
                    ]
                    .copy()
                )

                df_persistencias = (
                    df_periodo[
                        df_periodo[
                            "PERSISTENCIA_ABERTO"
                        ]
                    ]
                    .copy()
                )

                # ==================================================
                # MÉTRICAS
                # ==================================================

                ofensores_unicos = (
                    df_novas_ofensas[
                        "DRIVER_ID"
                    ].nunique()
                )

                registros_ofensores = (
                    len(
                        df_novas_ofensas
                    )
                )

                ocorrencias_periodo = int(
                    df_novas_ofensas[
                        "ONHOLD"
                    ].sum()
                )

                abertos_periodo = int(
                    df_novas_ofensas[
                        "ABERTOS_D1"
                    ].sum()
                )

                pacotes_periodo = int(
                    df_novas_ofensas[
                        "PACOTES_CARREGADOS"
                    ].sum()
                )

                # ==================================================
                # REINCIDÊNCIA
                # ==================================================

                if not df_novas_ofensas.empty:

                    operacoes_por_driver = (
                        df_novas_ofensas
                        .groupby(
                            "DRIVER_ID"
                        )[
                            "DATA_DT"
                        ]
                        .nunique()
                    )

                    drivers_reincidentes = (
                        int(
                            (
                                operacoes_por_driver
                                > 1
                            ).sum()
                        )
                    )

                    total_reincidencias = (
                        int(
                            (
                                operacoes_por_driver
                                - 1
                            )
                            .clip(
                                lower=0
                            )
                            .sum()
                        )
                    )

                else:

                    operacoes_por_driver = (
                        pd.Series(
                            dtype="int64"
                        )
                    )

                    drivers_reincidentes = 0

                    total_reincidencias = 0

                taxa_reincidencia = (
                    drivers_reincidentes
                    / ofensores_unicos
                    * 100
                    if ofensores_unicos > 0
                    else 0
                )

                # ==================================================
                # PERSISTÊNCIA
                # ==================================================

                motoristas_persistentes = (
                    df_persistencias[
                        "DRIVER_ID"
                    ].nunique()
                )

                pacotes_persistentes = int(
                    df_persistencias[
                        "PERMANECEM_ABERTOS"
                    ].sum()
                )

                maior_persistencia = (
                    int(
                        df_persistencias[
                            "DIAS_PERSISTENCIA"
                        ].max()
                    )
                    if not df_persistencias.empty
                    else 0
                )

                # ==================================================
                # D0
                # ==================================================

                if pacotes_periodo > 0:

                    pacotes_sucesso = (
                        max(
                            pacotes_periodo
                            - ocorrencias_periodo
                            - abertos_periodo,
                            0
                        )
                    )

                    d0_periodo = (
                        pacotes_sucesso
                        / pacotes_periodo
                        * 100
                    )

                else:

                    d0_periodo = 0

                # ==================================================
                # CARDS
                # ==================================================

                c1, c2, c3, c4 = (
                    st.columns(4)
                )

                c1.metric(
                    "Ofensores únicos",
                    ofensores_unicos
                )

                c2.metric(
                    "Registros ofensores",
                    registros_ofensores
                )

                c3.metric(
                    "Drivers reincidentes",
                    drivers_reincidentes,
                    delta=(
                        f"{taxa_reincidencia:.1f}%"
                    ),
                    delta_color="off"
                )

                c4.metric(
                    "D0 dos ofensores",
                    f"{d0_periodo:.2f}%"
                )

                c1, c2, c3, c4 = (
                    st.columns(4)
                )

                c1.metric(
                    "Reincidências",
                    total_reincidencias
                )

                c2.metric(
                    "Ocorrências",
                    ocorrencias_periodo
                )

                c3.metric(
                    "Em aberto D-1",
                    abertos_periodo
                )

                c4.metric(
                    "Pacotes analisados",
                    f"{pacotes_periodo:,}"
                    .replace(
                        ",",
                        "."
                    )
                )

                st.divider()

                # ==================================================
                # PRINCIPAIS MOTIVOS
                # ==================================================

                motivos_somados = {}

                for resumo in (
                    df_periodo[
                        "RESUMO_EXIBICAO"
                    ]
                    .fillna("")
                ):

                    resumo = str(
                        resumo
                    ).strip()

                    if (
                        not resumo
                        or resumo.lower()
                        in [
                            "nan",
                            "none",
                            "-"
                        ]
                    ):

                        continue

                    encontrados = (
                        re.findall(
                            r"([^,]+?)\s*\((\d+)\)",
                            resumo
                        )
                    )

                    for (
                        motivo,
                        quantidade
                    ) in encontrados:

                        motivo = (
                            motivo.strip()
                        )

                        if (
                            motivo.lower()
                            .startswith(
                                "em aberto"
                            )
                        ):

                            continue

                        quantidade = int(
                            quantidade
                        )

                        motivos_somados[
                            motivo
                        ] = (
                            motivos_somados
                            .get(
                                motivo,
                                0
                            )
                            + quantidade
                        )

                df_motivos = (
                    pd.DataFrame(
                        [
                            {
                                "MOTIVO":
                                    motivo,

                                "QUANTIDADE":
                                    quantidade,
                            }
                            for (
                                motivo,
                                quantidade
                            )
                            in motivos_somados.items()
                        ]
                    )
                )

                if not df_motivos.empty:

                    df_motivos = (
                        df_motivos
                        .sort_values(
                            "QUANTIDADE",
                            ascending=False
                        )
                        .reset_index(
                            drop=True
                        )
                    )

                st.subheader(
                    "Principais motivos de ocorrência"
                )

                st.caption(
                    "Motivos de OnHold acumulados "
                    "no período e filtros selecionados."
                )

                if df_motivos.empty:

                    st.info(
                        "Nenhum motivo de OnHold "
                        "encontrado."
                    )

                else:

                    top_3 = (
                        df_motivos
                        .head(3)
                        .to_dict(
                            "records"
                        )
                    )

                    col1, col2, col3 = (
                        st.columns(3)
                    )

                    cols_motivos = [
                        col1,
                        col2,
                        col3
                    ]

                    for indice, coluna in enumerate(
                        cols_motivos
                    ):

                        if (
                            indice
                            < len(
                                top_3
                            )
                        ):

                            coluna.metric(
                                top_3[
                                    indice
                                ][
                                    "MOTIVO"
                                ],
                                int(
                                    top_3[
                                        indice
                                    ][
                                        "QUANTIDADE"
                                    ]
                                )
                            )

                        else:

                            coluna.metric(
                                "-",
                                0
                            )

                    top_5 = (
                        df_motivos
                        .head(5)
                    )

                    resumo_top = ", ".join(
                        [
                            (
                                f"{row['MOTIVO']} "
                                f"({int(row['QUANTIDADE'])})"
                            )
                            for _, row
                            in top_5.iterrows()
                        ]
                    )

                    st.markdown(
                        f"**Maiores motivos:** "
                        f"{resumo_top}"
                    )

                    with st.expander(
                        "Ver todos os motivos"
                    ):

                        st.dataframe(
                            df_motivos,
                            column_config={

                                "MOTIVO":
                                    "Motivo",

                                "QUANTIDADE":
                                    "Ocorrências",
                            },
                            use_container_width=True,
                            hide_index=True,
                            height=350
                        )

                st.divider()

                # ==================================================
                # FUNÇÕES HORÁRIO
                # ==================================================

                def extrair_horas(
                    valor
                ):

                    if pd.isna(
                        valor
                    ):

                        return []

                    texto = str(
                        valor
                    )

                    horas = []

                    for parte in texto.split(
                        ","
                    ):

                        parte = (
                            parte.strip()
                        )

                        try:

                            hora = int(
                                parte.split(
                                    ":"
                                )[0]
                            )

                            if (
                                0
                                <= hora
                                <= 23
                            ):

                                horas.append(
                                    hora
                                )

                        except:

                            continue

                    return list(
                        dict.fromkeys(
                            horas
                        )
                    )

                def identificar_turno_hora(
                    hora
                ):

                    if 3 <= hora <= 10:

                        return "AM"

                    if 11 <= hora <= 21:

                        return "SD"

                    return (
                        "Fora da janela"
                    )

                def identificar_faixa(
                    hora
                ):

                    if 3 <= hora <= 5:
                        return "03:00 - 05:59"

                    if 6 <= hora <= 8:
                        return "06:00 - 08:59"

                    if 9 <= hora <= 10:
                        return "09:00 - 10:59"

                    if 11 <= hora <= 13:
                        return "11:00 - 13:59"

                    if 14 <= hora <= 16:
                        return "14:00 - 16:59"

                    if 17 <= hora <= 19:
                        return "17:00 - 19:59"

                    if 20 <= hora <= 21:
                        return "20:00 - 21:59"

                    return (
                        "Fora da janela"
                    )

                # ==================================================
                # HORÁRIOS DAS OFENSAS
                # ==================================================

                registros_horarios = []

                for _, row in (
                    df_novas_ofensas
                    .iterrows()
                ):

                    horas = (
                        extrair_horas(
                            row.get(
                                "HORA_CARREGAMENTO",
                                ""
                            )
                        )
                    )

                    for hora in horas:

                        registros_horarios.append(
                            {
                                "DRIVER_ID":
                                    row[
                                        "DRIVER_ID"
                                    ],

                                "DRIVER_NAME":
                                    row[
                                        "DRIVER_NAME"
                                    ],

                                "DATA_DT":
                                    row[
                                        "DATA_DT"
                                    ],

                                "HORA":
                                    hora,

                                "TURNO":
                                    identificar_turno_hora(
                                        hora
                                    ),

                                "FAIXA":
                                    identificar_faixa(
                                        hora
                                    ),
                            }
                        )

                df_horarios = (
                    pd.DataFrame(
                        registros_horarios
                    )
                )

                # ==================================================
                # TURNO CRÍTICO
                # ==================================================

                turno_critico = "-"
                qtd_turno_critico = 0

                if not df_horarios.empty:

                    resumo_turno_card = (
                        df_horarios[
                            df_horarios[
                                "TURNO"
                            ]
                            != "Fora da janela"
                        ]
                        .groupby(
                            "TURNO"
                        )[
                            "DRIVER_ID"
                        ]
                        .nunique()
                        .sort_values(
                            ascending=False
                        )
                    )

                    if not resumo_turno_card.empty:

                        turno_critico = (
                            resumo_turno_card
                            .index[0]
                        )

                        qtd_turno_critico = (
                            int(
                                resumo_turno_card
                                .iloc[0]
                            )
                        )

                # ==================================================
                # FAIXA CRÍTICA
                # ==================================================

                faixa_critica = "-"
                qtd_faixa_critica = 0

                if not df_horarios.empty:

                    resumo_faixa_card = (
                        df_horarios[
                            df_horarios[
                                "FAIXA"
                            ]
                            != "Fora da janela"
                        ]
                        .groupby(
                            "FAIXA"
                        )[
                            "DRIVER_ID"
                        ]
                        .nunique()
                        .sort_values(
                            ascending=False
                        )
                    )

                    if not resumo_faixa_card.empty:

                        faixa_critica = (
                            resumo_faixa_card
                            .index[0]
                        )

                        qtd_faixa_critica = (
                            int(
                                resumo_faixa_card
                                .iloc[0]
                            )
                        )

                # ==================================================
                # CLUSTERS DOS OFENSORES
                # ==================================================

                registros_clusters = []

                for _, row in (
                    df_novas_ofensas
                    .iterrows()
                ):

                    texto = str(
                        row.get(
                            "CLUSTER",
                            ""
                        )
                    )

                    clusters_linha = (
                        set()
                    )

                    for cluster in texto.split(
                        ","
                    ):

                        cluster = (
                            cluster.strip()
                        )

                        if (
                            cluster
                            and
                            cluster.lower()
                            not in [
                                "nan",
                                "none",
                                "-"
                            ]
                        ):

                            clusters_linha.add(
                                cluster
                            )

                    for cluster in (
                        clusters_linha
                    ):

                        registros_clusters.append(
                            {
                                "CLUSTER":
                                    cluster,

                                "DRIVER_ID":
                                    row[
                                        "DRIVER_ID"
                                    ],

                                "DATA_DT":
                                    row[
                                        "DATA_DT"
                                    ],
                            }
                        )

                df_clusters = (
                    pd.DataFrame(
                        registros_clusters
                    )
                )

                # ==================================================
                # EXPEDIÇÕES REAIS POR CLUSTER
                #
                # Cada TASK_ID representa um carregamento.
                #
                # Portanto:
                #
                # EXPEDIÇÕES =
                # quantidade de TASK_ID distintos
                # daquele cluster no período.
                # ==================================================

                expedicoes_clusters = []

                for _, row in (
                    df_carga_periodo
                    .iterrows()
                ):

                    task_id = str(
                        row.get(
                            "TASK_ID",
                            ""
                        )
                    ).strip()

                    if (
                        not task_id
                        or task_id.lower()
                        in [
                            "nan",
                            "none"
                        ]
                    ):

                        continue

                    texto_cluster = str(
                        row.get(
                            "CLUSTER",
                            ""
                        )
                    )

                    clusters_task = (
                        set()
                    )

                    for cluster in (
                        texto_cluster.split(
                            ","
                        )
                    ):

                        cluster = (
                            cluster.strip()
                        )

                        if (
                            cluster
                            and cluster.lower()
                            not in [
                                "nan",
                                "none",
                                "-"
                            ]
                        ):

                            clusters_task.add(
                                cluster
                            )

                    for cluster in (
                        clusters_task
                    ):

                        expedicoes_clusters.append(
                            {
                                "CLUSTER":
                                    cluster,

                                "TASK_ID":
                                    task_id,

                                "DRIVER_ID":
                                    row[
                                        "DRIVER_ID"
                                    ],

                                "PACOTES_CARREGADOS":
                                    row[
                                        "PACOTES_CARREGADOS"
                                    ],

                                "PACOTES_AREA_RISCO":
                                    row[
                                        "PACOTES_AREA_RISCO"
                                    ],
                            }
                        )

                df_expedicoes_cluster = (
                    pd.DataFrame(
                        expedicoes_clusters
                    )
                )

                # ==================================================
                # CLUSTER CRÍTICO
                # ==================================================

                cluster_critico = "-"
                qtd_cluster_critico = 0

                if not df_clusters.empty:

                    resumo_cluster_card = (
                        df_clusters
                        .groupby(
                            "CLUSTER"
                        )[
                            "DRIVER_ID"
                        ]
                        .nunique()
                        .sort_values(
                            ascending=False
                        )
                    )

                    if not resumo_cluster_card.empty:

                        cluster_critico = (
                            resumo_cluster_card
                            .index[0]
                        )

                        qtd_cluster_critico = (
                            int(
                                resumo_cluster_card
                                .iloc[0]
                            )
                        )

                # ==================================================
                # ÁREA DE RISCO
                #
                # AQUI CONTINUA MOSTRANDO OFENSORES EXPOSTOS
                # ==================================================

                if not df_novas_ofensas.empty:

                    motoristas_risco = (
                        df_novas_ofensas[
                            df_novas_ofensas[
                                "PACOTES_AREA_RISCO"
                            ]
                            > 0
                        ][
                            "DRIVER_ID"
                        ]
                        .nunique()
                    )

                else:

                    motoristas_risco = 0

                percentual_risco_driver = (
                    motoristas_risco
                    / ofensores_unicos
                    * 100
                    if ofensores_unicos > 0
                    else 0
                )

                # ==================================================
                # PERFIL DAS OFENSAS
                # ==================================================

                st.subheader(
                    "Perfil das ofensas"
                )

                c1, c2, c3, c4 = (
                    st.columns(4)
                )

                c1.metric(
                    "Turno com mais ofensores",
                    turno_critico,
                    delta=(
                        f"{qtd_turno_critico} drivers"
                    ),
                    delta_color="off"
                )

                c2.metric(
                    "Cluster com mais ofensores",
                    cluster_critico,
                    delta=(
                        f"{qtd_cluster_critico} drivers"
                    ),
                    delta_color="off"
                )

                c3.metric(
                    "Ofensores com área de risco",
                    motoristas_risco,
                    delta=(
                        f"{percentual_risco_driver:.1f}%"
                    ),
                    delta_color="off"
                )

                c4.metric(
                    "Faixa de horário crítica",
                    faixa_critica,
                    delta=(
                        f"{qtd_faixa_critica} drivers"
                    ),
                    delta_color="off"
                )

                st.divider()

                # ==================================================
                # RESUMO POR TURNO
                # ==================================================

                st.subheader(
                    "Resumo por turno"
                )

                if df_horarios.empty:

                    st.info(
                        "Sem horários de carregamento "
                        "no período."
                    )

                else:

                    resumo_turno = (
                        df_horarios[
                            df_horarios[
                                "TURNO"
                            ]
                            != "Fora da janela"
                        ]
                        .groupby(
                            "TURNO"
                        )
                        .agg(
                            REGISTROS_OFENSORES=(
                                "DRIVER_ID",
                                "size"
                            ),

                            OFENSORES=(
                                "DRIVER_ID",
                                "nunique"
                            ),
                        )
                        .reset_index()
                        .sort_values(
                            "OFENSORES",
                            ascending=False
                        )
                    )

                    st.dataframe(
                        resumo_turno,
                        column_config={

                            "TURNO":
                                "Turno",

                            "REGISTROS_OFENSORES":
                                "Registros ofensores",

                            "OFENSORES":
                                "Ofensores únicos",
                        },
                        use_container_width=True,
                        hide_index=True
                    )

                st.divider()

                # ==================================================
                # CLUSTER + HORÁRIO
                # ==================================================

                col1, col2 = (
                    st.columns(2)
                )

                # ==================================================
                # CLUSTERS
                # ==================================================

                with col1:

                    st.subheader(
                        "Clusters com mais ofensores"
                    )

                    if df_clusters.empty:

                        st.info(
                            "Sem informação de cluster."
                        )

                    else:

                        # ==========================================
                        # OFENSORES / REGISTROS
                        # ==========================================

                        tabela_clusters = (
                            df_clusters
                            .groupby(
                                "CLUSTER"
                            )
                            .agg(
                                OFENSORES=(
                                    "DRIVER_ID",
                                    "nunique"
                                ),
                            )
                            .reset_index()
                        )

                        # ==========================================
                        # EXPEDIÇÕES REAIS
                        # ==========================================

                        if not df_expedicoes_cluster.empty:

                            resumo_expedicoes = (
                                df_expedicoes_cluster
                                .groupby(
                                    "CLUSTER"
                                )
                                .agg(
                                    EXPEDICOES=(
                                        "TASK_ID",
                                        "nunique"
                                    ),

                                    PACOTES_EXPEDIDOS=(
                                        "PACOTES_CARREGADOS",
                                        "sum"
                                    ),

                                    PACOTES_AREA_RISCO=(
                                        "PACOTES_AREA_RISCO",
                                        "sum"
                                    ),
                                )
                                .reset_index()
                            )

                            tabela_clusters = (
                                tabela_clusters.merge(
                                    resumo_expedicoes,
                                    on="CLUSTER",
                                    how="left"
                                )
                            )

                        else:

                            tabela_clusters[
                                "EXPEDICOES"
                            ] = 0

                            tabela_clusters[
                                "PACOTES_EXPEDIDOS"
                            ] = 0

                            tabela_clusters[
                                "PACOTES_AREA_RISCO"
                            ] = 0

                        # ==========================================
                        # TRATAR NULOS
                        # ==========================================

                        for coluna in [
                            "EXPEDICOES",
                            "PACOTES_EXPEDIDOS",
                            "PACOTES_AREA_RISCO",
                        ]:

                            tabela_clusters[
                                coluna
                            ] = (
                                pd.to_numeric(
                                    tabela_clusters[
                                        coluna
                                    ],
                                    errors="coerce"
                                )
                                .fillna(0)
                            )

                        tabela_clusters[
                            "EXPEDICOES"
                        ] = (
                            tabela_clusters[
                                "EXPEDICOES"
                            ]
                            .astype(int)
                        )

                        # ==========================================
                        # % ÁREA DE RISCO
                        #
                        # Agora calculado sobre TODA A EXPEDIÇÃO
                        # daquele cluster, não somente ofensores.
                        # ==========================================

                        tabela_clusters[
                            "PERCENTUAL_RISCO"
                        ] = 0.0

                        possui_pacotes = (
                            tabela_clusters[
                                "PACOTES_EXPEDIDOS"
                            ]
                            > 0
                        )

                        tabela_clusters.loc[
                            possui_pacotes,
                            "PERCENTUAL_RISCO"
                        ] = (
                            tabela_clusters.loc[
                                possui_pacotes,
                                "PACOTES_AREA_RISCO"
                            ]
                            /
                            tabela_clusters.loc[
                                possui_pacotes,
                                "PACOTES_EXPEDIDOS"
                            ]
                            * 100
                        )

                        # ==========================================
                        # INCIDÊNCIA DE OFENSA
                        #
                        # Quantos registros ofensores existem em
                        # relação às expedições daquele cluster.
                        # ==========================================

                        tabela_clusters[
                            "TAXA_OFENSA"
                        ] = 0.0

                        possui_expedicao = (
                            tabela_clusters[
                                "EXPEDICOES"
                            ]
                            > 0
                        )

                        tabela_clusters.loc[
                            possui_expedicao,
                            "TAXA_OFENSA"
                        ] = (
                            tabela_clusters.loc[
                                possui_expedicao,
                                "OFENSORES"
                            ]
                            /
                            tabela_clusters.loc[
                                possui_expedicao,
                                "EXPEDICOES"
                            ]
                            * 100
                        )

                        # ==========================================
                        # ORDENAÇÃO
                        # ==========================================

                        tabela_clusters = (
                            tabela_clusters
                            .sort_values(
                                [
                                    "OFENSORES",
                                    "OFENSORES",
                                    "EXPEDICOES"
                                ],
                                ascending=[
                                    False,
                                    False,
                                    False
                                ]
                            )
                            .head(15)
                        )

                        # ==========================================
                        # TABELA
                        # ==========================================

                        st.dataframe(
                            tabela_clusters,
                            column_order=[
                                "CLUSTER",
                                "OFENSORES",
                                "EXPEDICOES",
                                "TAXA_OFENSA",
                                "PERCENTUAL_RISCO",
                            ],
                            column_config={

                                "CLUSTER":
                                    "Cluster",

                                "OFENSORES":
                                    "Ofensores",

                                "EXPEDICOES":
                                    "Expedições",

                                "TAXA_OFENSA":
                                    st.column_config.NumberColumn(
                                        "% Expedições com ofensa",
                                        format="%.1f%%"
                                    ),

                                "PERCENTUAL_RISCO":
                                    st.column_config.NumberColumn(
                                        "% Área de risco",
                                        format="%.1f%%"
                                    ),
                            },
                            use_container_width=True,
                            hide_index=True
                        )

                # ==================================================
                # FAIXA DE CARREGAMENTO
                # ==================================================

                with col2:

                    st.subheader(
                        "Faixa de carregamento"
                    )

                    if df_horarios.empty:

                        st.info(
                            "Sem informação de horário."
                        )

                    else:

                        ordem_faixas = [
                            "03:00 - 05:59",
                            "06:00 - 08:59",
                            "09:00 - 10:59",
                            "11:00 - 13:59",
                            "14:00 - 16:59",
                            "17:00 - 19:59",
                            "20:00 - 21:59",
                        ]

                        tabela_faixa = (
                            df_horarios[
                                df_horarios[
                                    "FAIXA"
                                ]
                                != "Fora da janela"
                            ]
                            .groupby(
                                "FAIXA"
                            )
                            .agg(
                                OFENSORES=(
                                    "DRIVER_ID",
                                    "nunique"
                                ),

                                REGISTROS_OFENSORES=(
                                    "DRIVER_ID",
                                    "size"
                                ),
                            )
                            .reset_index()
                        )

                        tabela_faixa[
                            "FAIXA"
                        ] = pd.Categorical(
                            tabela_faixa[
                                "FAIXA"
                            ],
                            categories=(
                                ordem_faixas
                            ),
                            ordered=True
                        )

                        tabela_faixa = (
                            tabela_faixa
                            .sort_values(
                                "FAIXA"
                            )
                        )

                        st.dataframe(
                            tabela_faixa,
                            column_config={

                                "FAIXA":
                                    "Faixa",

                                "OFENSORES":
                                    "Ofensores",

                                "REGISTROS_OFENSORES":
                                    "Registros ofensores",
                            },
                            use_container_width=True,
                            hide_index=True
                        )

                # ==================================================
                # PERSISTÊNCIA
                # ==================================================

                st.divider()

                st.subheader(
                    "Pacotes que permanecem em aberto"
                )

                st.caption(
                    "Persistência é analisada separadamente "
                    "da reincidência. Pacotes antigos que "
                    "continuam em aberto não geram uma nova "
                    "reincidência."
                )

                c1, c2, c3 = (
                    st.columns(3)
                )

                c1.metric(
                    "Motoristas com persistência",
                    motoristas_persistentes
                )

                c2.metric(
                    "Pacotes persistentes",
                    pacotes_persistentes
                )

                c3.metric(
                    "Maior persistência",
                    (
                        f"{maior_persistencia} dias"
                        if maior_persistencia > 0
                        else "-"
                    )
                )

                if df_persistencias.empty:

                    st.success(
                        "Nenhum pacote persistente "
                        "no período selecionado."
                    )

                else:

                    persistencia_motorista = (
                        df_persistencias
                        .groupby(
                            [
                                "DRIVER_ID",
                                "DRIVER_NAME"
                            ],
                            as_index=False
                        )
                        .agg(
                            PACOTES_PERSISTENTES=(
                                "PERMANECEM_ABERTOS",
                                "max"
                            ),

                            MAIOR_PERSISTENCIA=(
                                "DIAS_PERSISTENCIA",
                                "max"
                            ),

                            DESDE=(
                                "DESDE_DT",
                                "min"
                            ),
                        )
                        .sort_values(
                            [
                                "MAIOR_PERSISTENCIA",
                                "PACOTES_PERSISTENTES"
                            ],
                            ascending=False
                        )
                    )

                    persistencia_motorista[
                        "DESDE"
                    ] = (
                        persistencia_motorista[
                            "DESDE"
                        ]
                        .dt.strftime(
                            "%d/%m/%Y"
                        )
                    )

                    st.dataframe(
                        persistencia_motorista,
                        column_order=[
                            "DRIVER_ID",
                            "DRIVER_NAME",
                            "PACOTES_PERSISTENTES",
                            "MAIOR_PERSISTENCIA",
                            "DESDE",
                        ],
                        column_config={

                            "DRIVER_ID":
                                "ID",

                            "DRIVER_NAME":
                                "Motorista",

                            "PACOTES_PERSISTENTES":
                                "Pacotes em aberto",

                            "MAIOR_PERSISTENCIA":
                                "Dias em aberto",

                            "DESDE":
                                "Desde",
                        },
                        use_container_width=True,
                        hide_index=True
                    )

                # ==================================================
                # RANKING DE REINCIDÊNCIA
                # ==================================================

                st.divider()

                st.subheader(
                    "Ranking de reincidência"
                )

                st.caption(
                    "Conta somente novas operações em que "
                    "o motorista carregou e voltou a atingir "
                    "critério de ofensa."
                )

                if df_novas_ofensas.empty:

                    st.info(
                        "Nenhuma nova ofensa "
                        "no período selecionado."
                    )

                else:

                    ranking = (
                        df_novas_ofensas
                        .groupby(
                            [
                                "DRIVER_ID",
                                "DRIVER_NAME"
                            ],
                            as_index=False
                        )
                        .agg(
                            OPERACOES_OFENSORAS=(
                                "DATA_DT",
                                "nunique"
                            ),

                            PACOTES_CARREGADOS=(
                                "PACOTES_CARREGADOS",
                                "sum"
                            ),

                            OCORRENCIAS=(
                                "ONHOLD",
                                "sum"
                            ),

                            ABERTOS_D1=(
                                "ABERTOS_D1",
                                "sum"
                            ),

                            PACOTES_AREA_RISCO=(
                                "PACOTES_AREA_RISCO",
                                "sum"
                            ),
                        )
                    )

                    # ==============================================
                    # REINCIDÊNCIAS
                    # ==============================================

                    ranking[
                        "REINCIDENCIAS"
                    ] = (
                        ranking[
                            "OPERACOES_OFENSORAS"
                        ]
                        - 1
                    ).clip(
                        lower=0
                    )

                    # ==============================================
                    # D0
                    # ==============================================

                    ranking[
                        "D0"
                    ] = 0.0

                    possui_carga = (
                        ranking[
                            "PACOTES_CARREGADOS"
                        ]
                        > 0
                    )

                    ranking.loc[
                        possui_carga,
                        "D0"
                    ] = (
                        (
                            ranking.loc[
                                possui_carga,
                                "PACOTES_CARREGADOS"
                            ]
                            -
                            ranking.loc[
                                possui_carga,
                                "OCORRENCIAS"
                            ]
                            -
                            ranking.loc[
                                possui_carga,
                                "ABERTOS_D1"
                            ]
                        )
                        /
                        ranking.loc[
                            possui_carga,
                            "PACOTES_CARREGADOS"
                        ]
                        * 100
                    )

                    ranking[
                        "D0"
                    ] = (
                        ranking[
                            "D0"
                        ]
                        .clip(
                            lower=0,
                            upper=100
                        )
                        .round(2)
                    )

                    # ==============================================
                    # ÁREA DE RISCO
                    # ==============================================

                    ranking[
                        "PERCENTUAL_RISCO"
                    ] = 0.0

                    ranking.loc[
                        possui_carga,
                        "PERCENTUAL_RISCO"
                    ] = (
                        ranking.loc[
                            possui_carga,
                            "PACOTES_AREA_RISCO"
                        ]
                        /
                        ranking.loc[
                            possui_carga,
                            "PACOTES_CARREGADOS"
                        ]
                        * 100
                    )

                    # ==============================================
                    # ORDENAR
                    # ==============================================

                    ranking = (
                        ranking
                        .sort_values(
                            [
                                "OPERACOES_OFENSORAS",
                                "OCORRENCIAS",
                                "ABERTOS_D1"
                            ],
                            ascending=False
                        )
                    )

                    # ==============================================
                    # TABELA
                    # ==============================================

                    st.dataframe(
                        ranking,
                        column_order=[
                            "DRIVER_ID",
                            "DRIVER_NAME",
                            "OPERACOES_OFENSORAS",
                            "REINCIDENCIAS",
                            "PACOTES_CARREGADOS",
                            "OCORRENCIAS",
                            "ABERTOS_D1",
                            "D0",
                            "PERCENTUAL_RISCO",
                        ],
                        column_config={

                            "DRIVER_ID":
                                "ID",

                            "DRIVER_NAME":
                                "Motorista",

                            "OPERACOES_OFENSORAS":
                                "Dias com ofensa",

                            "REINCIDENCIAS":
                                "Reincidências",

                            "PACOTES_CARREGADOS":
                                "Pacotes",

                            "OCORRENCIAS":
                                "Ocorrências",

                            "ABERTOS_D1":
                                "Em aberto D-1",

                            "D0":
                                st.column_config.ProgressColumn(
                                    "D0",
                                    min_value=0,
                                    max_value=100,
                                    format="%.2f%%"
                                ),

                            "PERCENTUAL_RISCO":
                                st.column_config.NumberColumn(
                                    "% Área de risco",
                                    format="%.1f%%"
                                ),
                        },
                        use_container_width=True,
                        hide_index=True,
                        height=500
                    )

                # ==================================================
                # DETALHAMENTO
                # ==================================================

                st.divider()

                with st.expander(
                    "Ver todos os registros do período"
                ):

                    detalhe = (
                        df_periodo
                        .sort_values(
                            "DATA_DT",
                            ascending=False
                        )
                        .copy()
                    )

                    st.dataframe(
                        detalhe,
                        column_order=[
                            "DATA",
                            "DRIVER_ID",
                            "DRIVER_NAME",
                            "TIPO_REGISTRO",
                            "PACOTES_CARREGADOS",
                            "ONHOLD",
                            "RESUMO_EXIBICAO",
                            "ABERTOS_D1",
                            "PERMANECEM_ABERTOS",
                            "DIAS_PERSISTENCIA",
                            "REALIZACAO_ROTA",
                            "CLUSTER",
                            "HORA_CARREGAMENTO",
                            "PACOTES_AREA_RISCO",
                            "PERCENTUAL_AREA_RISCO",
                        ],
                        column_config={

                            "DATA":
                                "Data",

                            "DRIVER_ID":
                                "ID",

                            "DRIVER_NAME":
                                "Motorista",

                            "TIPO_REGISTRO":
                                "Tipo",

                            "PACOTES_CARREGADOS":
                                "Carga",

                            "ONHOLD":
                                "Ocorrências",

                            "RESUMO_EXIBICAO":
                                st.column_config.TextColumn(
                                    "Resumo das ocorrências",
                                    width="large"
                                ),

                            "ABERTOS_D1":
                                "Em aberto D-1",

                            "PERMANECEM_ABERTOS":
                                "Persistentes",

                            "DIAS_PERSISTENCIA":
                                "Dias em aberto",

                            "REALIZACAO_ROTA":
                                st.column_config.ProgressColumn(
                                    "D0",
                                    min_value=0,
                                    max_value=100,
                                    format="%.2f%%"
                                ),

                            "CLUSTER":
                                "Cluster",

                            "HORA_CARREGAMENTO":
                                "Carregou",

                            "PACOTES_AREA_RISCO":
                                "Área de risco",

                            "PERCENTUAL_AREA_RISCO":
                                st.column_config.NumberColumn(
                                    "% Risco",
                                    format="%.1f%%"
                                ),
                        },
                        use_container_width=True,
                        hide_index=True,
                        height=520
                    )

    except Exception as e:

        st.error(
            "Erro ao carregar o histórico."
        )

        st.exception(e)
# ==========================================================
# TRATATIVAS
# ==========================================================

elif pagina == "Tratativas":

    st.title("Tratativas")

    st.caption(
        "Acompanhamento e registro das ações realizadas "
        "com motoristas ofensores."
    )

    st.divider()

    try:

        # ======================================================
        # CARREGAR BASES
        # ======================================================

        with st.spinner(
            "Carregando ofensores e tratativas..."
        ):

            df_ofensores_trat = carregar_dados_aba(
                "DADOS DE OFENSORES"
            )

            df_tratativas = carregar_tratativas()

        # ======================================================
        # VERIFICA HISTÓRICO
        # ======================================================

        if df_ofensores_trat.empty:

            st.info(
                "Ainda não existem ofensores registrados."
            )

        else:

            df_ofensores_trat = (
                df_ofensores_trat.copy()
            )

            df_tratativas = (
                df_tratativas.copy()
            )

            # ==================================================
            # GARANTIR COLUNAS DOS OFENSORES
            # ==================================================

            colunas_ofensores = {

                "DATA": "",

                "DRIVER_ID": "",

                "DRIVER_NAME": "",

                "CARREGAMENTOS": 0,

                "PACOTES_CARREGADOS": 0,

                "ONHOLD": 0,

                "ABERTOS_D1": 0,

                "PERMANECEM_ABERTOS": 0,

                "RESUMO_OCORRENCIAS": "",

                "CLUSTER": "",

                "REALIZACAO_ROTA": 0,

                "OFENSOR_OCORRENCIA": "",

                "OFENSOR_ABERTO_D1": "",

                "OFENSOR_ABERTO_ANTIGO": "",
            }

            for (
                coluna,
                valor_padrao
            ) in colunas_ofensores.items():

                if (
                    coluna
                    not in df_ofensores_trat.columns
                ):

                    df_ofensores_trat[
                        coluna
                    ] = valor_padrao

            # ==================================================
            # NORMALIZAR IDS
            # ==================================================

            df_ofensores_trat[
                "DRIVER_ID"
            ] = (
                df_ofensores_trat[
                    "DRIVER_ID"
                ]
                .astype(str)
                .str.replace(
                    r"\.0$",
                    "",
                    regex=True
                )
                .str.strip()
            )

            df_ofensores_trat[
                "DRIVER_NAME"
            ] = (
                df_ofensores_trat[
                    "DRIVER_NAME"
                ]
                .fillna("")
                .astype(str)
                .str.strip()
            )

            # ==================================================
            # DATAS
            # ==================================================

            df_ofensores_trat[
                "DATA_DT"
            ] = pd.to_datetime(
                df_ofensores_trat[
                    "DATA"
                ],
                errors="coerce",
                dayfirst=True
            )

            df_ofensores_trat = (
                df_ofensores_trat[
                    df_ofensores_trat[
                        "DATA_DT"
                    ].notna()
                ]
                .copy()
            )

            # ==================================================
            # NUMÉRICOS
            # ==================================================

            for coluna in [

                "CARREGAMENTOS",

                "PACOTES_CARREGADOS",

                "ONHOLD",

                "ABERTOS_D1",

                "PERMANECEM_ABERTOS",

                "REALIZACAO_ROTA",

            ]:

                df_ofensores_trat[
                    coluna
                ] = (
                    pd.to_numeric(
                        df_ofensores_trat[
                            coluna
                        ],
                        errors="coerce"
                    )
                    .fillna(0)
                )

            # ==================================================
            # FUNÇÃO SIM/NÃO
            # ==================================================

            def valor_booleano(
                valor
            ):

                return (
                    str(valor)
                    .strip()
                    .upper()
                    in [
                        "SIM",
                        "TRUE",
                        "1",
                    ]
                )

            # ==================================================
            # IDENTIFICAR NOVA OFENSA
            #
            # Persistência antiga sozinha NÃO gera
            # nova tratativa.
            # ==================================================

            df_ofensores_trat[
                "NOVA_OFENSA"
            ] = (
                (
                    df_ofensores_trat[
                        "ONHOLD"
                    ]
                    > 5
                )
                |
                (
                    df_ofensores_trat[
                        "ABERTOS_D1"
                    ]
                    > 10
                )
            )

            # ==================================================
            # SOMENTE NOVAS OFENSAS
            # ==================================================

            df_novas_ofensas_trat = (
                df_ofensores_trat[
                    df_ofensores_trat[
                        "NOVA_OFENSA"
                    ]
                ]
                .copy()
            )

            # ==================================================
            # NORMALIZAR TRATATIVAS
            # ==================================================

            if not df_tratativas.empty:

                df_tratativas[
                    "DRIVER_ID"
                ] = (
                    df_tratativas[
                        "DRIVER_ID"
                    ]
                    .astype(str)
                    .str.replace(
                        r"\.0$",
                        "",
                        regex=True
                    )
                    .str.strip()
                )

                df_tratativas[
                    "DATA_OFENSA_DT"
                ] = pd.to_datetime(
                    df_tratativas[
                        "DATA_OFENSA"
                    ],
                    errors="coerce",
                    dayfirst=True
                )

                df_tratativas[
                    "STATUS_NORMALIZADO"
                ] = (
                    df_tratativas[
                        "STATUS_TRATATIVA"
                    ]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                    .str.lower()
                )

            # ==================================================
            # IDENTIFICAR SE CADA OFENSA POSSUI TRATATIVA
            # ==================================================

            def buscar_status_tratativa(
                row
            ):

                if df_tratativas.empty:

                    return pd.Series(
                        {
                            "TRATATIVA_ID_ATUAL": "",
                            "STATUS_TRATATIVA_ATUAL": "Pendente",
                            "TIPO_TRATATIVA_ATUAL": "",
                            "RESPONSAVEL_ATUAL": "",
                        }
                    )

                driver_id = str(
                    row[
                        "DRIVER_ID"
                    ]
                ).strip()

                data_ofensa = (
                    row[
                        "DATA_DT"
                    ].date()
                )

                encontrados = (
                    df_tratativas[
                        (
                            df_tratativas[
                                "DRIVER_ID"
                            ]
                            == driver_id
                        )
                        &
                        (
                            df_tratativas[
                                "DATA_OFENSA_DT"
                            ].dt.date
                            == data_ofensa
                        )
                    ]
                )

                if encontrados.empty:

                    return pd.Series(
                        {
                            "TRATATIVA_ID_ATUAL": "",
                            "STATUS_TRATATIVA_ATUAL": "Pendente",
                            "TIPO_TRATATIVA_ATUAL": "",
                            "RESPONSAVEL_ATUAL": "",
                        }
                    )

                ultima = (
                    encontrados.iloc[-1]
                )

                status = str(
                    ultima.get(
                        "STATUS_TRATATIVA",
                        "Pendente"
                    )
                ).strip()

                if not status:

                    status = "Pendente"

                return pd.Series(
                    {
                        "TRATATIVA_ID_ATUAL":
                            str(
                                ultima.get(
                                    "TRATATIVA_ID",
                                    ""
                                )
                            ),

                        "STATUS_TRATATIVA_ATUAL":
                            status,

                        "TIPO_TRATATIVA_ATUAL":
                            str(
                                ultima.get(
                                    "TIPO_TRATATIVA",
                                    ""
                                )
                            ),

                        "RESPONSAVEL_ATUAL":
                            str(
                                ultima.get(
                                    "RESPONSAVEL",
                                    ""
                                )
                            ),
                    }
                )

            if not df_novas_ofensas_trat.empty:

                dados_status = (
                    df_novas_ofensas_trat
                    .apply(
                        buscar_status_tratativa,
                        axis=1
                    )
                )

                df_novas_ofensas_trat = (
                    pd.concat(
                        [
                            df_novas_ofensas_trat,
                            dados_status
                        ],
                        axis=1
                    )
                )

            else:

                df_novas_ofensas_trat[
                    "TRATATIVA_ID_ATUAL"
                ] = ""

                df_novas_ofensas_trat[
                    "STATUS_TRATATIVA_ATUAL"
                ] = ""

                df_novas_ofensas_trat[
                    "TIPO_TRATATIVA_ATUAL"
                ] = ""

                df_novas_ofensas_trat[
                    "RESPONSAVEL_ATUAL"
                ] = ""

            # ==================================================
            # REINCIDÊNCIA APÓS TRATATIVA
            # ==================================================

            def verificar_reincidencia(row):

                resultado = (
                    analisar_reincidencia_pos_tratativa(
                        driver_id=row["DRIVER_ID"],
                        data_ofensa=row["DATA_DT"],
                        df_historico_ofensores=df_ofensores_trat,

                        # IMPORTANTE:
                        # passa o DataFrame que já foi carregado
                        # para não consultar o Google Sheets de novo
                        df_tratativas=df_tratativas,
                    )
                )

                return pd.Series(
                    {
                        "JA_TRATADO":
                            resultado["ja_tratado"],

                        "REINCIDENTE_POS_TRATATIVA":
                            resultado[
                                "reincidente_pos_tratativa"
                            ],

                        "ULTIMA_TRATATIVA":
                            resultado["ultima_tratativa"],

                        "DATA_ULTIMA_TRATATIVA":
                            resultado[
                                "data_ultima_tratativa"
                            ],

                        "OFENSAS_APOS_TRATATIVA":
                            resultado[
                                "ofensas_apos_tratativa"
                            ],
                    }
                )


            if not df_novas_ofensas_trat.empty:
                dados_reincidencia = (
                    df_novas_ofensas_trat
                    .apply(
                        verificar_reincidencia,
                        axis=1
                    )
                )

                df_novas_ofensas_trat = (
                    pd.concat(
                        [
                            df_novas_ofensas_trat,
                            dados_reincidencia
                        ],
                        axis=1
                    )
                )

            # ==================================================
            # SITUAÇÃO
            # ==================================================

            def classificar_situacao(
                row
            ):

                status = str(
                    row.get(
                        "STATUS_TRATATIVA_ATUAL",
                        ""
                    )
                ).strip().lower()

                reincidente = bool(
                    row.get(
                        "REINCIDENTE_POS_TRATATIVA",
                        False
                    )
                )

                ja_tratado = bool(
                    row.get(
                        "JA_TRATADO",
                        False
                    )
                )

                # ----------------------------------------------
                # PRIORIDADE MÁXIMA
                # ----------------------------------------------

                if reincidente:

                    return (
                        "🔴 Reincidente após tratativa"
                    )

                # ----------------------------------------------
                # TRATATIVA EM ANDAMENTO
                # ----------------------------------------------

                if (
                    status
                    == "em acompanhamento"
                ):

                    return (
                        "🟠 Em acompanhamento"
                    )

                # ----------------------------------------------
                # JÁ CONCLUÍDA PARA ESTA OFENSA
                # ----------------------------------------------

                if (
                    status
                    in [
                        "concluída",
                        "concluida"
                    ]
                ):

                    return (
                        "🟢 Tratativa concluída"
                    )

                # ----------------------------------------------
                # JÁ FOI TRATADO ANTES
                # ----------------------------------------------

                if ja_tratado:

                    return (
                        "🟡 Já tratado anteriormente"
                    )

                # ----------------------------------------------
                # PRIMEIRA TRATATIVA
                # ----------------------------------------------

                return (
                    "⚪ Primeira tratativa"
                )

            if not df_novas_ofensas_trat.empty:

                df_novas_ofensas_trat[
                    "SITUACAO"
                ] = (
                    df_novas_ofensas_trat
                    .apply(
                        classificar_situacao,
                        axis=1
                    )
                )

            # ==================================================
            # CARDS
            # ==================================================

            total_pendentes = int(
                (
                    df_novas_ofensas_trat[
                        "STATUS_TRATATIVA_ATUAL"
                    ]
                    .fillna("")
                    .str.lower()
                    .isin(
                        [
                            "",
                            "pendente"
                        ]
                    )
                ).sum()
            )

            em_acompanhamento = int(
                (
                    df_novas_ofensas_trat[
                        "STATUS_TRATATIVA_ATUAL"
                    ]
                    .fillna("")
                    .str.lower()
                    == "em acompanhamento"
                ).sum()
            )

            concluidas = int(
                (
                    df_novas_ofensas_trat[
                        "STATUS_TRATATIVA_ATUAL"
                    ]
                    .fillna("")
                    .str.lower()
                    .isin(
                        [
                            "concluída",
                            "concluida"
                        ]
                    )
                ).sum()
            )

            reincidentes_pos = int(
                df_novas_ofensas_trat[
                    "REINCIDENTE_POS_TRATATIVA"
                ]
                .fillna(False)
                .sum()
            )

            c1, c2, c3, c4 = (
                st.columns(4)
            )

            c1.metric(
                "Pendentes",
                total_pendentes
            )

            c2.metric(
                "Em acompanhamento",
                em_acompanhamento
            )

            c3.metric(
                "Concluídas",
                concluidas
            )

            c4.metric(
                "Reincidentes após tratativa",
                reincidentes_pos
            )

            st.divider()

            # ==================================================
            # FILTROS
            # ==================================================

            st.subheader(
                "Ofensores"
            )

            col_busca, col_status = (
                st.columns(
                    [2, 1]
                )
            )

            with col_busca:

                busca_tratativa = (
                    st.text_input(
                        "Buscar motorista",
                        placeholder=(
                            "Digite o ID ou nome"
                        ),
                        key=(
                            "busca_motorista_tratativa"
                        )
                    )
                )

            with col_status:

                filtro_status_trat = (
                    st.multiselect(
                        "Status",
                        options=[
                            "Pendente",
                            "Em acompanhamento",
                            "Concluída",
                        ],
                        placeholder=(
                            "Todos"
                        ),
                        key=(
                            "status_tratativa_filtro"
                        )
                    )
                )

            df_lista = (
                df_novas_ofensas_trat
                .copy()
            )

            # ==================================================
            # BUSCA
            # ==================================================

            if busca_tratativa:

                busca = (
                    busca_tratativa
                    .strip()
                    .lower()
                )

                df_lista = (
                    df_lista[
                        (
                            df_lista[
                                "DRIVER_ID"
                            ]
                            .str.lower()
                            .str.contains(
                                busca,
                                na=False,
                                regex=False
                            )
                        )
                        |
                        (
                            df_lista[
                                "DRIVER_NAME"
                            ]
                            .str.lower()
                            .str.contains(
                                busca,
                                na=False,
                                regex=False
                            )
                        )
                    ]
                    .copy()
                )

            # ==================================================
            # STATUS
            # ==================================================

            if filtro_status_trat:

                df_lista = (
                    df_lista[
                        df_lista[
                            "STATUS_TRATATIVA_ATUAL"
                        ]
                        .isin(
                            filtro_status_trat
                        )
                    ]
                    .copy()
                )

            # ==================================================
            # PRIORIDADE
            # ==================================================

            def prioridade_tratativa(
                row
            ):

                if bool(
                    row.get(
                        "REINCIDENTE_POS_TRATATIVA",
                        False
                    )
                ):

                    return 1

                if bool(
                    row.get(
                        "JA_TRATADO",
                        False
                    )
                ):

                    return 2

                return 3

            df_lista[
                "PRIORIDADE"
            ] = (
                df_lista.apply(
                    prioridade_tratativa,
                    axis=1
                )
            )

            df_lista = (
                df_lista
                .sort_values(
                    [
                        "PRIORIDADE",
                        "DATA_DT"
                    ],
                    ascending=[
                        True,
                        False
                    ]
                )
            )

            # ==================================================
            # TABELA RESUMIDA
            # ==================================================

            if df_lista.empty:

                st.success(
                    "Nenhum motorista encontrado "
                    "com os filtros selecionados."
                )

            else:

                tabela_tratativas = (
                    df_lista[
                        [
                            "DATA",
                            "DRIVER_ID",
                            "DRIVER_NAME",
                            "SITUACAO",
                            "ONHOLD",
                            "ABERTOS_D1",
                            "CLUSTER",
                            "REALIZACAO_ROTA",
                        ]
                    ]
                    .copy()
                )

                st.dataframe(
                    tabela_tratativas,
                    column_config={

                        "DATA":
                            "Data",

                        "DRIVER_ID":
                            "ID",

                        "DRIVER_NAME":
                            "Motorista",

                        "SITUACAO":
                            "Situação",

                        "ONHOLD":
                            "Ocorrências",

                        "ABERTOS_D1":
                            "Em aberto",

                        "CLUSTER":
                            "Cluster",

                        "REALIZACAO_ROTA":
                            st.column_config.ProgressColumn(
                                "D0",
                                min_value=0,
                                max_value=100,
                                format="%.2f%%"
                            ),
                    },
                    use_container_width=True,
                    hide_index=True
                )

                st.divider()

                # ==================================================
                # SELECIONAR MOTORISTA PARA TRATAR
                # ==================================================

                st.subheader(
                    "Registrar tratativa"
                )

                opcoes = {}

                for indice, row in (
                    df_lista.iterrows()
                ):

                    data_texto = (
                        row[
                            "DATA_DT"
                        ]
                        .strftime(
                            "%d/%m/%Y"
                        )
                    )

                    label = (
                        f"{row['DRIVER_ID']} | "
                        f"{row['DRIVER_NAME']} | "
                        f"{data_texto}"
                    )

                    opcoes[
                        label
                    ] = indice

                motorista_selecionado = (
                    st.selectbox(
                        "Selecione o motorista",
                        options=list(
                            opcoes.keys()
                        ),
                        key=(
                            "motorista_tratativa_select"
                        )
                    )
                )

                indice_selecionado = (
                    opcoes[
                        motorista_selecionado
                    ]
                )

                registro = (
                    df_lista.loc[
                        indice_selecionado
                    ]
                )

                # ==================================================
                # DETALHES
                # ==================================================

                st.markdown(
                    f"### {registro['DRIVER_NAME']}"
                )

                st.caption(
                    f"ID {registro['DRIVER_ID']} • "
                    f"{registro['DATA_DT'].strftime('%d/%m/%Y')}"
                )

                # ==================================================
                # ALERTA DE REINCIDÊNCIA
                # ==================================================

                if bool(
                    registro.get(
                        "REINCIDENTE_POS_TRATATIVA",
                        False
                    )
                ):

                    st.error(
                        "🔴 REINCIDENTE APÓS TRATATIVA"
                    )

                    ultima_tratativa = str(
                        registro.get(
                            "ULTIMA_TRATATIVA",
                            "-"
                        )
                    )

                    data_ultima = str(
                        registro.get(
                            "DATA_ULTIMA_TRATATIVA",
                            "-"
                        )
                    )

                    quantidade_apos = int(
                        registro.get(
                            "OFENSAS_APOS_TRATATIVA",
                            0
                        )
                    )

                    st.markdown(
                        f"""
**Última tratativa:** {ultima_tratativa}  
**Data:** {data_ultima}  
**Ofensas após a tratativa:** {quantidade_apos}
"""
                    )

                elif bool(
                    registro.get(
                        "JA_TRATADO",
                        False
                    )
                ):

                    st.warning(
                        "🟡 Este motorista já recebeu "
                        "tratativa anteriormente."
                    )

                else:

                    st.info(
                        "⚪ Esta é a primeira tratativa "
                        "registrada para este motorista."
                    )

                # ==================================================
                # OFENSA ATUAL
                # ==================================================

                st.markdown(
                    "#### Ofensa atual"
                )

                c1, c2, c3, c4 = (
                    st.columns(4)
                )

                c1.metric(
                    "Pacotes",
                    int(
                        registro[
                            "PACOTES_CARREGADOS"
                        ]
                    )
                )

                c2.metric(
                    "Ocorrências",
                    int(
                        registro[
                            "ONHOLD"
                        ]
                    )
                )

                c3.metric(
                    "Em aberto",
                    int(
                        registro[
                            "ABERTOS_D1"
                        ]
                    )
                )

                c4.metric(
                    "D0",
                    (
                        f"{float(registro['REALIZACAO_ROTA']):.2f}%"
                    )
                )

                resumo = str(
                    registro.get(
                        "RESUMO_OCORRENCIAS",
                        ""
                    )
                ).strip()

                if (
                    resumo
                    and resumo.lower()
                    not in [
                        "nan",
                        "none",
                        "-"
                    ]
                ):

                    st.markdown(
                        f"**Motivos:** {resumo}"
                    )

                if (
                    int(
                        registro[
                            "ABERTOS_D1"
                        ]
                    )
                    > 0
                ):

                    st.markdown(
                        f"**Em aberto:** "
                        f"{int(registro['ABERTOS_D1'])}"
                    )

                st.markdown(
                    f"**Cluster:** "
                    f"{registro['CLUSTER'] or '-'}"
                )

                st.divider()

                # ==================================================
                # FORMULÁRIO
                # ==================================================

                tratativa_id_atual = str(
                    registro.get(
                        "TRATATIVA_ID_ATUAL",
                        ""
                    )
                ).strip()

                # --------------------------------------------------
                # SE JÁ EXISTE, PEGA VALORES ATUAIS
                # --------------------------------------------------

                tipo_atual = str(
                    registro.get(
                        "TIPO_TRATATIVA_ATUAL",
                        ""
                    )
                ).strip()

                responsavel_atual = str(
                    registro.get(
                        "RESPONSAVEL_ATUAL",
                        ""
                    )
                ).strip()

                status_atual = str(
                    registro.get(
                        "STATUS_TRATATIVA_ATUAL",
                        "Pendente"
                    )
                ).strip()

                if not status_atual:

                    status_atual = (
                        "Pendente"
                    )

                tipos_tratativa = [
                    "Orientação",
                    "Advertência",
                    "Contato com motorista",
                    "Contato com agência/3PL",
                    "Análise operacional",
                    "Bloqueio",
                    "Outros",
                ]

                status_opcoes = [
                    "Pendente",
                    "Em acompanhamento",
                    "Concluída",
                ]

                indice_tipo = 0

                if (
                    tipo_atual
                    in tipos_tratativa
                ):

                    indice_tipo = (
                        tipos_tratativa.index(
                            tipo_atual
                        )
                    )

                indice_status = 0

                if (
                    status_atual
                    in status_opcoes
                ):

                    indice_status = (
                        status_opcoes.index(
                            status_atual
                        )
                    )

                # ==================================================
                # BUSCAR OBSERVAÇÃO EXISTENTE
                # ==================================================

                observacao_atual = ""

                if (
                    tratativa_id_atual
                    and
                    not df_tratativas.empty
                ):

                    trat_existente = (
                        df_tratativas[
                            df_tratativas[
                                "TRATATIVA_ID"
                            ]
                            == tratativa_id_atual
                        ]
                    )

                    if not trat_existente.empty:

                        observacao_atual = str(
                            trat_existente
                            .iloc[-1]
                            .get(
                                "OBSERVACAO",
                                ""
                            )
                        )

                # ==================================================
                # FORM
                # ==================================================

                with st.form(
                    "form_tratativa"
                ):

                    col1, col2 = (
                        st.columns(2)
                    )

                    with col1:

                        tipo_tratativa = (
                            st.selectbox(
                                "Tipo de tratativa",
                                options=(
                                    tipos_tratativa
                                ),
                                index=(
                                    indice_tipo
                                )
                            )
                        )

                    with col2:

                        status_tratativa = (
                            st.selectbox(
                                "Status",
                                options=(
                                    status_opcoes
                                ),
                                index=(
                                    indice_status
                                )
                            )
                        )

                    responsavel = (
                        st.text_input(
                            "Responsável",
                            value=(
                                responsavel_atual
                            ),
                            placeholder=(
                                "Nome do responsável pela tratativa"
                            )
                        )
                    )

                    observacao = (
                        st.text_area(
                            "Observação",
                            value=(
                                observacao_atual
                            ),
                            placeholder=(
                                "Descreva a orientação, "
                                "contato ou ação realizada..."
                            ),
                            height=130
                        )
                    )

                    salvar = (
                        st.form_submit_button(
                            "💾 Salvar tratativa",
                            use_container_width=True,
                            type="primary"
                        )
                    )

                # ==================================================
                # SALVAR
                # ==================================================

                if salvar:

                    if not responsavel.strip():

                        st.error(
                            "Informe o responsável "
                            "pela tratativa."
                        )

                    else:

                        # ==========================================
                        # TIPO DA OFENSA
                        # ==========================================

                        tipos_ofensa = []

                        if (
                            registro[
                                "ONHOLD"
                            ]
                            > 5
                        ):

                            tipos_ofensa.append(
                                "Ocorrência"
                            )

                        if (
                            registro[
                                "ABERTOS_D1"
                            ]
                            > 10
                        ):

                            tipos_ofensa.append(
                                "Em aberto"
                            )

                        tipo_ofensa = (
                            " + ".join(
                                tipos_ofensa
                            )
                        )

                        # ==========================================
                        # ATUALIZA
                        # ==========================================

                        if tratativa_id_atual:

                            resultado = (
                                atualizar_tratativa(
                                    tratativa_id=(
                                        tratativa_id_atual
                                    ),
                                    tipo_tratativa=(
                                        tipo_tratativa
                                    ),
                                    responsavel=(
                                        responsavel
                                    ),
                                    observacao=(
                                        observacao
                                    ),
                                    status_tratativa=(
                                        status_tratativa
                                    ),
                                )
                            )

                            st.success(
                                "Tratativa atualizada "
                                "com sucesso."
                            )

                        # ==========================================
                        # NOVA
                        # ==========================================

                        else:

                            resultado = (
                                salvar_tratativa(
                                    data_ofensa=(
                                        registro[
                                            "DATA_DT"
                                        ]
                                    ),
                                    driver_id=(
                                        registro[
                                            "DRIVER_ID"
                                        ]
                                    ),
                                    driver_name=(
                                        registro[
                                            "DRIVER_NAME"
                                        ]
                                    ),
                                    tipo_ofensa=(
                                        tipo_ofensa
                                    ),
                                    onhold=(
                                        int(
                                            registro[
                                                "ONHOLD"
                                            ]
                                        )
                                    ),
                                    abertos_d1=(
                                        int(
                                            registro[
                                                "ABERTOS_D1"
                                            ]
                                        )
                                    ),
                                    permanecem_abertos=(
                                        int(
                                            registro[
                                                "PERMANECEM_ABERTOS"
                                            ]
                                        )
                                    ),
                                    resumo_ocorrencias=(
                                        resumo
                                    ),
                                    cluster=(
                                        registro[
                                            "CLUSTER"
                                        ]
                                    ),
                                    d0=(
                                        float(
                                            registro[
                                                "REALIZACAO_ROTA"
                                            ]
                                        )
                                    ),
                                    tipo_tratativa=(
                                        tipo_tratativa
                                    ),
                                    responsavel=(
                                        responsavel
                                    ),
                                    observacao=(
                                        observacao
                                    ),
                                    status_tratativa=(
                                        status_tratativa
                                    ),
                                )
                            )

                            if (
                                resultado.get(
                                    "duplicado"
                                )
                            ):

                                st.warning(
                                    "Essa ofensa já possui "
                                    "uma tratativa registrada."
                                )

                            else:

                                st.success(
                                    "Tratativa registrada "
                                    "com sucesso."
                                )

                        # ==========================================
                        # ATUALIZA A TELA
                        # ==========================================

                        st.rerun()

            # ==================================================
            # HISTÓRICO DE TRATATIVAS
            # ==================================================

            st.divider()

            st.subheader(
                "Histórico de tratativas"
            )

            if df_tratativas.empty:

                st.info(
                    "Nenhuma tratativa registrada ainda."
                )

            else:

                historico_trat = (
                    df_tratativas.copy()
                )

                historico_trat[
                    "DATA_OFENSA_DT"
                ] = pd.to_datetime(
                    historico_trat[
                        "DATA_OFENSA"
                    ],
                    errors="coerce",
                    dayfirst=True
                )

                historico_trat[
                    "DATA_TRATATIVA_DT"
                ] = pd.to_datetime(
                    historico_trat[
                        "DATA_TRATATIVA"
                    ],
                    errors="coerce",
                    dayfirst=True
                )

                historico_trat = (
                    historico_trat
                    .sort_values(
                        [
                            "DATA_OFENSA_DT",
                            "DATA_TRATATIVA_DT"
                        ],
                        ascending=False
                    )
                )

                st.dataframe(
                    historico_trat,
                    column_order=[
                        "DATA_OFENSA",
                        "DRIVER_ID",
                        "DRIVER_NAME",
                        "TIPO_OFENSA",
                        "TIPO_TRATATIVA",
                        "RESPONSAVEL",
                        "STATUS_TRATATIVA",
                        "DATA_TRATATIVA",
                        "DATA_CONCLUSAO",
                        "OBSERVACAO",
                    ],
                    column_config={

                        "DATA_OFENSA":
                            "Data da ofensa",

                        "DRIVER_ID":
                            "ID",

                        "DRIVER_NAME":
                            "Motorista",

                        "TIPO_OFENSA":
                            "Ofensa",

                        "TIPO_TRATATIVA":
                            "Tratativa",

                        "RESPONSAVEL":
                            "Responsável",

                        "STATUS_TRATATIVA":
                            "Status",

                        "DATA_TRATATIVA":
                            "Tratado em",

                        "DATA_CONCLUSAO":
                            "Concluído em",

                        "OBSERVACAO":
                            st.column_config.TextColumn(
                                "Observação",
                                width="large"
                            ),
                    },
                    use_container_width=True,
                    hide_index=True,
                    height=450
                )

    except Exception as e:

        st.error(
            "Erro ao carregar a página de tratativas."
        )

        st.exception(e)