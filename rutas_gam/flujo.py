"""Operaciones de alto nivel utilizadas por los notebooks del proyecto."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

import pandas as pd

from .algoritmos import ruta_por_puntos
from .datos import (
    agregar_costo_ajustado,
    agregar_tiempos,
    calcular_importancia,
    cargar_grafo,
    cargar_paradas,
    preparar_paradas,
)
from .metricas import ResultadoMonteCarlo, evaluar_rutas_monte_carlo
from .modelos import (
    ModeloRuta,
    ResultadoModelo,
    comparar_resultados_modelos,
    ejecutar_modelo,
)


@dataclass(frozen=True)
class DatosEstudio:
    """Agrupa la red y los puntos preparados para el análisis."""

    grafo_crudo: object
    grafo: object
    paradas: pd.DataFrame
    puntos_estudio: pd.DataFrame


@dataclass(frozen=True)
class EjecucionAjustada:
    """Contiene el grafo ajustado y el resultado del Modelo 2."""

    grafo: object
    resultado: ResultadoModelo


@dataclass(frozen=True)
class ComparacionSimulada:
    """Reúne selección determinista y evaluación Monte Carlo."""

    tabla_determinista: pd.DataFrame
    rutas: list
    evaluacion: ResultadoMonteCarlo


@dataclass(frozen=True)
class ReferenciasSimuladas:
    """Reúne las rutas base y sus escenarios junto con los modelos."""

    rutas: list
    evaluacion: ResultadoMonteCarlo
    escenarios: pd.DataFrame


def cargar_datos_estudio(ruta_grafo, ruta_paradas, ruta_puntos):
    """Carga y prepara la red, las paradas y los puntos de estudio.

    Args:
        ruta_grafo: Archivo GraphML de la red vial.
        ruta_paradas: CSV con las paradas importantes.
        ruta_puntos: CSV con los extremos de los casos de estudio.

    Returns:
        DatosEstudio con la red cruda, la red con tiempos y ambos conjuntos de
        puntos conectados a sus nodos viales más cercanos.
    """
    grafo_crudo = cargar_grafo(ruta_grafo)
    grafo = agregar_tiempos(grafo_crudo)
    paradas = cargar_paradas(ruta_paradas)
    paradas = preparar_paradas(grafo, calcular_importancia(paradas))
    puntos_estudio = preparar_paradas(grafo, cargar_paradas(ruta_puntos))
    return DatosEstudio(grafo_crudo, grafo, paradas, puntos_estudio)


def buscar_parada(puntos, fragmento):
    """Localiza la primera parada cuyo nombre contiene un fragmento."""
    coincidencias = puntos[
        puntos["nombre"].str.contains(fragmento, case=False, na=False)
    ]
    if coincidencias.empty:
        raise ValueError(f"No se encontró una parada que contenga: {fragmento}")
    return coincidencias.iloc[0]


def preparar_casos_estudio(paradas, puntos_estudio, configuraciones):
    """Convierte configuraciones nominales en casos reproducibles.

    Args:
        paradas: Paradas importantes conectadas a la red.
        puntos_estudio: Extremos de los casos conectados a la red.
        configuraciones: Tuplas con nombre, origen, destino e intermedio.

    Returns:
        Tupla con la lista de casos y un diccionario de puntos intermedios.
    """
    puntos_busqueda = pd.concat([paradas, puntos_estudio], ignore_index=True)
    casos = []
    intermedios = {}
    for nombre, texto_origen, texto_destino, texto_intermedio in configuraciones:
        origen = buscar_parada(puntos_busqueda, texto_origen)
        destino = buscar_parada(puntos_busqueda, texto_destino)
        intermedio = buscar_parada(puntos_busqueda, texto_intermedio)
        casos.append({
            "nombre": nombre,
            "origen": origen.node_id,
            "destino": destino.node_id,
        })
        intermedios[nombre] = intermedio
    return casos, intermedios


def _validar_resultado(resultado):
    """Exige que A* y Dijkstra coincidan en todos los casos."""
    if not resultado.tabla["coincide"].all():
        raise AssertionError("A* y Dijkstra deben coincidir.")


def ejecutar_modelo_menor_tiempo(grafo, casos):
    """Ejecuta y verifica el modelo que minimiza tiempo de flujo libre."""
    resultado = ejecutar_modelo(
        grafo,
        casos,
        ModeloRuta(nombre="Menor tiempo", peso="travel_time_min"),
    )
    _validar_resultado(resultado)
    return resultado


def ejecutar_modelo_ajustado(grafo, casos, lambda_riesgo):
    """Prepara, ejecuta y verifica el modelo ajustado por variabilidad."""
    grafo_ajustado = agregar_costo_ajustado(
        grafo,
        lambda_riesgo=lambda_riesgo,
    )
    resultado = ejecutar_modelo(
        grafo_ajustado,
        casos,
        ModeloRuta(
            nombre="Ajustada por variabilidad",
            peso="risk_adjusted_time_min",
        ),
    )
    _validar_resultado(resultado)
    return EjecucionAjustada(grafo=grafo_ajustado, resultado=resultado)


def comparar_y_simular_modelos(
    grafo,
    resultados: Sequence[ResultadoModelo],
    repeticiones=1000,
    semilla=2026,
):
    """Combina modelos fijos y los evalúa bajo escenarios Monte Carlo."""
    tabla, rutas = comparar_resultados_modelos(resultados)
    if not tabla["coincide"].all():
        raise AssertionError("A* y Dijkstra deben coincidir.")
    evaluacion = evaluar_rutas_monte_carlo(
        grafo,
        rutas,
        repeticiones=repeticiones,
        semilla=semilla,
    )
    return ComparacionSimulada(tabla, rutas, evaluacion)


def construir_y_simular_rutas_base(
    grafo,
    grafo_simulacion,
    casos,
    intermedios,
    escenarios_modelos,
    repeticiones=1000,
    semilla=2026,
):
    """Construye las rutas base y reúne todos los escenarios simulados."""
    rutas = []
    for caso in casos:
        intermedio = intermedios[caso["nombre"]]
        ruta_base = ruta_por_puntos(
            grafo,
            [caso["origen"], intermedio.node_id, caso["destino"]],
            peso="length",
        )
        rutas.append({
            "nombre": caso["nombre"],
            "origen": caso["origen"],
            "destino": caso["destino"],
            "modelos": {},
            "ruta_base": ruta_base,
        })

    evaluacion = evaluar_rutas_monte_carlo(
        grafo_simulacion,
        rutas,
        repeticiones=repeticiones,
        semilla=semilla,
    )
    escenarios = pd.concat(
        [escenarios_modelos, evaluacion.escenarios],
        ignore_index=True,
    )
    return ReferenciasSimuladas(rutas, evaluacion, escenarios)


def resumir_resultados_referencia(
    casos,
    intermedios,
    tabla_modelo,
    tabla_simulacion,
    tabla_rutas_base,
    nombre_modelo,
):
    """Calcula RT, RV, IC y métricas algorítmicas para cada caso."""
    filas = []
    for caso in casos:
        nombre = caso["nombre"]
        fila_tiempo = tabla_modelo[tabla_modelo["par"] == nombre].iloc[0]
        fila_simulada = tabla_simulacion[
            (tabla_simulacion["par"] == nombre)
            & (tabla_simulacion["modelo"] == nombre_modelo)
        ].iloc[0]
        fila_base = tabla_rutas_base[
            (tabla_rutas_base["par"] == nombre)
            & (tabla_rutas_base["modelo"] == "Ruta base")
        ].iloc[0]
        filas.append({
            "par": nombre,
            "distancia_optima_km": fila_tiempo["distancia_km"],
            "tiempo_optimo_min": fila_tiempo["tiempo_determinista_min"],
            "tiempo_base_min": fila_base["tiempo_determinista_min"],
            "RT_pct": (
                1
                - fila_tiempo["tiempo_determinista_min"]
                / fila_base["tiempo_determinista_min"]
            ) * 100,
            "RV_pct": (
                1
                - fila_simulada["desviacion_simulada_min"]
                / fila_base["desviacion_simulada_min"]
            ) * 100,
            "IC_pct": fila_simulada["IC_pct"],
            "NE": fila_tiempo["NE_astar"],
            "costo_dijkstra_min": fila_tiempo["costo_dijkstra"],
            "NE_dijkstra": fila_tiempo["NE_dijkstra"],
            "ejecucion_astar_ms": fila_tiempo["ejecucion_astar_ms"],
            "ejecucion_dijkstra_ms": fila_tiempo["ejecucion_dijkstra_ms"],
            "punto_base": intermedios[nombre]["nombre"],
        })
    return pd.DataFrame(filas)


def validar_tiempos_esperados(tabla, esperados, tolerancia=0.02):
    """Comprueba que los tiempos óptimos conserven valores de referencia."""
    tiempos = tabla["tiempo_optimo_min"]
    if len(tiempos) != len(esperados) or not all(
        math.isclose(valor, esperado, abs_tol=tolerancia)
        for valor, esperado in zip(tiempos, esperados)
    ):
        raise AssertionError("Los tiempos óptimos no coinciden con la referencia.")


def resumir_cambios_modelos(tabla):
    """Devuelve un indicador de cambio de ruta por cada par comparado."""
    return tabla.drop_duplicates("par")[["par", "ruta_cambio"]]
