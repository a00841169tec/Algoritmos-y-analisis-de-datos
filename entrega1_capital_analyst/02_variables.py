"""
Entrega 1 - Punto 2: Identificacion de Variables Dependientes e Independientes

Lee la tabla "precios" de fondo.db (generada en el Punto 1) y calcula:
  - Variable dependiente: Daily_Return (retorno diario por accion)
  - Variables independientes: Rendimiento_Mercado, Volatilidad_20d,
    Volumen_Log, Momentum_10d

Guarda el resultado en fondo.db (tabla "variables_modelo") y en
variables_modelo.csv. Pensado para pegarse como celda de Colab despues
del Punto 1 (usa la misma fondo.db).
"""

import sqlite3

import numpy as np
import pandas as pd

DB_NAME = "fondo.db"

# ---------------------------------------------------------------------------
# 1. Cargar los datos limpios del Punto 1
# ---------------------------------------------------------------------------
conn = sqlite3.connect(DB_NAME)
df = pd.read_sql("SELECT * FROM precios", conn, parse_dates=["Date"])
conn.close()

df = df.sort_values(["Ticker", "Date"]).reset_index(drop=True)

# ---------------------------------------------------------------------------
# 2. Variable dependiente (Y): Daily_Return (ya viene del Punto 1)
# ---------------------------------------------------------------------------
# Si por alguna razon no existe, se recalcula aqui:
if "Daily_Return" not in df.columns:
    df["Daily_Return"] = df.groupby("Ticker")["Price"].pct_change() * 100

# ---------------------------------------------------------------------------
# 3. Variables independientes (X)
# ---------------------------------------------------------------------------

# 3.1 Rendimiento_Mercado: proxy de "mercado" = promedio diario de los
#     retornos de las 10 acciones (teoria: CAPM, factor de riesgo sistematico)
mercado = df.groupby("Date")["Daily_Return"].mean().rename("Rendimiento_Mercado")
df = df.merge(mercado, on="Date", how="left")

# 3.2 Volatilidad_20d: desviacion estandar movil de 20 dias del retorno,
#     por accion (teoria: la varianza/volatilidad como medida de riesgo)
df["Volatilidad_20d"] = df.groupby("Ticker")["Daily_Return"].transform(
    lambda s: s.rolling(window=20, min_periods=10).std()
)

# 3.3 Volumen_Log: logaritmo del volumen (teoria: liquidez de mercado,
#     el volumen aproxima el flujo de informacion)
df["Volumen_Log"] = np.log1p(df["Vol."])

# 3.4 Momentum_10d: retorno promedio movil de 10 dias, por accion
#     (teoria: anomalias de mercado / efecto momentum)
df["Momentum_10d"] = df.groupby("Ticker")["Daily_Return"].transform(
    lambda s: s.rolling(window=10, min_periods=5).mean()
)

print("Vista previa de las variables calculadas:")
print(
    df[
        [
            "Ticker",
            "Date",
            "Daily_Return",
            "Rendimiento_Mercado",
            "Volatilidad_20d",
            "Volumen_Log",
            "Momentum_10d",
        ]
    ].tail(10)
)

# ---------------------------------------------------------------------------
# 4. Tabla resumen para la parte escrita (variable, tipo, justificacion)
# ---------------------------------------------------------------------------
resumen = pd.DataFrame(
    [
        {
            "Variable": "Daily_Return",
            "Tipo": "Dependiente (Y)",
            "Justificacion": (
                "Retorno diario de cada accion: es lo que Capital Analyst "
                "quiere explicar/predecir para tomar decisiones de inversion."
            ),
        },
        {
            "Variable": "Rendimiento_Mercado",
            "Tipo": "Independiente (X1)",
            "Justificacion": (
                "Proxy del retorno de mercado (promedio de las 10 acciones). "
                "Base: CAPM - el retorno de un activo depende de su "
                "sensibilidad (beta) al riesgo sistematico del mercado."
            ),
        },
        {
            "Variable": "Volatilidad_20d",
            "Tipo": "Independiente (X2)",
            "Justificacion": (
                "Volatilidad movil de 20 dias por accion. Base: la varianza "
                "de los retornos como medida estandar de riesgo "
                "(Markowitz, modelos tipo GARCH)."
            ),
        },
        {
            "Variable": "Volumen_Log",
            "Tipo": "Independiente (X3)",
            "Justificacion": (
                "Logaritmo del volumen operado. Base: teoria de liquidez de "
                "mercado - el volumen refleja informacion y facilidad de "
                "entrada/salida de una posicion."
            ),
        },
        {
            "Variable": "Momentum_10d",
            "Tipo": "Independiente (X4)",
            "Justificacion": (
                "Retorno promedio de los ultimos 10 dias por accion. Base: "
                "anomalias de mercado / efecto momentum, mencionado "
                "explicitamente en la estrategia de Capital Analyst."
            ),
        },
    ]
)

print("\nResumen de variables (para la parte escrita):")
print(resumen.to_string(index=False))

# ---------------------------------------------------------------------------
# 5. Guardado en fondo.db y CSV de respaldo
# ---------------------------------------------------------------------------
conn = sqlite3.connect(DB_NAME)
df.to_sql("variables_modelo", conn, if_exists="replace", index=False)
conn.close()

df.to_csv("variables_modelo.csv", index=False)
print(
    f"\nGuardado en {DB_NAME} (tabla 'variables_modelo') y en "
    "variables_modelo.csv"
)
