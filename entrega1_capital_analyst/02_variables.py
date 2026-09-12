# Punto 2: Variables dependientes e independientes
# Usa pd, np y sqlite3 ya importados en la celda 2 del notebook.

conn = sqlite3.connect("fondo.db")
df = pd.read_sql("SELECT * FROM precios", conn, parse_dates=["Date"])
conn.close()
df = df.sort_values(["Ticker", "Date"]).reset_index(drop=True)

# Y: Daily_Return (ya viene del Punto 1)

# X1: Rendimiento_Mercado - promedio diario de las 10 acciones (CAPM)
mercado = df.groupby("Date")["Daily_Return"].mean().rename("Rendimiento_Mercado")
df = df.merge(mercado, on="Date", how="left")

# X2: Volatilidad_20d - riesgo (desv. estandar movil de 20 dias)
df["Volatilidad_20d"] = df.groupby("Ticker")["Daily_Return"].transform(
    lambda s: s.rolling(20, min_periods=10).std()
)

# X3: Volumen_Log - liquidez (log del volumen)
df["Volumen_Log"] = np.log1p(df["Vol."])

# X4: Momentum_10d - anomalias de mercado (retorno promedio de 10 dias)
df["Momentum_10d"] = df.groupby("Ticker")["Daily_Return"].transform(
    lambda s: s.rolling(10, min_periods=5).mean()
)

print(df[["Ticker", "Date", "Daily_Return", "Rendimiento_Mercado",
          "Volatilidad_20d", "Volumen_Log", "Momentum_10d"]].tail())

resumen = pd.DataFrame([
    ("Daily_Return", "Y", "Retorno diario a explicar/predecir"),
    ("Rendimiento_Mercado", "X1", "CAPM: riesgo sistematico de mercado"),
    ("Volatilidad_20d", "X2", "Varianza como medida de riesgo"),
    ("Volumen_Log", "X3", "Liquidez de mercado"),
    ("Momentum_10d", "X4", "Anomalia de mercado / momentum"),
], columns=["Variable", "Tipo", "Justificacion"])
print(resumen.to_string(index=False))

conn = sqlite3.connect("fondo.db")
df.to_sql("variables_modelo", conn, if_exists="replace", index=False)
conn.close()
df.to_csv("variables_modelo.csv", index=False)
print("Guardado en fondo.db (tabla variables_modelo) y variables_modelo.csv")
