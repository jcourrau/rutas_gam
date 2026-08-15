"""Ejecución uniforme y comparación de modelos de selección de rutas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import pandas as pd

from .algoritmos import astar_bidireccional, dijkstra
from .metricas import resumen_ruta


@dataclass(frozen=True)
class ModeloRuta:
    """Define una función de costo que puede resolverse sobre la red.

    Un modelo nuevo puede incorporarse preparando un atributo de costo en los
    arcos y declarando su nombre y peso. La escala de la heurística debe ser una
    cota inferior válida para ese costo; puede fijarse en cero si no se dispone
    de una heurística admisible.

    Attributes:
        nombre: Etiqueta legible utilizada en tablas y figuras.
        peso: Atributo de los arcos que representa la función de costo.
        escala_heuristica: Multiplicador no negativo de la heurística temporal.
    """

    nombre: str
    peso: str
    escala_heuristica: float = 1.0

    def __post_init__(self):
        """Valida que la especificación sea utilizable."""
        if not self.nombre.strip():
            raise ValueError("El modelo debe tener un nombre.")
        if not self.peso.strip():
            raise ValueError("El modelo debe indicar un peso de arco.")
        if self.escala_heuristica < 0:
            raise ValueError("La escala de la heurística no puede ser negativa.")


@dataclass(frozen=True)
class ResultadoModelo:
    """Agrupa la salida completa de un modelo para varios pares.

    Attributes:
        modelo: Especificación utilizada para resolver los casos.
        tabla: Métricas deterministas y de validación algorítmica.
        rutas: Rutas y firmas de arcos obtenidas para cada par.
    """

    modelo: ModeloRuta
    tabla: pd.DataFrame
    rutas: tuple[dict[str, Any], ...]


def _firma_ruta(grafo, ruta, peso):
    """Representa una ruta incluyendo el arco paralelo seleccionado."""
    firma = []
    for origen, destino in zip(ruta[:-1], ruta[1:]):
        clave = min(
            grafo[origen][destino],
            key=lambda actual: float(grafo[origen][destino][actual][peso]),
        )
        firma.append((origen, destino, clave))
    return tuple(firma)


def _validar_peso(grafo, modelo):
    """Comprueba que todos los arcos posean el costo solicitado."""
    for origen, destino, clave, datos in grafo.edges(keys=True, data=True):
        if modelo.peso not in datos:
            raise ValueError(
                f"El arco {(origen, destino, clave)} no contiene "
                f"el peso {modelo.peso!r} del modelo {modelo.nombre!r}."
            )


def ejecutar_modelo(
    grafo,
    casos,
    modelo,
):
    """Selecciona y valida rutas para una colección de pares.

    A* bidireccional selecciona cada ruta utilizando el peso declarado por el
    modelo y Dijkstra resuelve la misma función objetivo como control. La
    evaluación estocástica se realiza por separado una vez fijadas las rutas.

    Args:
        grafo: Red con el atributo de costo requerido por ``modelo``.
        casos: Casos con las claves ``nombre``, ``origen`` y ``destino``.
        modelo: Instancia de :class:`ModeloRuta`.

    Returns:
        ResultadoModelo con una fila y una ruta por caso.
    """
    if not isinstance(modelo, ModeloRuta):
        raise TypeError("modelo debe ser una instancia de ModeloRuta.")
    _validar_peso(grafo, modelo)

    filas = []
    rutas = []
    for caso in casos:
        resultado_astar = astar_bidireccional(
            grafo,
            caso["origen"],
            caso["destino"],
            peso=modelo.peso,
            escala_heuristica=modelo.escala_heuristica,
        )
        resultado_dijkstra = dijkstra(
            grafo,
            caso["origen"],
            caso["destino"],
            peso=modelo.peso,
        )
        resumen = resumen_ruta(
            grafo,
            resultado_astar["ruta"],
            peso_seleccion=modelo.peso,
        )
        diferencia = abs(
            resultado_astar["costo"] - resultado_dijkstra["costo"]
        )
        filas.append({
            "par": caso["nombre"],
            "modelo": modelo.nombre,
            "peso_modelo": modelo.peso,
            "distancia_km": resumen["distancia_km"],
            "tiempo_determinista_min": resumen["tiempo_min"],
            "costo_objetivo": resumen["costo_objetivo"],
            "costo_astar": resultado_astar["costo"],
            "costo_dijkstra": resultado_dijkstra["costo"],
            "diferencia_abs": diferencia,
            "coincide": diferencia < 1e-6,
            "NE_astar": resultado_astar["nodos_explorados"],
            "NE_dijkstra": resultado_dijkstra["nodos_explorados"],
            "ejecucion_astar_ms": resultado_astar["milisegundos"],
            "ejecucion_dijkstra_ms": resultado_dijkstra["milisegundos"],
        })
        rutas.append({
            "nombre": caso["nombre"],
            "origen": caso["origen"],
            "destino": caso["destino"],
            "modelo": modelo.nombre,
            "peso": modelo.peso,
            "ruta": resultado_astar["ruta"],
            "firma": _firma_ruta(grafo, resultado_astar["ruta"], modelo.peso),
        })

    return ResultadoModelo(
        modelo=modelo,
        tabla=pd.DataFrame(filas),
        rutas=tuple(rutas),
    )


def comparar_resultados_modelos(resultados: Sequence[ResultadoModelo]):
    """Combina modelos ejecutados sobre los mismos pares.

    El primer resultado funciona como referencia para identificar qué modelos
    seleccionan una ruta distinta. La estructura consolidada conserva un mapa
    por nombre de modelo, de modo que la comparación admite modelos futuros sin
    agregar nuevas claves específicas al código.

    Args:
        resultados: Dos o más resultados producidos por ``ejecutar_modelo``.

    Returns:
        Tupla con la tabla comparativa y una lista de rutas por par.
    """
    resultados = tuple(resultados)
    if len(resultados) < 2:
        raise ValueError("Se necesitan al menos dos modelos para comparar.")
    if not all(isinstance(resultado, ResultadoModelo) for resultado in resultados):
        raise TypeError("Todos los elementos deben ser ResultadoModelo.")

    nombres = [resultado.modelo.nombre for resultado in resultados]
    if len(nombres) != len(set(nombres)):
        raise ValueError("Cada modelo comparado debe tener un nombre único.")

    pares_referencia = [ruta["nombre"] for ruta in resultados[0].rutas]
    rutas_por_modelo = []
    for resultado in resultados:
        indice = {ruta["nombre"]: ruta for ruta in resultado.rutas}
        if set(indice) != set(pares_referencia):
            raise ValueError("Los modelos deben ejecutarse sobre los mismos pares.")
        rutas_por_modelo.append(indice)

    comparaciones = []
    cambios_por_par = {}
    cambios_individuales = {}
    for par in pares_referencia:
        referencia = rutas_por_modelo[0][par]
        modelos = {}
        diferencias = {}
        for resultado, indice in zip(resultados, rutas_por_modelo):
            ruta = indice[par]
            difiere = ruta["firma"] != referencia["firma"]
            diferencias[resultado.modelo.nombre] = difiere
            modelos[resultado.modelo.nombre] = {
                "ruta": ruta["ruta"],
                "peso": ruta["peso"],
                "firma": ruta["firma"],
            }
        cambio = any(diferencias.values())
        cambios_por_par[par] = cambio
        cambios_individuales[par] = diferencias
        comparaciones.append({
            "nombre": par,
            "origen": referencia["origen"],
            "destino": referencia["destino"],
            "modelos": modelos,
            "ruta_cambio": cambio,
        })

    tabla = pd.concat(
        [resultado.tabla for resultado in resultados],
        ignore_index=True,
    )
    tabla["ruta_cambio"] = tabla["par"].map(cambios_por_par).astype(bool)
    tabla["difiere_referencia"] = [
        cambios_individuales[par][modelo]
        for par, modelo in zip(tabla["par"], tabla["modelo"])
    ]
    return tabla, comparaciones
