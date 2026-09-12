# Punto 4: Perfil de riesgo del cliente
# Usa pd y sqlite3 ya importados en la celda 2 del notebook.

# Cliente hipotetico (cuestionario simple, 1-5 c/u)
cliente = {
    "Horizonte de inversion (largo=5)": 4,
    "Tolerancia a perdidas (alta=5)": 3,
    "Estabilidad de ingresos (alta=5)": 4,
    "Conocimiento financiero (alto=5)": 3,
    "Objetivo (crecimiento=5, preservar=1)": 4,
}

puntaje = sum(cliente.values()) / len(cliente)

if puntaje < 2.5:
    perfil = "Conservador"
elif puntaje < 3.8:
    perfil = "Moderado"
else:
    perfil = "Agresivo"

print(f"Puntaje promedio: {puntaje:.2f} -> Perfil: {perfil}")

# Adaptar el portafolio segun el perfil, usando la volatilidad ya calculada
conn = sqlite3.connect("fondo.db")
vol = pd.read_sql("SELECT Ticker, Volatilidad_20d FROM variables_modelo", conn)
conn.close()

vol_prom = vol.groupby("Ticker")["Volatilidad_20d"].mean().sort_values()

if perfil == "Conservador":
    seleccion = vol_prom.head(5)
elif perfil == "Agresivo":
    seleccion = vol_prom.tail(5)
else:
    seleccion = vol_prom  # las 10, sin filtrar

print(f"\nAcciones sugeridas para perfil {perfil} (por volatilidad):")
print(seleccion)
