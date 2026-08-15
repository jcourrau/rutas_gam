"""Carga y preparación de los datos de la red y las paradas."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import numpy as np
import osmnx as ox
import pandas as pd


# Valores aproximados basados en el artículo 98 de la Ley de Tránsito.
VELOCIDADES_POR_VIA = {
    "motorway": 80,
    "motorway_link": 60,
    "trunk": 70,
    "trunk_link": 50,
    "primary": 60,
    "primary_link": 45,
    "secondary": 50,
    "secondary_link": 40,
    "tertiary": 40,
    "tertiary_link": 35,
    "residential": 30,
    "living_street": 20,
    "service": 20,
    "unclassified": 40,
    "road": 30,
}

# Dispersión lognormal por clase vial usada desde el Avance 1.
SIGMA_POR_VIA = {
    "motorway": 0.10,
    "trunk": 0.12,
    "primary": 0.18,
    "secondary": 0.20,
    "tertiary": 0.22,
    "residential": 0.16,
    "service": 0.14,
}

NOMBRES_VISUALES = {
    "nombre": "Nombre",
    "distrito": "Distrito",
    "sector": "Sector",
    "densidad_poblacional": "Densidad poblacional",
    "destinos_estrategicos": "Destinos estratégicos",
    "w_i": "Índice de importancia",
    "distancia_optima_km": "Distancia óptima (km)",
    "tiempo_optimo_min": "Tiempo óptimo (min)",
    "tiempo_base_min": "Tiempo base (min)",
    "RT_pct": "RT %",
    "RV_pct": "RV %",
    "IC_pct": "IC %",
    "NE": "NE",
    "par": "Par",
    "modelo": "Modelo",
    "distancia_km": "Distancia (km)",
    "tiempo_determinista_min": "Tiempo determinista (min)",
    "costo_objetivo": "Costo objetivo (min)",
    "costo_astar": "Costo A* (min)",
    "costo_dijkstra": "Costo Dijkstra (min)",
    "coincide": "Coincide",
    "NE_astar": "NE A*",
    "media_simulada_min": "Media simulada (min)",
    "desviacion_simulada_min": "Desviación simulada (min)",
    "percentil_90_min": "Percentil 90 (min)",
    "ruta_cambio": "Ruta diferente",
    "costo_dijkstra_min": "Costo Dijkstra (min)",
    "NE_dijkstra": "NE Dijkstra",
    "ejecucion_astar_ms": "Ejecución A* (ms)",
    "ejecucion_dijkstra_ms": "Ejecución Dijkstra (ms)",
    "punto_base": "Punto base",
    "lambda_riesgo": "Lambda",
    "distancia_promedio_km": "Distancia promedio (km)",
    "tiempo_promedio_min": "Tiempo promedio (min)",
    "costo_objetivo_promedio_min": "Costo objetivo promedio (min)",
    "penalizacion_promedio_min": "Penalización promedio (min)",
    "rutas_diferentes": "Rutas diferentes",
    "rutas_diferentes_pct": "Rutas diferentes (%)",
    "coincide_algoritmos": "A* y Dijkstra coinciden",
}


def primer_valor(valor):
    """Obtiene un valor escalar de los atributos almacenados por OSM."""
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return None
    if isinstance(valor, str) and valor.startswith("["):
        try:
            valor = ast.literal_eval(valor)
        except (ValueError, SyntaxError):
            pass
    if isinstance(valor, (list, tuple, set)):
        return next(iter(valor), None)
    return valor


def normalizar_velocidad(valor):
    """Convierte un límite de velocidad de OSM a kilómetros por hora."""
    valor = primer_valor(valor)
    if valor is None:
        return None
    texto = str(valor).lower().strip()
    numero = re.search(r"(\d+(?:\.\d+)?)", texto)
    if not numero:
        return None
    velocidad = float(numero.group(1))
    if "mph" in texto:
        velocidad *= 1.609344
    return velocidad


def velocidad_por_tipo(tipo_via):
    """Devuelve la velocidad imputada para una clase vial de OSM."""
    tipo = str(primer_valor(tipo_via) or "unclassified")
    return float(VELOCIDADES_POR_VIA.get(tipo, 30))


def sigma_por_tipo(tipo_via):
    """Devuelve la dispersión lognormal supuesta para una clase vial."""
    tipo = str(primer_valor(tipo_via) or "residential")
    return float(SIGMA_POR_VIA.get(tipo, 0.18))


def cargar_grafo(ruta):
    """Carga una extracción GraphML de la red vial."""
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró la red vial: {ruta}")
    return ox.load_graphml(ruta)


def agregar_tiempos(grafo, escala_imputada=1.0):
    """Agrega velocidad y tiempo estimado a todos los arcos.

    Args:
        grafo: Red vial dirigida cargada desde GraphML.
        escala_imputada: Factor aplicado únicamente a las velocidades que no
            estaban registradas en OSM. Se usa para sensibilidad.

    Returns:
        Copia del grafo con velocidad, fuente y tiempo de flujo libre.
    """
    if escala_imputada <= 0:
        raise ValueError("escala_imputada debe ser positiva.")

    preparado = grafo.copy()
    for _, _, _, datos in preparado.edges(keys=True, data=True):
        velocidad_osm = normalizar_velocidad(datos.get("maxspeed"))
        if velocidad_osm:
            velocidad = velocidad_osm
            fuente = "OSM"
        else:
            velocidad = velocidad_por_tipo(datos.get("highway")) * escala_imputada
            fuente = "Imputada"
        datos["speed_kph"] = velocidad
        datos["speed_source"] = fuente
        datos["travel_time_min"] = float(datos["length"]) / velocidad * 0.06
    return preparado


def agregar_costo_ajustado(grafo, lambda_riesgo=1.0):
    """Agrega el costo de tiempo más penalización por variabilidad.

    La desviación de cada arco se deriva de la distribución lognormal usada
    en el Avance 1: ``s_ij = t_ij * sqrt(exp(sigma_via**2) - 1)``.

    Args:
        grafo: Grafo que ya contiene ``travel_time_min``.
        lambda_riesgo: Importancia no negativa asignada a la variabilidad.

    Returns:
        Copia con ``risk_adjusted_time_min`` y ``arc_std_min``.
    """
    if lambda_riesgo < 0:
        raise ValueError("lambda_riesgo no puede ser negativo.")

    preparado = grafo.copy()
    for _, _, _, datos in preparado.edges(keys=True, data=True):
        tiempo = float(datos["travel_time_min"])
        sigma = sigma_por_tipo(datos.get("highway"))
        desviacion = tiempo * np.sqrt(np.exp(sigma**2) - 1)
        datos["arc_std_min"] = desviacion
        datos["risk_adjusted_time_min"] = (
            tiempo + lambda_riesgo * desviacion
        )
    return preparado


def cargar_paradas(ruta):
    """Carga una tabla fija de paradas o puntos de estudio."""
    return pd.read_csv(ruta)


def calcular_importancia(paradas, alfa=0.6, beta=0.4):
    """Calcula y ordena el índice de importancia de cada parada."""
    resultado = paradas.copy()
    if "w_i_preliminar" in resultado.columns:
        resultado["w_i"] = resultado["w_i_preliminar"]
        return resultado.sort_values("w_i", ascending=False).reset_index(drop=True)
    for columna, nueva in (
        ("densidad_poblacional", "densidad_normalizada"),
        ("destinos_estrategicos", "destinos_normalizados"),
    ):
        minimo = resultado[columna].min()
        rango = resultado[columna].max() - minimo
        resultado[nueva] = (
            0.0 if rango == 0 else (resultado[columna] - minimo) / rango
        )
    resultado["w_i"] = (
        alfa * resultado["densidad_normalizada"]
        + beta * resultado["destinos_normalizados"]
    )
    return resultado.sort_values("w_i", ascending=False).reset_index(drop=True)


def preparar_paradas(grafo, paradas):
    """Conecta cada parada con el nodo vial más cercano."""
    resultado = paradas.copy()
    resultado["node_id"] = ox.distance.nearest_nodes(
        grafo,
        resultado["longitud"].to_numpy(),
        resultado["latitud"].to_numpy(),
    )
    return resultado


def usar_nombres_visuales(tabla):
    """Cambia nombres internos por etiquetas adecuadas para presentación."""
    return tabla.rename(columns=NOMBRES_VISUALES)
