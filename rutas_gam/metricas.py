"""Cálculo de las métricas de éxito del proyecto."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _arco_mas_rapido(grafo, origen, destino):
    return min(
        grafo[origen][destino].values(),
        key=lambda datos: float(datos["travel_time_min"]),
    )


def resumen_ruta(grafo, ruta):
    """Resume la distancia y el tiempo determinista de una ruta."""
    distancia, tiempo = 0.0, 0.0
    for origen, destino in zip(ruta[:-1], ruta[1:]):
        arco = _arco_mas_rapido(grafo, origen, destino)
        distancia += float(arco["length"])
        tiempo += float(arco["travel_time_min"])
    return {"distancia_km": distancia / 1000, "tiempo_min": tiempo}


def simular_tiempos(grafo, ruta, repeticiones=1000, semilla=42):
    """Simula variaciones de tiempo sin cambiar la ruta elegida."""
    generador = np.random.default_rng(semilla)
    totales = np.zeros(repeticiones)
    # Este factor representa una condición general del escenario, por ejemplo lluvia
    # o mayor volumen de tránsito, que afecta todos los tramos de una misma corrida.
    sigma_general = 0.15
    factor_general = generador.lognormal(
        -sigma_general**2 / 2, sigma_general, repeticiones
    )
    variacion_por_via = {
        "motorway": 0.10,
        "trunk": 0.12,
        "primary": 0.18,
        "secondary": 0.20,
        "tertiary": 0.22,
        "residential": 0.16,
        "service": 0.14,
    }
    for origen, destino in zip(ruta[:-1], ruta[1:]):
        arco = _arco_mas_rapido(grafo, origen, destino)
        tipo = str(arco.get("highway", "residential"))
        if tipo.startswith("["):
            tipo = "residential"
        sigma = variacion_por_via.get(tipo, 0.18)
        multiplicador = generador.lognormal(-sigma**2 / 2, sigma, repeticiones)
        totales += float(arco["travel_time_min"]) * multiplicador
    return totales * factor_general


def evaluar_rutas(grafo, ruta_optima, ruta_base, nodos_explorados, semilla=42):
    """Calcula RT, RV, IC y NE para una ruta optimizada."""
    optima = resumen_ruta(grafo, ruta_optima)
    base = resumen_ruta(grafo, ruta_base)
    simulada_optima = simular_tiempos(grafo, ruta_optima, semilla=semilla)
    simulada_base = simular_tiempos(grafo, ruta_base, semilla=semilla)
    reduccion_tiempo = (base["tiempo_min"] - optima["tiempo_min"]) / base["tiempo_min"] * 100
    desviacion_optima = simulada_optima.std(ddof=1)
    desviacion_base = simulada_base.std(ddof=1)
    reduccion_variabilidad = (1 - desviacion_optima / desviacion_base) * 100
    confiabilidad = np.mean(simulada_optima <= 1.15 * simulada_optima.mean()) * 100
    return pd.Series({
        "distancia_optima_km": optima["distancia_km"],
        "tiempo_optimo_min": optima["tiempo_min"],
        "tiempo_base_min": base["tiempo_min"],
        "RT_pct": reduccion_tiempo,
        "RV_pct": reduccion_variabilidad,
        "IC_pct": confiabilidad,
        "NE": nodos_explorados,
    })
