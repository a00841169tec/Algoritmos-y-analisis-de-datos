"""
Entrega 1 - Punto 1: Adquisicion y Limpieza de Datos

Lee los CSV de precios historicos de 10 acciones (formato yfinance:
Date, Open, High, Low, Close, Adj Close, Volume - uno por accion),
los combina, limpia y guarda el resultado en:
  - data/processed/precios_limpios.csv
  - data/processed/retornos_diarios.csv
  - la base de datos SQLite "fondo.db" (tablas "precios" y "retornos")

MODIFICA la seccion CONFIG para apuntar a tus archivos reales.
"""

import glob
import os
import sqlite3

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# CONFIG - ajusta esto a tus archivos
# ---------------------------------------------------------------------------

RAW_DATA_DIR = "data/raw"

# Mapeo archivo -> ticker. Si tus CSV se llaman igual que el ticker
# (p.ej. "AAPL.csv", "WALMEX.MX.csv"), puedes generarlo automaticamente:
ARCHIVOS = {
    os.path.splitext(os.path.basename(f))[0]: f
    for f in glob.glob(os.path.join(RAW_DATA_DIR, "*.csv"))
}

# O bien, defínelo a mano si prefieres controlar el orden/nombres:
# ARCHIVOS = {
#     "AAPL": "data/raw/AAPL.csv",
#     "MSFT": "data/raw/MSFT.csv",
#     "WALMEX.MX": "data/raw/WALMEX.MX.csv",
#     ...
# }

DB_PATH = "fondo.db"
OUT_PRECIOS = "data/processed/precios_limpios.csv"
OUT_RETORNOS = "data/processed/retornos_diarios.csv"

# Umbral para marcar un retorno diario como posible error de datos
# (dato "fat-finger", split no ajustado, etc.)
UMBRAL_RETORNO_ATIPICO = 0.40  # 40% en un dia

# ---------------------------------------------------------------------------
# 1. Adquisicion: cargar y unificar los CSV crudos
# ---------------------------------------------------------------------------


def cargar_crudos(archivos: dict[str, str]) -> pd.DataFrame:
    frames = []
    for ticker, path in archivos.items():
        df = pd.read_csv(path)
        df.columns = [c.strip() for c in df.columns]
        df["Ticker"] = ticker
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# 2. Limpieza
# ---------------------------------------------------------------------------


def limpiar(df: pd.DataFrame) -> pd.DataFrame:
    reporte = {}

    # --- Normalizar nombres y tipos de columnas ---
    df = df.rename(columns={"Adj Close": "Adj_Close"})
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    columnas_numericas = ["Open", "High", "Low", "Close", "Adj_Close", "Volume"]
    for col in columnas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # --- Duplicados exactos (mismo Ticker + Date) ---
    antes = len(df)
    df = df.drop_duplicates(subset=["Ticker", "Date"], keep="first")
    reporte["duplicados_eliminados"] = antes - len(df)

    # --- Fechas invalidas ---
    antes = len(df)
    df = df.dropna(subset=["Date"])
    reporte["fechas_invalidas_eliminadas"] = antes - len(df)

    # --- Valores faltantes en precios/volumen ---
    reporte["nulos_antes"] = int(df[columnas_numericas].isna().sum().sum())

    df = df.sort_values(["Ticker", "Date"]).reset_index(drop=True)

    # Interpola dentro de cada ticker (huecos cortos, p.ej. feriados no
    # alineados entre mercados) y luego elimina lo que no se pudo rellenar
    # (p.ej. el primer o ultimo dato de una serie faltante).
    df[columnas_numericas] = df.groupby("Ticker")[columnas_numericas].transform(
        lambda s: s.interpolate(limit_direction="both")
    )
    antes = len(df)
    df = df.dropna(subset=columnas_numericas)
    reporte["filas_eliminadas_por_nulos_no_rellenables"] = antes - len(df)
    reporte["nulos_despues"] = int(df[columnas_numericas].isna().sum().sum())

    # --- Precios no positivos (errores de captura) ---
    antes = len(df)
    df = df[(df["Close"] > 0) & (df["Volume"] >= 0)]
    reporte["precios_no_positivos_eliminados"] = antes - len(df)

    # --- Retornos diarios y deteccion de outliers ---
    df["Retorno"] = df.groupby("Ticker")["Adj_Close"].pct_change()

    atipicos = df["Retorno"].abs() > UMBRAL_RETORNO_ATIPICO
    reporte["retornos_atipicos_detectados"] = int(atipicos.sum())
    # Se documentan pero NO se eliminan solas: podrian ser splits/eventos
    # reales. Se dejan marcados para revision manual.
    df["Retorno_Atipico"] = atipicos

    print("Reporte de limpieza:")
    for k, v in reporte.items():
        print(f"  {k}: {v}")

    return df


# ---------------------------------------------------------------------------
# 3. Guardado: CSV + base de datos "fondo"
# ---------------------------------------------------------------------------


def guardar(df: pd.DataFrame) -> None:
    os.makedirs(os.path.dirname(OUT_PRECIOS), exist_ok=True)

    precios = df[
        ["Ticker", "Date", "Open", "High", "Low", "Close", "Adj_Close", "Volume"]
    ]
    retornos = df.loc[
        df["Retorno"].notna(),
        ["Ticker", "Date", "Retorno", "Retorno_Atipico"],
    ]

    precios.to_csv(OUT_PRECIOS, index=False)
    retornos.to_csv(OUT_RETORNOS, index=False)

    with sqlite3.connect(DB_PATH) as con:
        precios.to_sql("precios", con, if_exists="replace", index=False)
        retornos.to_sql("retornos", con, if_exists="replace", index=False)

    print(f"\nGuardado: {OUT_PRECIOS}, {OUT_RETORNOS} y base de datos {DB_PATH}")
    print(f"Tickers procesados: {sorted(df['Ticker'].unique())}")
    print(f"Rango de fechas: {df['Date'].min().date()} a {df['Date'].max().date()}")
    print(f"Filas finales: {len(precios)}")


if __name__ == "__main__":
    if not ARCHIVOS:
        raise SystemExit(
            f"No se encontraron CSV en {RAW_DATA_DIR}/. "
            "Coloca ahi tus 10 archivos o edita ARCHIVOS en este script."
        )
    crudo = cargar_crudos(ARCHIVOS)
    limpio = limpiar(crudo)
    guardar(limpio)
