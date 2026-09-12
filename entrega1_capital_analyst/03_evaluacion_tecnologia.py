# Punto 3: Evaluacion de tecnologias (Python vs R vs Excel)
# Usa pd ya importado en la celda 2 del notebook.

criterios = pd.DataFrame({
    "Criterio": ["Automatizacion", "Integracion con Interactive Brokers/APIs",
                 "Machine Learning", "Manejo de grandes datos", "Facilidad de uso"],
    "Peso": [0.25, 0.25, 0.25, 0.15, 0.10],
    "Python": [5, 5, 5, 5, 3],
    "R":      [4, 3, 3, 4, 3],
    "Excel":  [1, 1, 1, 2, 5],
})

for col in ["Python", "R", "Excel"]:
    criterios[f"{col}_pond"] = criterios[col] * criterios["Peso"]

print(criterios)

totales = criterios[["Python_pond", "R_pond", "Excel_pond"]].sum()
print("\nPuntaje final (0-5):")
print(totales)

ganador = totales.idxmax().replace("_pond", "")
print(f"\nTecnologia seleccionada: {ganador}")
