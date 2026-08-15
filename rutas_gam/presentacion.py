"""Tablas compactas utilizadas para presentar resultados en los notebooks."""

from __future__ import annotations

import pandas as pd

from .datos import usar_nombres_visuales


def _seleccionar(tabla, columnas):
    """Aplica nombres visuales, selecciona columnas y redondea valores."""
    return usar_nombres_visuales(tabla)[columnas].round(2)


def tabla_puntos_visual(tabla):
    """Prepara la tabla de puntos de estudio."""
    return _seleccionar(tabla, ["Nombre", "Sector"])


def tabla_casos_estudio(casos):
    """Convierte los casos preparados en una tabla para inspección."""
    return pd.DataFrame(casos)


def tabla_modelo_visual(tabla):
    """Prepara los resultados deterministas de un modelo."""
    return _seleccionar(tabla, [
        "Par",
        "Modelo",
        "Distancia (km)",
        "Tiempo determinista (min)",
        "Costo objetivo (min)",
        "Costo A* (min)",
        "Costo Dijkstra (min)",
        "Coincide",
        "NE A*",
        "NE Dijkstra",
    ])


def tabla_lambda_visual(tabla):
    """Prepara la comparación determinista de valores de lambda."""
    return _seleccionar(tabla, [
        "Lambda",
        "Distancia promedio (km)",
        "Tiempo promedio (min)",
        "Costo objetivo promedio (min)",
        "Penalización promedio (min)",
        "Rutas diferentes",
        "Rutas diferentes (%)",
    ])


def tabla_simulacion_visual(tabla):
    """Prepara las métricas Monte Carlo de cada recorrido."""
    return _seleccionar(tabla, [
        "Par",
        "Modelo",
        "Tiempo determinista (min)",
        "Media simulada (min)",
        "Desviación simulada (min)",
        "Percentil 90 (min)",
        "IC %",
    ])


def tabla_referencia_visual(tabla):
    """Prepara las métricas frente a la ruta base."""
    return _seleccionar(tabla, [
        "Par",
        "Tiempo óptimo (min)",
        "Tiempo base (min)",
        "RT %",
        "RV %",
        "IC %",
        "NE",
        "NE Dijkstra",
    ])


def tabla_comparacion_visual(tabla):
    """Prepara la comparación final de los modelos."""
    return _seleccionar(tabla, [
        "Par",
        "Modelo",
        "Tiempo determinista (min)",
        "Media simulada (min)",
        "Desviación simulada (min)",
        "Percentil 90 (min)",
        "IC %",
        "Ruta diferente",
    ])


def tabla_validacion_original(tabla):
    """Prepara el detalle comparable de los tres pares originales."""
    originales = tabla[tabla["muestra"] == "Original"]
    return _seleccionar(originales, [
        "Par",
        "Modelo",
        "Tiempo determinista (min)",
        "Media simulada (min)",
        "Percentil 90 (min)",
        "Ruta diferente",
    ])


def tabla_validacion_adicional(tabla):
    """Prepara la comparación agregada de los pares adicionales."""
    columnas = {
        "modelo": "Modelo",
        "pares": "Pares",
        "rutas_diferentes": "Rutas diferentes",
        "tiempo_determinista_promedio_min": (
            "Tiempo determinista promedio (min)"
        ),
        "media_simulada_promedio_min": "Media simulada promedio (min)",
        "desviacion_simulada_promedio_min": "Desviación promedio (min)",
        "p90_promedio_min": "Percentil 90 promedio (min)",
        "IC_promedio_pct": "IC promedio (%)",
    }
    adicional = tabla[tabla["muestra"] == "Adicional"].rename(columns=columnas)
    return adicional[list(columnas.values())].round(2)
