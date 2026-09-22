import pandas as pd
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
import math
import streamlit as st
import os

ARQUIVO_CREDENCIAIS = "keys.json"
NOME_PLANILHA = "Ofensores DB"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


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

def conectar_google_sheets():

    # ======================================================
    # LOCAL
    # ======================================================

    if os.path.exists("keys.json"):

        credenciais = Credentials.from_service_account_file(
            "keys.json",
            scopes=SCOPES
        )

    # ======================================================
    # STREAMLIT CLOUD
    # ======================================================

    else:

        credenciais_dict = dict(
            st.secrets["gcp_service_account"]
        )

        credenciais = Credentials.from_service_account_info(
            credenciais_dict,
            scopes=SCOPES
        )

    return gspread.authorize(
        credenciais
    )

def abrir_planilha():

    return conectar_google_sheets().open(
        NOME_PLANILHA
    )


def obter_aba(nome_aba):

    return abrir_planilha().worksheet(
        nome_aba
    )


# ==========================================================
# LEITURA
# ==========================================================

def carregar_dados_aba(nome_aba):

    aba = obter_aba(nome_aba)

    valores = aba.get_all_values()

    if len(valores) <= 1:
        return pd.DataFrame()

    cabecalho = valores[0]

    return pd.DataFrame(
        valores[1:],
        columns=cabecalho
    )


# ==========================================================
# VALIDAÇÃO
# ==========================================================

def salvar_carregamentos_sem_duplicar(
    df_novo: pd.DataFrame
):
    nome_aba = "DADOS DE CARREGAMENTO"

    aba = obter_aba(nome_aba)

    # ======================================================
    # CABEÇALHO REAL DO GOOGLE SHEETS
    # ======================================================

    cabecalho = [
        str(valor).strip()
        for valor in aba.row_values(1)
    ]

    print("CABEÇALHO SHEETS:")
    print(cabecalho)

    # Colunas que obrigatoriamente precisamos
    obrigatorias = [
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

    faltando_sheets = [
        col
        for col in obrigatorias
        if col not in cabecalho
    ]

    if faltando_sheets:
        raise ValueError(
            "Estas colunas não existem no Sheets: "
            + ", ".join(faltando_sheets)
        )

    # ======================================================
    # CONFERE DATAFRAME
    # ======================================================

    df = df_novo.copy()

    faltando_df = [
        col
        for col in obrigatorias
        if col not in df.columns
    ]

    if faltando_df:
        raise ValueError(
            "Estas colunas não existem no DataFrame: "
            + ", ".join(faltando_df)
        )

    # ======================================================
    # NORMALIZA TASK ID
    # ======================================================

    df["TASK_ID"] = (
        df["TASK_ID"]
        .astype(str)
        .str.strip()
    )

    # ======================================================
    # TASKS JÁ EXISTENTES
    # ======================================================

    coluna_task = cabecalho.index("TASK_ID") + 1

    tasks_existentes = aba.col_values(
        coluna_task
    )[1:]

    ids_existentes = {
        str(valor).strip()
        for valor in tasks_existentes
        if str(valor).strip()
    }

    mascara_duplicado = (
        df["TASK_ID"].isin(ids_existentes)
    )

    duplicados = int(
        mascara_duplicado.sum()
    )

    novos = df[
        ~mascara_duplicado
    ].copy()

    if novos.empty:
        return {
            "salvos": 0,
            "duplicados": duplicados
        }

    # ======================================================
    # MONTA LINHAS USANDO O CABEÇALHO DO SHEETS
    # ======================================================

    linhas = []

    for _, registro in novos.iterrows():

        linha = []

        for coluna_sheets in cabecalho:

            # Caso exista alguma coluna vazia física no Sheets
            if not coluna_sheets:
                linha.append("")
                continue

            # Se o DataFrame possui essa coluna
            if coluna_sheets in registro.index:

                valor = registro[coluna_sheets]

                if pd.isna(valor):
                    valor = ""

                elif isinstance(valor, (float, int)):

                    if not math.isfinite(float(valor)):
                        valor = ""

                linha.append(valor)

            else:
                # Coluna do Sheets que não pertence a esta importação
                linha.append("")

        linhas.append(linha)

    # ======================================================
    # DEBUG - PRIMEIRA LINHA
    # ======================================================

    print("\nPRIMEIRO REGISTRO A SER GRAVADO:")

    for coluna, valor in zip(
        cabecalho,
        linhas[0]
    ):
        print(f"{coluna} = {valor}")

    # ======================================================
    # GRAVA
    # ======================================================

    aba.append_rows(
        linhas,
        value_input_option="USER_ENTERED"
    )

    return {
        "salvos": len(linhas),
        "duplicados": duplicados
    }
def salvar_ofensores_sem_duplicar(
    df_ofensores: pd.DataFrame
):
    nome_aba = "DADOS DE OFENSORES"

    aba = obter_aba(nome_aba)

    colunas = [
        "DATA",
        "DRIVER_ID",
        "DRIVER_NAME",
        "CARREGAMENTOS",
        "PACOTES_CARREGADOS",
        "ONHOLD",
        "PERCENTUAL_OCORRENCIA",
        "ABERTOS_D1",
        "PERCENTUAL_ABERTO",
        "PERMANECEM_ABERTOS",
        "DESDE",
        "RESUMO_OCORRENCIAS",
        "CLUSTER",
        "HORA_CARREGAMENTO",
        "PACOTES_AREA_RISCO",
        "PERCENTUAL_AREA_RISCO",
        "REALIZACAO_ROTA",
        "OFENSOR_OCORRENCIA",
        "OFENSOR_ABERTO_D1",
        "OFENSOR_ABERTO_ANTIGO",
        "DATA_IMPORTACAO",
    ]

    df = df_ofensores.copy()

    # ==========================================
    # GARANTE COLUNAS
    # ==========================================

    faltando = [
        col
        for col in colunas
        if col not in df.columns
        and col != "DATA_IMPORTACAO"
    ]

    if faltando:
        raise ValueError(
            "Colunas ausentes para salvar ofensores: "
            + ", ".join(faltando)
        )

    # ==========================================
    # DATA IMPORTAÇÃO
    # ==========================================

    df["DATA_IMPORTACAO"] = (
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    # ==========================================
    # NORMALIZA
    # ==========================================

    df["DRIVER_ID"] = (
        df["DRIVER_ID"]
        .astype(str)
        .str.replace(
            r"\.0$",
            "",
            regex=True
        )
        .str.strip()
    )

    df["DATA"] = (
        df["DATA"]
        .astype(str)
        .str.strip()
    )

    # chave única:
    # DATA + DRIVER_ID
    df["CHAVE"] = (
        df["DATA"]
        + "|"
        + df["DRIVER_ID"]
    )

    # ==========================================
    # LÊ O QUE JÁ EXISTE
    # ==========================================

    registros_existentes = (
        aba.get_all_records()
    )

    chaves_existentes = set()

    for registro in registros_existentes:

        data = str(
            registro.get("DATA", "")
        ).strip()

        driver_id = str(
            registro.get("DRIVER_ID", "")
        ).replace(
            ".0",
            ""
        ).strip()

        if data and driver_id:
            chaves_existentes.add(
                f"{data}|{driver_id}"
            )

    # ==========================================
    # REMOVE DUPLICADOS
    # ==========================================

    mascara_duplicado = (
        df["CHAVE"]
        .isin(chaves_existentes)
    )

    duplicados = int(
        mascara_duplicado.sum()
    )

    novos = df[
        ~mascara_duplicado
    ].copy()

    if novos.empty:
        return {
            "salvos": 0,
            "duplicados": duplicados
        }

    # ==========================================
    # CABEÇALHO REAL DO SHEETS
    # ==========================================

    cabecalho = [
        str(valor).strip()
        for valor in aba.row_values(1)
    ]

    # ==========================================
    # MONTA LINHAS PELO NOME DA COLUNA
    # ==========================================

    linhas = []

    for _, row in novos.iterrows():

        linha = []

        for coluna in cabecalho:

            if not coluna:
                linha.append("")
                continue

            if coluna in row.index:

                valor = row[coluna]

                if pd.isna(valor):
                    valor = ""

                # boolean vira texto legível
                if isinstance(valor, bool):
                    valor = "SIM" if valor else "NÃO"

                linha.append(valor)

            else:
                linha.append("")

        linhas.append(linha)

    # ==========================================
    # SALVA
    # ==========================================

    aba.append_rows(
        linhas,
        value_input_option="USER_ENTERED"
    )

    return {
        "salvos": len(linhas),
        "duplicados": duplicados
    }

# ==========================================================
# TRATATIVAS
# ==========================================================

COLUNAS_TRATATIVA = [
    "TRATATIVA_ID",
    "DATA_OFENSA",
    "DRIVER_ID",
    "DRIVER_NAME",
    "TIPO_OFENSA",
    "ONHOLD",
    "ABERTOS_D1",
    "PERMANECEM_ABERTOS",
    "RESUMO_OCORRENCIAS",
    "CLUSTER",
    "D0",
    "DATA_TRATATIVA",
    "TIPO_TRATATIVA",
    "RESPONSAVEL",
    "OBSERVACAO",
    "STATUS_TRATATIVA",
    "DATA_CONCLUSAO",
    "DATA_ATUALIZACAO",
]


# ==========================================================
# NORMALIZAR DRIVER ID
# ==========================================================

def _normalizar_driver_id(valor):

    if pd.isna(valor):
        return ""

    return (
        str(valor)
        .replace(".0", "")
        .strip()
    )


# ==========================================================
# NORMALIZAR DATA
# ==========================================================

def _normalizar_data_tratativa(valor):

    if valor is None:
        return ""

    if pd.isna(valor):
        return ""

    if isinstance(valor, pd.Timestamp):
        return valor.strftime("%Y-%m-%d")

    if isinstance(valor, datetime):
        return valor.strftime("%Y-%m-%d")

    texto = str(valor).strip()

    if not texto:
        return ""

    data = pd.to_datetime(
        texto,
        errors="coerce",
        dayfirst=True
    )

    if pd.isna(data):
        return texto

    return data.strftime("%Y-%m-%d")


# ==========================================================
# GERAR ID DA TRATATIVA
# ==========================================================

def gerar_tratativa_id(
    driver_id,
    data_ofensa
):

    driver_id = _normalizar_driver_id(
        driver_id
    )

    data_ofensa = _normalizar_data_tratativa(
        data_ofensa
    )

    agora = datetime.now().strftime(
        "%Y%m%d%H%M%S%f"
    )

    return (
        f"TRAT-{driver_id}-"
        f"{data_ofensa.replace('-', '')}-"
        f"{agora}"
    )


# ==========================================================
# CARREGAR TRATATIVAS
# ==========================================================

def carregar_tratativas():

    try:

        df = carregar_dados_aba(
            "DADOS DE TRATATIVA"
        )

        if df.empty:
            return pd.DataFrame(
                columns=COLUNAS_TRATATIVA
            )

        # ==============================================
        # GARANTE COLUNAS
        # ==============================================

        for coluna in COLUNAS_TRATATIVA:

            if coluna not in df.columns:
                df[coluna] = ""

        # ==============================================
        # NORMALIZA DRIVER
        # ==============================================

        df["DRIVER_ID"] = (
            df["DRIVER_ID"]
            .apply(
                _normalizar_driver_id
            )
        )

        # ==============================================
        # NORMALIZA DATAS
        # ==============================================

        for coluna in [
            "DATA_OFENSA",
            "DATA_TRATATIVA",
            "DATA_CONCLUSAO",
            "DATA_ATUALIZACAO",
        ]:

            if coluna in df.columns:

                df[coluna] = (
                    df[coluna]
                    .astype(str)
                    .str.strip()
                )

        return df

    except gspread.WorksheetNotFound:

        raise ValueError(
            "A aba 'DADOS DE TRATATIVA' "
            "não existe no Google Sheets."
        )


# ==========================================================
# BUSCAR TRATATIVA DA OFENSA
#
# A chave operacional é:
#
# DATA_OFENSA + DRIVER_ID
#
# Assim uma mesma ofensa não recebe duas tratativas.
# ==========================================================

def buscar_tratativa_ofensa(
    driver_id,
    data_ofensa
):

    driver_id = _normalizar_driver_id(
        driver_id
    )

    data_ofensa = _normalizar_data_tratativa(
        data_ofensa
    )

    df = carregar_tratativas()

    if df.empty:
        return None

    datas = (
        df["DATA_OFENSA"]
        .apply(
            _normalizar_data_tratativa
        )
    )

    mascara = (
        (
            df["DRIVER_ID"]
            == driver_id
        )
        &
        (
            datas
            == data_ofensa
        )
    )

    encontrados = df[
        mascara
    ].copy()

    if encontrados.empty:
        return None

    return (
        encontrados.iloc[-1]
        .to_dict()
    )


# ==========================================================
# SALVAR NOVA TRATATIVA
# ==========================================================

def salvar_tratativa(
    data_ofensa,
    driver_id,
    driver_name,
    tipo_ofensa,
    onhold=0,
    abertos_d1=0,
    permanecem_abertos=0,
    resumo_ocorrencias="",
    cluster="",
    d0=0,
    tipo_tratativa="",
    responsavel="",
    observacao="",
    status_tratativa="Pendente",
):

    nome_aba = "DADOS DE TRATATIVA"

    aba = obter_aba(
        nome_aba
    )

    # ======================================================
    # NORMALIZA
    # ======================================================

    driver_id = _normalizar_driver_id(
        driver_id
    )

    data_ofensa = _normalizar_data_tratativa(
        data_ofensa
    )

    driver_name = (
        str(driver_name)
        .strip()
    )

    # ======================================================
    # VERIFICA SE ESSA OFENSA JÁ TEM TRATATIVA
    # ======================================================

    existente = buscar_tratativa_ofensa(
        driver_id,
        data_ofensa
    )

    if existente:

        return {
            "salvo": False,
            "duplicado": True,
            "tratativa_id": existente.get(
                "TRATATIVA_ID",
                ""
            )
        }

    # ======================================================
    # CABEÇALHO REAL
    # ======================================================

    cabecalho = [
        str(valor).strip()
        for valor
        in aba.row_values(1)
    ]

    faltando = [
        coluna
        for coluna
        in COLUNAS_TRATATIVA
        if coluna not in cabecalho
    ]

    if faltando:

        raise ValueError(
            "Estas colunas não existem em "
            "'DADOS DE TRATATIVA': "
            + ", ".join(faltando)
        )

    # ======================================================
    # ID
    # ======================================================

    tratativa_id = gerar_tratativa_id(
        driver_id,
        data_ofensa
    )

    agora = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # ======================================================
    # DATA DA TRATATIVA
    #
    # Se ainda estiver pendente e nenhuma ação foi
    # informada, deixamos em branco.
    # ======================================================

    houve_acao = bool(
        str(tipo_tratativa).strip()
        or str(responsavel).strip()
        or str(observacao).strip()
        or status_tratativa
        in [
            "Em acompanhamento",
            "Concluída"
        ]
    )

    data_tratativa = (
        agora
        if houve_acao
        else ""
    )

    # ======================================================
    # DATA CONCLUSÃO
    # ======================================================

    data_conclusao = (
        agora
        if status_tratativa
        == "Concluída"
        else ""
    )

    # ======================================================
    # REGISTRO
    # ======================================================

    registro = {

        "TRATATIVA_ID":
            tratativa_id,

        "DATA_OFENSA":
            data_ofensa,

        "DRIVER_ID":
            driver_id,

        "DRIVER_NAME":
            driver_name,

        "TIPO_OFENSA":
            str(
                tipo_ofensa
            ).strip(),

        "ONHOLD":
            onhold,

        "ABERTOS_D1":
            abertos_d1,

        "PERMANECEM_ABERTOS":
            permanecem_abertos,

        "RESUMO_OCORRENCIAS":
            str(
                resumo_ocorrencias
            ).strip(),

        "CLUSTER":
            str(
                cluster
            ).strip(),

        "D0":
            d0,

        "DATA_TRATATIVA":
            data_tratativa,

        "TIPO_TRATATIVA":
            str(
                tipo_tratativa
            ).strip(),

        "RESPONSAVEL":
            str(
                responsavel
            ).strip(),

        "OBSERVACAO":
            str(
                observacao
            ).strip(),

        "STATUS_TRATATIVA":
            str(
                status_tratativa
            ).strip(),

        "DATA_CONCLUSAO":
            data_conclusao,

        "DATA_ATUALIZACAO":
            agora,
    }

    # ======================================================
    # MONTA NA ORDEM FÍSICA DO SHEETS
    # ======================================================

    linha = []

    for coluna in cabecalho:

        if not coluna:

            linha.append("")
            continue

        valor = registro.get(
            coluna,
            ""
        )

        if pd.isna(valor):
            valor = ""

        linha.append(
            valor
        )

    # ======================================================
    # SALVA
    # ======================================================

    aba.append_row(
        linha,
        value_input_option="USER_ENTERED"
    )

    return {
        "salvo": True,
        "duplicado": False,
        "tratativa_id": tratativa_id
    }


# ==========================================================
# ATUALIZAR TRATATIVA
# ==========================================================

def atualizar_tratativa(
    tratativa_id,
    tipo_tratativa=None,
    responsavel=None,
    observacao=None,
    status_tratativa=None,
):

    aba = obter_aba(
        "DADOS DE TRATATIVA"
    )

    valores = (
        aba.get_all_values()
    )

    if len(valores) <= 1:

        raise ValueError(
            "Nenhuma tratativa encontrada."
        )

    cabecalho = [
        str(valor).strip()
        for valor in valores[0]
    ]

    if (
        "TRATATIVA_ID"
        not in cabecalho
    ):

        raise ValueError(
            "A coluna TRATATIVA_ID "
            "não existe no Sheets."
        )

    coluna_id = (
        cabecalho.index(
            "TRATATIVA_ID"
        )
    )

    linha_encontrada = None

    # +2 porque:
    # linha 1 = cabeçalho
    # enumerate começa em 0
    for numero, linha in enumerate(
        valores[1:],
        start=2
    ):

        if (
            coluna_id
            < len(linha)
        ):

            valor_id = str(
                linha[
                    coluna_id
                ]
            ).strip()

            if (
                valor_id
                == str(
                    tratativa_id
                ).strip()
            ):

                linha_encontrada = (
                    numero
                )

                break

    if linha_encontrada is None:

        raise ValueError(
            "Tratativa não encontrada."
        )

    agora = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # ======================================================
    # ALTERA SOMENTE O QUE FOI ENVIADO
    # ======================================================

    atualizacoes = {}

    if tipo_tratativa is not None:

        atualizacoes[
            "TIPO_TRATATIVA"
        ] = str(
            tipo_tratativa
        ).strip()

    if responsavel is not None:

        atualizacoes[
            "RESPONSAVEL"
        ] = str(
            responsavel
        ).strip()

    if observacao is not None:

        atualizacoes[
            "OBSERVACAO"
        ] = str(
            observacao
        ).strip()

    if status_tratativa is not None:

        atualizacoes[
            "STATUS_TRATATIVA"
        ] = str(
            status_tratativa
        ).strip()

    # ======================================================
    # DATA TRATATIVA
    #
    # Se houve uma ação e ainda não existe data,
    # registra agora.
    # ======================================================

    if (
        "DATA_TRATATIVA"
        in cabecalho
    ):

        coluna_data_tratativa = (
            cabecalho.index(
                "DATA_TRATATIVA"
            )
            + 1
        )

        valor_atual = (
            aba.cell(
                linha_encontrada,
                coluna_data_tratativa
            ).value
        )

        if not str(
            valor_atual or ""
        ).strip():

            atualizacoes[
                "DATA_TRATATIVA"
            ] = agora

    # ======================================================
    # CONCLUSÃO
    # ======================================================

    if (
        status_tratativa
        == "Concluída"
    ):

        atualizacoes[
            "DATA_CONCLUSAO"
        ] = agora

    elif (
        status_tratativa
        is not None
        and status_tratativa
        != "Concluída"
    ):

        atualizacoes[
            "DATA_CONCLUSAO"
        ] = ""

    atualizacoes[
        "DATA_ATUALIZACAO"
    ] = agora

    # ======================================================
    # UPDATE
    # ======================================================

    for (
        coluna,
        valor
    ) in atualizacoes.items():

        if coluna not in cabecalho:
            continue

        numero_coluna = (
            cabecalho.index(
                coluna
            )
            + 1
        )

        aba.update_cell(
            linha_encontrada,
            numero_coluna,
            valor
        )

    return {
        "atualizado": True,
        "tratativa_id": tratativa_id
    }


# ==========================================================
# HISTÓRICO DE TRATATIVAS DO DRIVER
# ==========================================================

def buscar_historico_tratativas_driver(
    driver_id
):

    driver_id = (
        _normalizar_driver_id(
            driver_id
        )
    )

    df = carregar_tratativas()

    if df.empty:

        return df

    df_driver = (
        df[
            df["DRIVER_ID"]
            == driver_id
        ]
        .copy()
    )

    if df_driver.empty:

        return df_driver

    df_driver[
        "DATA_OFENSA_DT"
    ] = pd.to_datetime(
        df_driver[
            "DATA_OFENSA"
        ],
        errors="coerce",
        dayfirst=True
    )

    return (
        df_driver
        .sort_values(
            "DATA_OFENSA_DT",
            ascending=False
        )
    )


# ==========================================================
# SITUAÇÃO DE TRATATIVA DO DRIVER
#
# Retorna:
#
# PRIMEIRA_OFENSA
# JA_TRATADO
# REINCIDENTE_APOS_TRATATIVA
#
# Também informa:
#
# última tratativa
# última data
# quantidade de ofensas posteriores
# ==========================================================
def analisar_reincidencia_pos_tratativa(
    driver_id,
    data_ofensa,
    df_historico_ofensores=None,
    df_tratativas=None
):

    driver_id = _normalizar_driver_id(
        driver_id
    )

    data_ofensa_dt = pd.to_datetime(
        data_ofensa,
        errors="coerce",
        dayfirst=True
    )

    # ======================================================
    # TRATATIVAS
    #
    # Se o app já carregou as tratativas,
    # reutiliza o DataFrame e NÃO consulta o Sheets novamente.
    # ======================================================

    if df_tratativas is None:

        df_tratativas = carregar_tratativas()

    else:

        df_tratativas = df_tratativas.copy()

    # ======================================================
    # NUNCA FOI TRATADO
    # ======================================================

    if df_tratativas.empty:

        return {
            "ja_tratado": False,
            "reincidente_pos_tratativa": False,
            "ultima_tratativa": "",
            "data_ultima_tratativa": "",
            "ofensas_apos_tratativa": 0,
        }

    # ======================================================
    # FILTRA DRIVER
    # ======================================================

    df_driver = (
        df_tratativas[
            df_tratativas["DRIVER_ID"]
            .apply(_normalizar_driver_id)
            == driver_id
        ]
        .copy()
    )

    if df_driver.empty:

        return {
            "ja_tratado": False,
            "reincidente_pos_tratativa": False,
            "ultima_tratativa": "",
            "data_ultima_tratativa": "",
            "ofensas_apos_tratativa": 0,
        }

    # ======================================================
    # STATUS
    # ======================================================

    df_driver["STATUS_NORMALIZADO"] = (
        df_driver["STATUS_TRATATIVA"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    # Somente tratativas realmente realizadas
    df_realizadas = (
        df_driver[
            df_driver["STATUS_NORMALIZADO"]
            .isin(
                [
                    "em acompanhamento",
                    "concluída",
                    "concluida",
                ]
            )
        ]
        .copy()
    )

    if df_realizadas.empty:

        return {
            "ja_tratado": False,
            "reincidente_pos_tratativa": False,
            "ultima_tratativa": "",
            "data_ultima_tratativa": "",
            "ofensas_apos_tratativa": 0,
        }

    # ======================================================
    # DATAS
    # ======================================================

    df_realizadas["DATA_TRATATIVA_DT"] = pd.to_datetime(
        df_realizadas["DATA_TRATATIVA"],
        errors="coerce",
        dayfirst=True
    )

    df_realizadas["DATA_CONCLUSAO_DT"] = pd.to_datetime(
        df_realizadas["DATA_CONCLUSAO"],
        errors="coerce",
        dayfirst=True
    )

    # ======================================================
    # DATA DE REFERÊNCIA
    #
    # A reincidência deve considerar quando a ação ocorreu,
    # e não somente quando ela foi concluída.
    # ======================================================

    df_realizadas["DATA_REFERENCIA_TRATATIVA"] = (
        df_realizadas["DATA_TRATATIVA_DT"]
        .fillna(
            df_realizadas["DATA_CONCLUSAO_DT"]
        )
    )

    df_realizadas = (
        df_realizadas[
            df_realizadas[
                "DATA_REFERENCIA_TRATATIVA"
            ].notna()
        ]
        .copy()
    )

    if df_realizadas.empty:

        return {
            "ja_tratado": False,
            "reincidente_pos_tratativa": False,
            "ultima_tratativa": "",
            "data_ultima_tratativa": "",
            "ofensas_apos_tratativa": 0,
        }

    # ======================================================
    # SOMENTE TRATATIVAS ANTERIORES À OFENSA ATUAL
    # ======================================================

    anteriores = (
        df_realizadas[
            df_realizadas[
                "DATA_REFERENCIA_TRATATIVA"
            ]
            < data_ofensa_dt
        ]
        .copy()
    )

    if anteriores.empty:

        return {
            "ja_tratado": False,
            "reincidente_pos_tratativa": False,
            "ultima_tratativa": "",
            "data_ultima_tratativa": "",
            "ofensas_apos_tratativa": 0,
        }

    # ======================================================
    # ÚLTIMA TRATATIVA ANTERIOR
    # ======================================================

    anteriores = (
        anteriores
        .sort_values(
            "DATA_REFERENCIA_TRATATIVA",
            ascending=False
        )
    )

    ultima = anteriores.iloc[0]

    data_ultima = ultima[
        "DATA_REFERENCIA_TRATATIVA"
    ]

    # ======================================================
    # QUANTIDADE DE OFENSAS APÓS A TRATATIVA
    # ======================================================

    quantidade_pos = 1

    if (
        df_historico_ofensores is not None
        and not df_historico_ofensores.empty
    ):

        hist = df_historico_ofensores.copy()

        if (
            "DRIVER_ID" in hist.columns
            and "DATA" in hist.columns
        ):

            hist["DRIVER_ID_NORMALIZADO"] = (
                hist["DRIVER_ID"]
                .apply(_normalizar_driver_id)
            )

            hist["DATA_OFENSA_DT"] = pd.to_datetime(
                hist["DATA"],
                errors="coerce",
                dayfirst=True
            )

            # ----------------------------------------------
            # Somente NOVAS OFENSAS.
            # Persistência antiga não vira reincidência.
            # ----------------------------------------------

            if (
                "ONHOLD" in hist.columns
                and "ABERTOS_D1" in hist.columns
            ):

                hist["ONHOLD_NUM"] = (
                    pd.to_numeric(
                        hist["ONHOLD"],
                        errors="coerce"
                    )
                    .fillna(0)
                )

                hist["ABERTOS_D1_NUM"] = (
                    pd.to_numeric(
                        hist["ABERTOS_D1"],
                        errors="coerce"
                    )
                    .fillna(0)
                )

                hist["NOVA_OFENSA_ANALISE"] = (
                    (hist["ONHOLD_NUM"] > 5)
                    |
                    (hist["ABERTOS_D1_NUM"] > 10)
                )

            else:

                hist["NOVA_OFENSA_ANALISE"] = True

            hist_driver = (
                hist[
                    (
                        hist["DRIVER_ID_NORMALIZADO"]
                        == driver_id
                    )
                    &
                    (
                        hist["DATA_OFENSA_DT"]
                        > data_ultima
                    )
                    &
                    (
                        hist["DATA_OFENSA_DT"]
                        <= data_ofensa_dt
                    )
                    &
                    (
                        hist["NOVA_OFENSA_ANALISE"]
                    )
                ]
                .copy()
            )

            quantidade_pos = (
                hist_driver["DATA_OFENSA_DT"]
                .dt.date
                .nunique()
            )

    # ======================================================
    # RETORNO
    # ======================================================

    return {
        "ja_tratado": True,
        "reincidente_pos_tratativa": True,

        "ultima_tratativa": str(
            ultima.get(
                "TIPO_TRATATIVA",
                ""
            )
        ),

        "data_ultima_tratativa": (
            data_ultima.strftime(
                "%d/%m/%Y"
            )
        ),

        "ofensas_apos_tratativa": int(
            quantidade_pos
        ),
    }