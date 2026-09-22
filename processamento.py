import pandas as pd
from datetime import datetime


COLUNAS_CARREGAMENTO = [
    "TASK_ID",
    "DRIVER_ID",
    "DRIVER_NAME",
    "DATA",
    "HORA_CARREGAMENTO",
    "TURNO_CARREGAMENTO",
    "SEMANA",
    "CLUSTER",
    "PACOTES_CARREGADOS",
    "PACOTES_AREA_RISCO",
    "PERCENTUAL_AREA_RISCO",
    "DATA_IMPORTACAO",
]


def identificar_turno_carregamento(create_time):

    if pd.isna(create_time):
        return ""

    try:
        hora = pd.to_datetime(create_time).hour
    except Exception:
        return ""

    if 3 <= hora <= 10:
        return "AM"

    elif 11 <= hora <= 21:
        return "SD"

    return ""


def processar_carregamento(
    df_raw: pd.DataFrame
) -> pd.DataFrame:

    df = df_raw.copy()

    # ======================================================
    # COLUNAS
    # ======================================================

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    obrigatorias = [
        "Task ID",
        "Driver ID",
        "Driver name",
        "Delivery Date",
        "Create Time",
        "SPX tracking num",
        "Cluster",
        "Risk Type",
    ]

    faltando = [
        coluna
        for coluna in obrigatorias
        if coluna not in df.columns
    ]

    if faltando:
        raise ValueError(
            "Colunas obrigatórias ausentes: "
            + ", ".join(faltando)
        )

    # ======================================================
    # DATAS
    # ======================================================

    df["DATA"] = pd.to_datetime(
        df["Delivery Date"],
        dayfirst=True,
        errors="coerce"
    )

    df["CREATE_TIME_DT"] = pd.to_datetime(
        df["Create Time"],
        dayfirst=True,
        errors="coerce"
    )

    # ======================================================
    # DRIVER ID
    # ======================================================

    df["Driver ID"] = (
        df["Driver ID"]
        .astype(str)
        .str.replace(
            r"\.0$",
            "",
            regex=True
        )
        .str.strip()
    )

    # ======================================================
    # ÁREA DE RISCO
    # ======================================================

    df["EH_AREA_RISCO"] = (
        df["Risk Type"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.casefold()
        .eq("risky area")
    )

    # ======================================================
    # CONSOLIDA POR TASK ID
    # ======================================================

    carregamentos = (
        df.groupby(
            [
                "Task ID",
                "Driver ID",
            ],
            dropna=False,
            as_index=False
        )
        .agg(
            DRIVER_NAME=(
                "Driver name",
                "first"
            ),

            DATA=(
                "DATA",
                "first"
            ),

            CREATE_TIME_DT=(
                "CREATE_TIME_DT",
                "first"
            ),

            CLUSTER=(
                "Cluster",
                "first"
            ),

            PACOTES_CARREGADOS=(
                "SPX tracking num",
                "nunique"
            ),

            PACOTES_AREA_RISCO=(
                "EH_AREA_RISCO",
                "sum"
            ),
        )
    )

    carregamentos = carregamentos.rename(
        columns={
            "Task ID": "TASK_ID",
            "Driver ID": "DRIVER_ID",
        }
    )

    # ======================================================
    # HORA
    # ======================================================

    carregamentos["HORA_CARREGAMENTO"] = (
        carregamentos[
            "CREATE_TIME_DT"
        ]
        .dt.strftime("%H:%M")
        .fillna("")
    )

    # ======================================================
    # TURNO
    # ======================================================

    carregamentos["TURNO_CARREGAMENTO"] = (
        carregamentos[
            "CREATE_TIME_DT"
        ]
        .apply(
            identificar_turno_carregamento
        )
    )

    # ======================================================
    # SEMANA
    # ======================================================

    carregamentos["SEMANA"] = (
        carregamentos["DATA"]
        .dt.strftime("%G-W%V")
        .fillna("")
    )

    # ======================================================
    # DATA
    # ======================================================

    carregamentos["DATA"] = (
        carregamentos["DATA"]
        .dt.strftime("%Y-%m-%d")
        .fillna("")
    )

    # ======================================================
    # PERCENTUAL ÁREA DE RISCO
    # ======================================================

    carregamentos[
        "PERCENTUAL_AREA_RISCO"
    ] = (
        (
            carregamentos[
                "PACOTES_AREA_RISCO"
            ]
            /
            carregamentos[
                "PACOTES_CARREGADOS"
            ]
        )
        * 100
    ).round(2)

    # ======================================================
    # DATA IMPORTAÇÃO
    # ======================================================

    carregamentos["DATA_IMPORTACAO"] = (
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    # ======================================================
    # AUXILIAR
    # ======================================================

    carregamentos = carregamentos.drop(
        columns=[
            "CREATE_TIME_DT"
        ]
    )

    # ======================================================
    # ORDEM FINAL
    # ======================================================

    return carregamentos[
        COLUNAS_CARREGAMENTO
    ].copy()

# ==========================================================
# TRADUÇÃO DOS MOTIVOS DE ONHOLD
# ==========================================================

TRADUCAO_ONHOLD = {
    "recipient unavailable for parcel": "Cliente ausente",
    "insufficient time": "Tempo insuficiente",
    "office closed": "Comércio fechado",
    "wrongly assigned": "Atribuição incorreta",
    "cannot find address": "Endereço não localizado",
    "parcel lost": "Pacote extraviado",
    "risky area of delivery": "Área de risco",
    "vehicle breakdown": "Problema com veículo",
    "incorrect/ missing verification": "Verificação incorreta/ausente",
    "recipient reject": "Destinatário recusou",
    "reject - buyers change their mind": "Cliente desistiu",
    "recipient change location": "Mudança de local",
    "do not deliver": "Não entregar",
    "parcel damaged, cannot attempt": "Pacote danificado",
}


def traduzir_motivo_onhold(valor):

    if pd.isna(valor):
        return "Não informado"

    texto = str(valor).strip()

    if not texto:
        return "Não informado"

    return TRADUCAO_ONHOLD.get(
        texto.casefold(),
        texto
    )


# ==========================================================
# PROCESSAMENTO DO FORWARD ORDER
# ==========================================================

def processar_ocorrencias(
    df_raw: pd.DataFrame,
    df_carregamentos: pd.DataFrame
):

    df = df_raw.copy()

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    # ======================================================
    # VALIDAÇÃO
    # ======================================================

    obrigatorias = [
        "SLS Tracking Number",
        "Driver ID",
        "Driver Name",
        "Delivering Time",
        "Status",
        "OnHoldReason",
    ]

    faltando = [
        coluna
        for coluna in obrigatorias
        if coluna not in df.columns
    ]

    if faltando:
        raise ValueError(
            "Colunas ausentes no Forward Order: "
            + ", ".join(faltando)
        )

    # ======================================================
    # NORMALIZA DRIVER
    # ======================================================

    df["DRIVER_ID"] = (
        df["Driver ID"]
        .astype(str)
        .str.replace(
            r"\.0$",
            "",
            regex=True
        )
        .str.strip()
    )

    df["DRIVER_NAME"] = (
        df["Driver Name"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # ======================================================
    # TRACKING
    # ======================================================

    df["TRACKING"] = (
        df["SLS Tracking Number"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # ======================================================
    # STATUS
    # ======================================================

    df["STATUS_NORM"] = (
        df["Status"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.casefold()
    )

    # ======================================================
    # DATA DO DELIVERING
    # ======================================================

    df["DELIVERING_DT"] = pd.to_datetime(
        df["Delivering Time"],
        errors="coerce",
        dayfirst=True
    )

    df["DATA_OPERACAO"] = (
        df["DELIVERING_DT"]
        .dt.date
    )

    df = df[
        df["DATA_OPERACAO"].notna()
    ].copy()

    if df.empty:
        raise ValueError(
            "Nenhuma data válida encontrada em Delivering Time."
        )

    # ======================================================
    # DATA DE REFERÊNCIA
    #
    # O arquivo é analisado pela data mais recente presente.
    # ======================================================

    data_referencia = (
        df["DATA_OPERACAO"].max()
    )

    # ======================================================
    # D-1 / DIA ANALISADO
    # ======================================================

    df_dia = df[
        df["DATA_OPERACAO"]
        == data_referencia
    ].copy()

    # ======================================================
    # ONHOLD DO DIA
    # ======================================================

    df_onhold = df_dia[
        df_dia["STATUS_NORM"]
        == "onhold"
    ].copy()

    df_onhold["MOTIVO_PT"] = (
        df_onhold["OnHoldReason"]
        .apply(traduzir_motivo_onhold)
    )

    # ======================================================
    # ABERTOS DO DIA
    # ======================================================

    df_abertos_d1 = df_dia[
        df_dia["STATUS_NORM"]
        == "delivering"
    ].copy()

    # ======================================================
    # PACOTES QUE PERMANECEM EM ABERTO
    # ======================================================

    df_abertos_antigos = df[
        (
            df["STATUS_NORM"]
            == "delivering"
        )
        &
        (
            df["DATA_OPERACAO"]
            < data_referencia
        )
    ].copy()

    # ======================================================
    # RESUMO ONHOLD POR DRIVER
    # ======================================================

    resumo_onhold = (
        df_onhold.groupby(
            "DRIVER_ID",
            as_index=False
        )
        .agg(
            ONHOLD=(
                "TRACKING",
                "nunique"
            )
        )
    )

    # ======================================================
    # MOTIVOS ONHOLD
    # ======================================================

    if not df_onhold.empty:

        motivos = (
            df_onhold.groupby(
                [
                    "DRIVER_ID",
                    "MOTIVO_PT"
                ],
                as_index=False
            )
            .agg(
                QTD=(
                    "TRACKING",
                    "nunique"
                )
            )
        )

        motivos = motivos.sort_values(
            [
                "DRIVER_ID",
                "QTD"
            ],
            ascending=[
                True,
                False
            ]
        )

        motivos["TEXTO"] = (
            motivos["MOTIVO_PT"]
            + " ("
            + motivos["QTD"].astype(str)
            + ")"
        )

        resumo_motivos = (
            motivos.groupby(
                "DRIVER_ID"
            )["TEXTO"]
            .apply(
                lambda valores:
                ", ".join(valores)
            )
            .reset_index(
                name="RESUMO_OCORRENCIAS"
            )
        )

        resumo_onhold = (
            resumo_onhold.merge(
                resumo_motivos,
                on="DRIVER_ID",
                how="left"
            )
        )

    else:

        resumo_onhold[
            "RESUMO_OCORRENCIAS"
        ] = ""

    # ======================================================
    # ABERTOS D-1
    # ======================================================

    resumo_abertos = (
        df_abertos_d1.groupby(
            "DRIVER_ID",
            as_index=False
        )
        .agg(
            ABERTOS_D1=(
                "TRACKING",
                "nunique"
            )
        )
    )

    # ======================================================
    # ABERTOS ANTIGOS
    # ======================================================

    if not df_abertos_antigos.empty:

        resumo_antigos = (
            df_abertos_antigos.groupby(
                "DRIVER_ID",
                as_index=False
            )
            .agg(
                PERMANECEM_ABERTOS=(
                    "TRACKING",
                    "nunique"
                ),
                DESDE=(
                    "DATA_OPERACAO",
                    "min"
                )
            )
        )

    else:

        resumo_antigos = pd.DataFrame(
            columns=[
                "DRIVER_ID",
                "PERMANECEM_ABERTOS",
                "DESDE",
            ]
        )

    # ======================================================
    # MOTORISTAS PRESENTES NO FORWARD
    # ======================================================

    motoristas = (
        df[
            [
                "DRIVER_ID",
                "DRIVER_NAME"
            ]
        ]
        .drop_duplicates(
            subset=["DRIVER_ID"],
            keep="first"
        )
    )

    base = motoristas.copy()

    base = base.merge(
        resumo_onhold,
        on="DRIVER_ID",
        how="left"
    )

    base = base.merge(
        resumo_abertos,
        on="DRIVER_ID",
        how="left"
    )

    base = base.merge(
        resumo_antigos,
        on="DRIVER_ID",
        how="left"
    )

    # ======================================================
    # ZEROS
    # ======================================================

    for coluna in [
        "ONHOLD",
        "ABERTOS_D1",
        "PERMANECEM_ABERTOS",
    ]:

        base[coluna] = (
            pd.to_numeric(
                base[coluna],
                errors="coerce"
            )
            .fillna(0)
            .astype(int)
        )

    base["RESUMO_OCORRENCIAS"] = (
        base["RESUMO_OCORRENCIAS"]
        .fillna("")
    )

    # ======================================================
    # CARREGAMENTOS
    # ======================================================

    carga = df_carregamentos.copy()

    if carga.empty:
        raise ValueError(
            "A base DADOS DE CARREGAMENTO está vazia."
        )

    carga.columns = (
        carga.columns
        .astype(str)
        .str.strip()
    )

    carga["DRIVER_ID"] = (
        carga["DRIVER_ID"]
        .astype(str)
        .str.replace(
            r"\.0$",
            "",
            regex=True
        )
        .str.strip()
    )

    carga["DATA_DT"] = pd.to_datetime(
        carga["DATA"],
        errors="coerce",
        dayfirst=True
    ).dt.date

    # somente carregamento do dia analisado
    carga_dia = carga[
        carga["DATA_DT"]
        == data_referencia
    ].copy()

    # campos numéricos vindos do Sheets
    carga_dia["PACOTES_CARREGADOS"] = (
        pd.to_numeric(
            carga_dia["PACOTES_CARREGADOS"],
            errors="coerce"
        )
        .fillna(0)
    )

    carga_dia["PACOTES_AREA_RISCO"] = (
        pd.to_numeric(
            carga_dia["PACOTES_AREA_RISCO"],
            errors="coerce"
        )
        .fillna(0)
    )

    # ======================================================
    # CONSOLIDA CASO DRIVER TENHA MAIS DE UMA TASK
    # ======================================================

    resumo_carga = (
        carga_dia.groupby(
            "DRIVER_ID",
            as_index=False
        )
        .agg(
            CARREGAMENTOS=(
                "TASK_ID",
                "nunique"
            ),

            PACOTES_CARREGADOS=(
                "PACOTES_CARREGADOS",
                "sum"
            ),

            PACOTES_AREA_RISCO=(
                "PACOTES_AREA_RISCO",
                "sum"
            ),

            HORA_CARREGAMENTO=(
                "HORA_CARREGAMENTO",
                lambda x:
                ", ".join(
                    dict.fromkeys(
                        str(v)
                        for v in x
                        if str(v).strip()
                    )
                )
            ),

            CLUSTER=(
                "CLUSTER",
                lambda x:
                ", ".join(
                    dict.fromkeys(
                        str(v)
                        for v in x
                        if str(v).strip()
                    )
                )
            ),
        )
    )

    base = base.merge(
        resumo_carga,
        on="DRIVER_ID",
        how="left"
    )

    # ======================================================
    # NÚMEROS DE CARGA
    # ======================================================

    base["CARREGAMENTOS"] = (
        pd.to_numeric(
            base["CARREGAMENTOS"],
            errors="coerce"
        )
        .fillna(0)
        .astype(int)
    )

    base["PACOTES_CARREGADOS"] = (
        pd.to_numeric(
            base["PACOTES_CARREGADOS"],
            errors="coerce"
        )
        .fillna(0)
        .astype(int)
    )

    base["PACOTES_AREA_RISCO"] = (
        pd.to_numeric(
            base["PACOTES_AREA_RISCO"],
            errors="coerce"
        )
        .fillna(0)
        .astype(int)
    )

    base["HORA_CARREGAMENTO"] = (
        base["HORA_CARREGAMENTO"]
        .fillna("")
    )

    base["CLUSTER"] = (
        base["CLUSTER"]
        .fillna("")
    )

    # ======================================================
    # PERCENTUAIS
    # ======================================================

    base["PERCENTUAL_OCORRENCIA"] = 0.0
    base["PERCENTUAL_ABERTO"] = 0.0
    base["PERCENTUAL_AREA_RISCO"] = 0.0

    possui_carga = (
        base["PACOTES_CARREGADOS"] > 0
    )

    base.loc[
        possui_carga,
        "PERCENTUAL_OCORRENCIA"
    ] = (
        base.loc[
            possui_carga,
            "ONHOLD"
        ]
        /
        base.loc[
            possui_carga,
            "PACOTES_CARREGADOS"
        ]
        * 100
    )

    base.loc[
        possui_carga,
        "PERCENTUAL_ABERTO"
    ] = (
        base.loc[
            possui_carga,
            "ABERTOS_D1"
        ]
        /
        base.loc[
            possui_carga,
            "PACOTES_CARREGADOS"
        ]
        * 100
    )

    base.loc[
        possui_carga,
        "PERCENTUAL_AREA_RISCO"
    ] = (
        base.loc[
            possui_carga,
            "PACOTES_AREA_RISCO"
        ]
        /
        base.loc[
            possui_carga,
            "PACOTES_CARREGADOS"
        ]
        * 100
    )

    for coluna in [
        "PERCENTUAL_OCORRENCIA",
        "PERCENTUAL_ABERTO",
        "PERCENTUAL_AREA_RISCO",
    ]:

        base[coluna] = (
            base[coluna]
            .round(2)
        )

    # ======================================================
    # REALIZAÇÃO DA ROTA
    #
    # Por enquanto é uma estimativa operacional:
    # 100% - OnHold - aberto D1
    # ======================================================

    base["REALIZACAO_ROTA"] = 0.0

    base.loc[
        possui_carga,
        "REALIZACAO_ROTA"
    ] = (
        100
        -
        base.loc[
            possui_carga,
            "PERCENTUAL_OCORRENCIA"
        ]
        -
        base.loc[
            possui_carga,
            "PERCENTUAL_ABERTO"
        ]
    )

    base["REALIZACAO_ROTA"] = (
        base["REALIZACAO_ROTA"]
        .clip(
            lower=0,
            upper=100
        )
        .round(2)
    )

    # ======================================================
    # CLASSIFICAÇÃO
    # ======================================================

    base["OFENSOR_OCORRENCIA"] = (
        base["ONHOLD"] > 5
    )

    base["OFENSOR_ABERTO_D1"] = (
        base["ABERTOS_D1"] > 10
    )

    base["OFENSOR_ABERTO_ANTIGO"] = (
        base["PERMANECEM_ABERTOS"] > 10
    )

    base["OFENSOR"] = (
        base["OFENSOR_OCORRENCIA"]
        |
        base["OFENSOR_ABERTO_D1"]
        |
        base["OFENSOR_ABERTO_ANTIGO"]
    )

    base["DATA"] = (
        data_referencia.strftime(
            "%Y-%m-%d"
        )
    )

    # ======================================================
    # DATA DESDE
    # ======================================================

    base["DESDE"] = base["DESDE"].apply(
        lambda valor:
        valor.strftime("%Y-%m-%d")
        if pd.notna(valor)
        else ""
    )

    # ======================================================
    # RETORNOS
    # ======================================================

    ofensores = base[
        base["OFENSOR"]
    ].copy()

    return {
        "data_referencia": data_referencia,
        "base_completa": base,
        "ofensores": ofensores,
        "onhold_raw": df_onhold,
        "abertos_d1_raw": df_abertos_d1,
        "abertos_antigos_raw": df_abertos_antigos,
    }