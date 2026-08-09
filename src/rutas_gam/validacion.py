"""Validación, comparación de modelos y análisis de sensibilidad.

Este módulo se agregó para la entrega final. Contiene tres bloques:

1. Validación extendida de A* sobre pares origen-destino adicionales
   (generaliza la verificación de optimalidad más allá de los tres pares
   presentados en el avance).
2. Comparación cuantitativa entre el Modelo 1 (determinista, A*) y el
   Modelo 2 (estocástico, simulación Monte Carlo) sobre las mismas rutas.
3. Análisis de sensibilidad: número de réplicas, dispersión de la condición
   general (sigma) y velocidades imputadas.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .algoritmos import astar_bidireccional, dijkstra
from .datos import agregar_tiempos, recalcular_importancia
from .metricas import _arco_mas_rapido, evaluar_rutas, resumen_ruta, simular_tiempos


def pares_aleatorios_validos(grafo, n, semilla=2026, excluir=None):
    """Muestrea n pares origen-destino con camino dirigido existente."""
    generador = np.random.default_rng(semilla)
    nodos = list(grafo.nodes())
    excluir = set(excluir or [])
    pares = []
    intentos = 0
    limite = n * 40
    while len(pares) < n and intentos < limite:
        intentos += 1
        origen, destino = generador.choice(nodos, size=2, replace=False)
        if (origen, destino) in excluir or origen == destino:
            continue
        try:
            resultado = dijkstra(grafo, origen, destino)
        except ValueError:
            continue
        if resultado["costo"] <= 0:
            continue
        pares.append((origen, destino))
    return pares


def validar_astar_extendido(grafo, pares):
    """Corre A* y Dijkstra sobre pares adicionales y compara sus costos."""
    filas = []
    for origen, destino in pares:
        try:
            resultado_astar = astar_bidireccional(grafo, origen, destino)
            resultado_dijkstra = dijkstra(grafo, origen, destino)
        except ValueError:
            continue
        diferencia = abs(resultado_astar["costo"] - resultado_dijkstra["costo"])
        filas.append({
            "origen": origen,
            "destino": destino,
            "costo_astar_min": resultado_astar["costo"],
            "costo_dijkstra_min": resultado_dijkstra["costo"],
            "diferencia_abs": diferencia,
            "coincide": diferencia < 1e-6,
            "NE_astar": resultado_astar["nodos_explorados"],
            "NE_dijkstra": resultado_dijkstra["nodos_explorados"],
            "reduccion_NE_pct": (
                (resultado_dijkstra["nodos_explorados"] - resultado_astar["nodos_explorados"])
                / resultado_dijkstra["nodos_explorados"] * 100
            ),
            "ms_astar": resultado_astar["milisegundos"],
            "ms_dijkstra": resultado_dijkstra["milisegundos"],
        })
    return pd.DataFrame(filas)


def validar_estabilidad_monte_carlo(grafo, comparaciones, n_folds=5, repeticiones=1000):
    """Repite la simulación en 'folds' con semillas distintas por par y ruta.

    Es el equivalente, para un modelo de simulación, de correr varias
    particiones de validación: si RT/RV/IC cambian poco entre folds, el
    resultado es estable ante la semilla aleatoria.
    """
    filas = []
    for comparacion in comparaciones:
        for fold in range(n_folds):
            semilla = 1000 * (fold + 1) + comparacion.get("semilla", 42)
            metricas = evaluar_rutas(
                grafo,
                comparacion["ruta_optima"],
                comparacion["ruta_base"],
                nodos_explorados=comparacion.get("nodos_explorados", np.nan),
                semilla=semilla,
            )
            filas.append({
                "par": comparacion["nombre"],
                "fold": fold + 1,
                "semilla": semilla,
                "RT_pct": metricas["RT_pct"],
                "RV_pct": metricas["RV_pct"],
                "IC_pct": metricas["IC_pct"],
            })
    tabla = pd.DataFrame(filas)
    resumen = tabla.groupby("par")[["RT_pct", "RV_pct", "IC_pct"]].agg(["mean", "std"])
    resumen.columns = ["_".join(columna) for columna in resumen.columns]
    coeficiente_variacion = (resumen["RV_pct_std"].abs() / resumen["RV_pct_mean"].abs() * 100)
    resumen["CV_RV_pct"] = coeficiente_variacion
    return tabla, resumen.reset_index()


def comparar_modelo1_modelo2(grafo, comparaciones, repeticiones=1000):
    """Compara el modelo determinista (Modelo 1) contra el estocástico (Modelo 2).

    Para cada par usa la MISMA ruta óptima (mismos datos de prueba) y calcula:
    - sesgo: diferencia entre el tiempo promedio simulado y el tiempo determinista
    - error_relativo_pct: sesgo como porcentaje del tiempo determinista
    - ic90_ancho_min: ancho del intervalo 5%-95% de la distribución simulada
    - cobertura_subestimacion_pct: % de escenarios en los que el Modelo 1
      subestima el tiempo que arroja el Modelo 2
    """
    filas = []
    for comparacion in comparaciones:
        semilla = comparacion.get("semilla", 42)
        ruta = comparacion["ruta_optima"]
        determinista = resumen_ruta(grafo, ruta)["tiempo_min"]
        simulado = simular_tiempos(grafo, ruta, repeticiones=repeticiones, semilla=semilla)
        sesgo = simulado.mean() - determinista
        filas.append({
            "par": comparacion["nombre"],
            "modelo1_tiempo_determinista_min": determinista,
            "modelo2_tiempo_medio_simulado_min": simulado.mean(),
            "modelo2_desviacion_min": simulado.std(ddof=1),
            "sesgo_min": sesgo,
            "error_relativo_pct": sesgo / determinista * 100,
            "ic90_ancho_min": np.percentile(simulado, 95) - np.percentile(simulado, 5),
            "cobertura_subestimacion_pct": float(np.mean(simulado > determinista) * 100),
        })
    return pd.DataFrame(filas)


def sensibilidad_replicas(grafo, comparaciones, valores=(200, 1000, 5000), semilla_base=42):
    """Sensibilidad del Modelo 2 al número de réplicas de Monte Carlo."""
    filas = []
    for comparacion in comparaciones:
        for repeticiones in valores:
            metricas = evaluar_rutas(
                grafo,
                comparacion["ruta_optima"],
                comparacion["ruta_base"],
                nodos_explorados=comparacion.get("nodos_explorados", np.nan),
                semilla=comparacion.get("semilla", semilla_base),
            )
            # evaluar_rutas usa 1000 réplicas fijas internamente para RV/IC;
            # aquí recalculamos con el número de réplicas variable.
            simulada_optima = simular_tiempos(
                grafo, comparacion["ruta_optima"], repeticiones=repeticiones,
                semilla=comparacion.get("semilla", semilla_base),
            )
            simulada_base = simular_tiempos(
                grafo, comparacion["ruta_base"], repeticiones=repeticiones,
                semilla=comparacion.get("semilla", semilla_base),
            )
            desviacion_optima = simulada_optima.std(ddof=1)
            desviacion_base = simulada_base.std(ddof=1)
            filas.append({
                "par": comparacion["nombre"],
                "repeticiones": repeticiones,
                "media_optima_min": simulada_optima.mean(),
                "RV_pct": (1 - desviacion_optima / desviacion_base) * 100,
                "IC_pct": float(np.mean(simulada_optima <= 1.15 * simulada_optima.mean()) * 100),
            })
    return pd.DataFrame(filas)


def sensibilidad_sigma_general(grafo, comparaciones, valores=(0.05, 0.15, 0.30), semilla_base=42):
    """Sensibilidad ante la dispersión de la condición general del escenario."""
    filas = []
    for comparacion in comparaciones:
        for sigma in valores:
            generador = np.random.default_rng(comparacion.get("semilla", semilla_base))

            def _simular(ruta, sigma=sigma, generador=generador):
                totales = np.zeros(1000)
                factor_general = generador.lognormal(-sigma**2 / 2, sigma, 1000)
                variacion_por_via = {
                    "motorway": 0.10, "trunk": 0.12, "primary": 0.18, "secondary": 0.20,
                    "tertiary": 0.22, "residential": 0.16, "service": 0.14,
                }
                for origen, destino in zip(ruta[:-1], ruta[1:]):
                    arco = _arco_mas_rapido(grafo, origen, destino)
                    tipo = str(arco.get("highway", "residential"))
                    if tipo.startswith("["):
                        tipo = "residential"
                    sigma_via = variacion_por_via.get(tipo, 0.18)
                    multiplicador = generador.lognormal(-sigma_via**2 / 2, sigma_via, 1000)
                    totales += float(arco["travel_time_min"]) * multiplicador
                return totales * factor_general

            simulada_optima = _simular(comparacion["ruta_optima"])
            simulada_base = _simular(comparacion["ruta_base"])
            filas.append({
                "par": comparacion["nombre"],
                "sigma_general": sigma,
                "desviacion_optima_min": simulada_optima.std(ddof=1),
                "RV_pct": (1 - simulada_optima.std(ddof=1) / simulada_base.std(ddof=1)) * 100,
                "IC_pct": float(np.mean(simulada_optima <= 1.15 * simulada_optima.mean()) * 100),
            })
    return pd.DataFrame(filas)


def sensibilidad_velocidades_imputadas(grafo_crudo, comparaciones, factores=(0.85, 1.0, 1.15)):
    """Sensibilidad del tiempo de ruta ante el supuesto de velocidad imputada.

    Mantiene fija la topología de cada ruta (calculada con el supuesto base)
    y recalcula su tiempo determinista bajo velocidades imputadas escaladas,
    para aislar el efecto de ese supuesto sobre la conclusión (RT_pct).
    """
    filas = []
    for factor in factores:
        grafo_escalado = agregar_tiempos(grafo_crudo, escala_imputada=factor)
        for comparacion in comparaciones:
            optima = resumen_ruta(grafo_escalado, comparacion["ruta_optima"])
            base = resumen_ruta(grafo_escalado, comparacion["ruta_base"])
            filas.append({
                "par": comparacion["nombre"],
                "factor_velocidad_imputada": factor,
                "tiempo_optimo_min": optima["tiempo_min"],
                "tiempo_base_min": base["tiempo_min"],
                "RT_pct": (base["tiempo_min"] - optima["tiempo_min"]) / base["tiempo_min"] * 100,
            })
    return pd.DataFrame(filas)


def sensibilidad_pesos_importancia(paradas, combinaciones=((0.6, 0.4), (0.5, 0.5), (0.8, 0.2))):
    """Sensibilidad del top-20 de paradas ante los pesos alfa/beta de w_i."""
    referencia = None
    filas = []
    for alfa, beta in combinaciones:
        recalculada = recalcular_importancia(paradas, alfa=alfa, beta=beta)
        top20 = set(recalculada.head(20)["nombre"])
        if referencia is None:
            referencia = top20
        superposicion = len(top20 & referencia) / len(referencia) * 100
        filas.append({
            "alfa": alfa,
            "beta": beta,
            "top20_paradas": sorted(top20),
            "superposicion_pct_vs_base": superposicion,
        })
    return pd.DataFrame(filas)
