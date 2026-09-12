# Punto 5: Visualizacion inicial (acciones y portafolio)
# Usa pd y sqlite3 ya importados en la celda 2 del notebook.
import matplotlib.pyplot as plt
import numpy as np

conn = sqlite3.connect("fondo.db")
df = pd.read_sql("SELECT * FROM variables_modelo", conn, parse_dates=["Date"])
conn.close()

tickers = sorted(df["Ticker"].unique())
colores = plt.get_cmap("tab10").colors

# 1. Evolucion de precios normalizada (base 100) - por accion
fig, ax = plt.subplots(figsize=(10, 5))
for i, t in enumerate(tickers):
    serie = df[df["Ticker"] == t].sort_values("Date")
    precio_norm = serie["Price"] / serie["Price"].iloc[0] * 100
    ax.plot(serie["Date"], precio_norm, label=t, color=colores[i % 10], linewidth=1.5)
ax.set_title("Evolucion de precios (base 100)")
ax.legend(fontsize=7, ncol=2)
plt.tight_layout()
plt.savefig("01_precios.png", dpi=150)
plt.show()

# 2. Distribucion de retornos diarios - por accion (small multiples)
fig, axes = plt.subplots(2, 5, figsize=(15, 5), sharex=True)
for ax, t in zip(axes.flat, tickers):
    serie = df[df["Ticker"] == t]["Daily_Return"].dropna()
    ax.hist(serie, bins=30, color="steelblue")
    ax.set_title(t, fontsize=9)
fig.suptitle("Distribucion de retornos diarios por accion")
plt.tight_layout()
plt.savefig("02_distribucion_retornos.png", dpi=150)
plt.show()

# 3. Retorno acumulado del portafolio (equal-weighted, via Rendimiento_Mercado)
portafolio = df.drop_duplicates("Date").sort_values("Date")[["Date", "Rendimiento_Mercado"]]
portafolio["Retorno_Acumulado"] = (1 + portafolio["Rendimiento_Mercado"] / 100).cumprod()

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(portafolio["Date"], portafolio["Retorno_Acumulado"], color=colores[0], linewidth=2)
ax.set_title("Retorno acumulado del portafolio (10 acciones, ponderacion igual)")
plt.tight_layout()
plt.savefig("03_portafolio_acumulado.png", dpi=150)
plt.show()

# 4. Riesgo vs retorno por accion (anualizado)
resumen = df.groupby("Ticker")["Daily_Return"].agg(["mean", "std"]).reset_index()
resumen["Retorno_Anual"] = resumen["mean"] * 252
resumen["Volatilidad_Anual"] = resumen["std"] * np.sqrt(252)

fig, ax = plt.subplots(figsize=(7, 6))
ax.scatter(resumen["Volatilidad_Anual"], resumen["Retorno_Anual"], color=colores[3], s=60)
for _, row in resumen.iterrows():
    ax.annotate(row["Ticker"], (row["Volatilidad_Anual"], row["Retorno_Anual"]), fontsize=8)
ax.set_xlabel("Volatilidad anualizada (%)")
ax.set_ylabel("Retorno anualizado (%)")
ax.set_title("Riesgo vs. retorno por accion")
plt.tight_layout()
plt.savefig("04_riesgo_retorno.png", dpi=150)
plt.show()

print("Graficos guardados: 01_precios.png, 02_distribucion_retornos.png,",
      "03_portafolio_acumulado.png, 04_riesgo_retorno.png")
