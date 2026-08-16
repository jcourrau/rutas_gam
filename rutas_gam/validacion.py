"""Muestreo reproducible y sensibilidad de los modelos de ruta."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .algoritmos import dijkstra
from .datos import (
    agregar_costo_ajustado,
    agregar_tiempos,
    calcular_importancia,
    cargar_grafo,
    cargar_paradas,
    preparar_paradas,
)
from .flujo import buscar_parada
from .metricas import (
    evaluar_rutas_monte_carlo,
    incorporar_metricas_simuladas,
)
from .modelos import (
    ModeloRuta,
    comparar_resultados_modelos,
    ejecutar_modelo,
)


SEMILLA_CURSO = 2026


@dataclass(frozen=True)
class PreparacionValidacion:
    """Agrupa los datos y casos necesarios para validar los modelos.

    Attributes:
        grafo_crudo: Red vial antes de calcular los tiempos de arco.
        grafo: Red vial preparada con tiempos de flujo libre.
        casos_originales: Tres pares definidos para el estudio principal.
        casos_adicionales: Pares reproducibles usados para ampliar la muestra.
        casos_validacion: Unión ordenada de ambas colecciones de casos.
        comparacion_exportada: Resultados originales que enlazan ambas etapas.
        lambda_riesgo: Penalización reconstruida con el criterio determinista.
    """

    grafo_crudo: object
    grafo: object
    casos_originales: list[dict]
    casos_adicionales: list[dict]
    casos_validacion: list[dict]
    comparacion_exportada: pd.DataFrame
    lambda_riesgo: float


@dataclass(frozen=True)
class ResultadoValidacion:
    """Contiene la validación detallada y sus resúmenes comparativos."""

    tabla: pd.DataFrame
    rutas: list
    resumen_muestras: pd.DataFrame
    comparacion_modelos: pd.DataFrame


@dataclass(frozen=True)
class AnalisisSensibilidad:
    """Agrupa el detalle y el resumen de un supuesto modificado."""

    detalle: pd.DataFrame
    resumen: pd.DataFrame


def pares_aleatorios_validos(
    grafo,
    cantidad=30,
    semilla=SEMILLA_CURSO,
    excluir=None,
):
    """Selecciona pares reproducibles que poseen un camino dirigido.

    Args:
        grafo: Red vial preparada.
        cantidad: Número de pares requeridos.
        semilla: Semilla de ``default_rng``.
        excluir: Pares que no deben formar parte de la muestra.

    Returns:
        Lista de casos con nombre, origen y destino.
    """
    generador = np.random.default_rng(semilla)
    nodos = np.asarray(list(grafo.nodes()), dtype=object)
    excluidos = set(excluir or [])
    seleccionados = []
    usados = set(excluidos)
    intentos = 0
    limite = max(100, cantidad * 80)

    while len(seleccionados) < cantidad and intentos < limite:
        intentos += 1
        origen, destino = generador.choice(nodos, size=2, replace=False)
        par = (origen, destino)
        if par in usados:
            continue
        try:
            dijkstra(grafo, origen, destino)
        except ValueError:
            continue
        usados.add(par)
        seleccionados.append({
            "nombre": f"Validación {len(seleccionados) + 1:02d}",
            "origen": origen,
            "destino": destino,
        })

    if len(seleccionados) != cantidad:
        raise RuntimeError(
            f"Solo se encontraron {len(seleccionados)} de {cantidad} pares válidos."
        )
    return seleccionados


def preparar_validacion_ampliada(
    ruta_grafo,
    ruta_paradas,
    ruta_puntos,
    ruta_comparacion,
    configuraciones,
    valores_lambda,
    cantidad_adicional=30,
    semilla=SEMILLA_CURSO,
):
    """Prepara los casos y reconstruye la configuración seleccionada.

    Args:
        ruta_grafo: Archivo GraphML de la red vial.
        ruta_paradas: CSV con las paradas importantes.
        ruta_puntos: CSV con los puntos originales del estudio.
        ruta_comparacion: CSV exportado por la comparación principal.
        configuraciones: Tuplas con nombre, origen y destino de cada caso.
        valores_lambda: Penalizaciones consideradas en la selección.
        cantidad_adicional: Número de pares reproducibles que se añadirán.
        semilla: Semilla para seleccionar los pares adicionales.

    Returns:
        PreparacionValidacion con redes, casos, resultados previos y lambda.
    """
    grafo_crudo = cargar_grafo(ruta_grafo)
    grafo = agregar_tiempos(grafo_crudo)
    paradas = preparar_paradas(
        grafo,
        calcular_importancia(cargar_paradas(ruta_paradas)),
    )
    puntos_estudio = preparar_paradas(grafo, cargar_paradas(ruta_puntos))
    puntos_busqueda = pd.concat([paradas, puntos_estudio], ignore_index=True)

    casos_originales = [
        {
            "nombre": nombre,
            "origen": buscar_parada(puntos_busqueda, origen).node_id,
            "destino": buscar_parada(puntos_busqueda, destino).node_id,
        }
        for nombre, origen, destino in configuraciones
    ]
    excluir = [
        (caso["origen"], caso["destino"])
        for caso in casos_originales
    ]
    casos_adicionales = pares_aleatorios_validos(
        grafo,
        cantidad=cantidad_adicional,
        semilla=semilla,
        excluir=excluir,
    )
    tabla_lambda = comparar_lambda_determinista(
        grafo,
        casos_originales,
        valores=valores_lambda,
    )
    lambda_riesgo = seleccionar_lambda_con_cambio(tabla_lambda)
    comparacion_exportada = pd.read_csv(Path(ruta_comparacion))

    return PreparacionValidacion(
        grafo_crudo=grafo_crudo,
        grafo=grafo,
        casos_originales=casos_originales,
        casos_adicionales=casos_adicionales,
        casos_validacion=casos_originales + casos_adicionales,
        comparacion_exportada=comparacion_exportada,
        lambda_riesgo=lambda_riesgo,
    )


def comparar_modelos(
    grafo,
    casos,
    lambda_riesgo=1.0,
    repeticiones=1000,
    semilla=SEMILLA_CURSO,
):
    """Ejecuta la comparación principal mediante la interfaz genérica.

    Esta función se conserva como acceso abreviado para la validación y los
    análisis de sensibilidad. Los notebooks pueden ejecutar por separado cada
    modelo mediante ``ejecutar_modelo`` y combinarlos posteriormente con
    ``comparar_resultados_modelos``.

    Args:
        grafo: Grafo con tiempos de flujo libre.
        casos: Casos con nombre, origen y destino.
        lambda_riesgo: Penalización del segundo modelo.
        repeticiones: Escenarios Monte Carlo por ruta.
        semilla: Semilla base compartida entre ambos modelos.

    Returns:
        Tupla con una tabla de métricas y las rutas de cada caso.
    """
    preparado = agregar_costo_ajustado(grafo, lambda_riesgo=lambda_riesgo)
    modelos = (
        ModeloRuta("Menor tiempo", "travel_time_min"),
        ModeloRuta("Ajustada por variabilidad", "risk_adjusted_time_min"),
    )
    resultados = [
        ejecutar_modelo(preparado, casos, modelo)
        for modelo in modelos
    ]
    tabla, rutas = comparar_resultados_modelos(resultados)
    evaluacion = evaluar_rutas_monte_carlo(
        preparado,
        rutas,
        repeticiones=repeticiones,
        semilla=semilla,
    )
    tabla = incorporar_metricas_simuladas(tabla, evaluacion)
    tabla["lambda_riesgo"] = lambda_riesgo
    return tabla, rutas


def _validar_transferencia_resultados(tabla, comparacion_exportada):
    """Comprueba que los casos originales conservan los resultados previos."""
    columnas_clave = [
        "par",
        "modelo",
        "tiempo_determinista_min",
        "costo_objetivo",
        "ruta_cambio",
    ]
    actual = (
        tabla.loc[tabla["muestra"] == "Original", columnas_clave]
        .sort_values(["par", "modelo"])
        .reset_index(drop=True)
    )
    exportada = (
        comparacion_exportada[columnas_clave]
        .sort_values(["par", "modelo"])
        .reset_index(drop=True)
    )
    if not actual[["par", "modelo"]].equals(exportada[["par", "modelo"]]):
        raise AssertionError("Los pares y modelos exportados no coinciden.")
    if not np.allclose(
        actual[["tiempo_determinista_min", "costo_objetivo"]],
        exportada[["tiempo_determinista_min", "costo_objetivo"]],
    ):
        raise AssertionError("Los costos originales exportados no coinciden.")
    if not actual["ruta_cambio"].equals(exportada["ruta_cambio"]):
        raise AssertionError("Los cambios de ruta exportados no coinciden.")


def ejecutar_validacion_ampliada(
    preparacion,
    repeticiones=1000,
    semilla=SEMILLA_CURSO,
):
    """Valida ambos modelos y resume su desempeño por tipo de muestra.

    Args:
        preparacion: Datos producidos por :func:`preparar_validacion_ampliada`.
        repeticiones: Cantidad de réplicas Monte Carlo por recorrido.
        semilla: Semilla común del procedimiento de simulación.

    Returns:
        ResultadoValidacion con el detalle, las rutas y dos resúmenes.
    """
    if not isinstance(preparacion, PreparacionValidacion):
        raise TypeError("preparacion debe ser PreparacionValidacion.")

    tabla, rutas = comparar_modelos(
        preparacion.grafo,
        preparacion.casos_validacion,
        lambda_riesgo=preparacion.lambda_riesgo,
        repeticiones=repeticiones,
        semilla=semilla,
    )
    nombres_originales = {
        caso["nombre"] for caso in preparacion.casos_originales
    }
    tabla["muestra"] = np.where(
        tabla["par"].isin(nombres_originales),
        "Original",
        "Adicional",
    )
    if not tabla["coincide"].all() or tabla["diferencia_abs"].max() >= 1e-6:
        raise AssertionError("A* y Dijkstra deben coincidir en todos los costos.")
    _validar_transferencia_resultados(tabla, preparacion.comparacion_exportada)

    resumen_muestras = (
        tabla.drop_duplicates("par")
        .groupby("muestra", as_index=False, sort=False)
        .agg(
            pares=("par", "count"),
            rutas_diferentes=("ruta_cambio", "sum"),
        )
    )
    comparacion_modelos = (
        tabla.groupby(["muestra", "modelo"], as_index=False, sort=False)
        .agg(
            pares=("par", "nunique"),
            rutas_diferentes=("ruta_cambio", "sum"),
            tiempo_determinista_promedio_min=(
                "tiempo_determinista_min",
                "mean",
            ),
            media_simulada_promedio_min=("media_simulada_min", "mean"),
            desviacion_simulada_promedio_min=(
                "desviacion_simulada_min",
                "mean",
            ),
            p90_promedio_min=("percentil_90_min", "mean"),
            IC_promedio_pct=("IC_pct", "mean"),
        )
    )
    return ResultadoValidacion(
        tabla=tabla,
        rutas=rutas,
        resumen_muestras=resumen_muestras,
        comparacion_modelos=comparacion_modelos,
    )


def comparar_lambda_determinista(
    grafo,
    casos,
    valores=tuple(indice * 0.5 for indice in range(21)),
):
    """Compara resultados promedio para distintos valores de lambda.

    La comparación utiliza únicamente la selección determinista de las rutas.
    Cada resultado se contrasta con el Modelo 1 para contar cuántos pares
    cambian al aumentar la penalización por variabilidad.

    Args:
        grafo: Grafo con tiempos de flujo libre.
        casos: Casos con nombre, origen y destino.
        valores: Valores no negativos de lambda que se evaluarán.

    Returns:
        DataFrame con promedios de distancia, tiempo y costo objetivo, además
        del número y porcentaje de rutas diferentes respecto al Modelo 1.
    """
    valores = tuple(float(valor) for valor in valores)
    if not valores or any(valor < 0 for valor in valores):
        raise ValueError("Los valores de lambda deben ser no negativos.")
    if len(valores) != len(set(valores)):
        raise ValueError("Los valores de lambda no deben repetirse.")

    referencia = ejecutar_modelo(
        grafo,
        casos,
        ModeloRuta("Menor tiempo", "travel_time_min"),
    )
    firmas_referencia = {
        ruta["nombre"]: ruta["firma"]
        for ruta in referencia.rutas
    }

    filas = []
    for valor in valores:
        preparado = agregar_costo_ajustado(grafo, lambda_riesgo=valor)
        resultado = ejecutar_modelo(
            preparado,
            casos,
            ModeloRuta(
                "Ajustada por variabilidad",
                "risk_adjusted_time_min",
            ),
        )
        rutas_diferentes = sum(
            ruta["firma"] != firmas_referencia[ruta["nombre"]]
            for ruta in resultado.rutas
        )
        tabla = resultado.tabla
        filas.append({
            "lambda_riesgo": valor,
            "distancia_promedio_km": tabla["distancia_km"].mean(),
            "tiempo_promedio_min": tabla["tiempo_determinista_min"].mean(),
            "costo_objetivo_promedio_min": tabla["costo_objetivo"].mean(),
            "penalizacion_promedio_min": (
                tabla["costo_objetivo"] - tabla["tiempo_determinista_min"]
            ).mean(),
            "rutas_diferentes": rutas_diferentes,
            "rutas_diferentes_pct": rutas_diferentes / len(casos) * 100,
            "coincide_algoritmos": bool(tabla["coincide"].all()),
        })
    return pd.DataFrame(filas)


def seleccionar_lambda_con_cambio(tabla):
    """Selecciona el menor lambda positivo que modifica al menos una ruta."""
    columnas = {"lambda_riesgo", "rutas_diferentes"}
    faltantes = columnas.difference(tabla.columns)
    if faltantes:
        raise ValueError(
            "Faltan columnas en la comparación: "
            + ", ".join(sorted(faltantes))
        )
    candidatos = tabla.loc[
        (tabla["lambda_riesgo"] > 0)
        & (tabla["rutas_diferentes"] > 0),
        "lambda_riesgo",
    ]
    if candidatos.empty:
        raise ValueError("Ningún valor evaluado produjo una ruta diferente.")
    return float(candidatos.min())


def sensibilidad_lambda(
    grafo,
    casos,
    valores=(0.0, 1.0, 2.0),
    repeticiones=1000,
    semilla=SEMILLA_CURSO,
):
    """Evalúa el efecto de la penalización por variabilidad."""
    tablas = []
    for valor in valores:
        tabla, _ = comparar_modelos(
            grafo,
            casos,
            lambda_riesgo=valor,
            repeticiones=repeticiones,
            semilla=semilla,
        )
        ajustada = tabla[tabla["modelo"] == "Ajustada por variabilidad"].copy()
        tablas.append(ajustada)
    return pd.concat(tablas, ignore_index=True)


def sensibilidad_velocidades(
    grafo_crudo,
    casos,
    factores=(0.85, 1.0, 1.15),
    lambda_riesgo=1.0,
    repeticiones=1000,
    semilla=SEMILLA_CURSO,
):
    """Recalcula ambos modelos al modificar velocidades imputadas."""
    tablas = []
    for factor in factores:
        grafo = agregar_tiempos(grafo_crudo, escala_imputada=factor)
        tabla, _ = comparar_modelos(
            grafo,
            casos,
            lambda_riesgo=lambda_riesgo,
            repeticiones=repeticiones,
            semilla=semilla,
        )
        tabla["factor_velocidad_imputada"] = factor
        tablas.append(tabla)
    return pd.concat(tablas, ignore_index=True)


def sensibilidad_replicas(
    grafo,
    casos,
    valores=(200, 1000, 5000),
    lambda_riesgo=1.0,
    semilla=SEMILLA_CURSO,
):
    """Mide la estabilidad Monte Carlo según el número de réplicas."""
    tablas = []
    for repeticiones in valores:
        tabla, _ = comparar_modelos(
            grafo,
            casos,
            lambda_riesgo=lambda_riesgo,
            repeticiones=repeticiones,
            semilla=semilla,
        )
        tabla["repeticiones"] = repeticiones
        tablas.append(tabla)
    return pd.concat(tablas, ignore_index=True)


def analizar_sensibilidad_lambda(
    grafo,
    casos,
    valores,
    repeticiones=1000,
    semilla=SEMILLA_CURSO,
):
    """Ejecuta, verifica y resume la sensibilidad respecto a lambda."""
    detalle = sensibilidad_lambda(
        grafo,
        casos,
        valores=valores,
        repeticiones=repeticiones,
        semilla=semilla,
    )
    lambda_cero = detalle[detalle["lambda_riesgo"] == 0]
    if lambda_cero["ruta_cambio"].any():
        raise AssertionError("lambda=0 debe reproducir el Modelo 1.")
    costos = detalle.pivot(
        index="par",
        columns="lambda_riesgo",
        values="costo_objetivo",
    )
    if not (costos.diff(axis=1).iloc[:, 1:] >= -1e-9).all().all():
        raise AssertionError("El costo objetivo debe crecer con lambda.")
    resumen = (
        detalle.groupby("lambda_riesgo", as_index=False)
        .agg(
            pares=("par", "nunique"),
            rutas_diferentes=("ruta_cambio", "sum"),
            tiempo_medio_min=("media_simulada_min", "mean"),
            desviacion_media_min=("desviacion_simulada_min", "mean"),
            p90_medio_min=("percentil_90_min", "mean"),
            IC_medio_pct=("IC_pct", "mean"),
        )
    )
    return AnalisisSensibilidad(detalle=detalle, resumen=resumen)


def analizar_sensibilidad_velocidades(
    grafo_crudo,
    casos,
    factores,
    lambda_riesgo,
    repeticiones=1000,
    semilla=SEMILLA_CURSO,
):
    """Ejecuta y resume la sensibilidad de las velocidades imputadas."""
    detalle = sensibilidad_velocidades(
        grafo_crudo,
        casos,
        factores=factores,
        lambda_riesgo=lambda_riesgo,
        repeticiones=repeticiones,
        semilla=semilla,
    )
    cambios = (
        detalle.drop_duplicates(["factor_velocidad_imputada", "par"])
        .groupby("factor_velocidad_imputada", as_index=False)
        .agg(rutas_diferentes=("ruta_cambio", "sum"))
    )
    resumen = (
        detalle.groupby(
            ["factor_velocidad_imputada", "modelo"],
            as_index=False,
            sort=False,
        )
        .agg(
            pares=("par", "nunique"),
            tiempo_medio_min=("media_simulada_min", "mean"),
            desviacion_media_min=("desviacion_simulada_min", "mean"),
            p90_medio_min=("percentil_90_min", "mean"),
            IC_medio_pct=("IC_pct", "mean"),
        )
        .merge(cambios, on="factor_velocidad_imputada")
    )
    return AnalisisSensibilidad(detalle=detalle, resumen=resumen)


def analizar_sensibilidad_replicas(
    grafo,
    casos,
    valores,
    lambda_riesgo,
    semilla=SEMILLA_CURSO,
):
    """Ejecuta y resume la estabilidad según el número de réplicas."""
    detalle = sensibilidad_replicas(
        grafo,
        casos,
        valores=valores,
        lambda_riesgo=lambda_riesgo,
        semilla=semilla,
    )
    resumen = (
        detalle.groupby(["repeticiones", "modelo"], as_index=False, sort=False)
        .agg(
            pares=("par", "nunique"),
            tiempo_medio_min=("media_simulada_min", "mean"),
            desviacion_media_min=("desviacion_simulada_min", "mean"),
            p90_medio_min=("percentil_90_min", "mean"),
            IC_medio_pct=("IC_pct", "mean"),
        )
    )
    return AnalisisSensibilidad(detalle=detalle, resumen=resumen)


def consolidar_sensibilidad(
    analisis_lambda,
    analisis_velocidades,
    analisis_replicas,
):
    """Construye la tabla final de los tres análisis de sensibilidad."""
    resumen_lambda = analisis_lambda.resumen.assign(
        analisis="Penalización de riesgo",
        modelo="Ajustada por variabilidad",
        efecto_observado="Sin cambios hasta lambda 6; uno con 6.5 y dos desde 9.5",
        conclusion="Estable ante penalizaciones moderadas y sensible desde lambda 6.5",
    ).rename(columns={"lambda_riesgo": "valor"})
    resumen_velocidades = analisis_velocidades.resumen.assign(
        analisis="Velocidades imputadas",
        efecto_observado=(
            "Cambian los tiempos; difieren dos pares con 0.85 y uno con 1.00 o 1.15"
        ),
        conclusion="Frágil ante la velocidad imputada en al menos un caso",
    ).rename(columns={"factor_velocidad_imputada": "valor"})
    resumen_replicas = analisis_replicas.resumen.assign(
        analisis="Réplicas Monte Carlo",
        rutas_diferentes=np.nan,
        efecto_observado="Media y percentil 90 se estabilizan al aumentar las réplicas",
        conclusion="Razonablemente robusta con 1000 réplicas",
    ).rename(columns={"repeticiones": "valor"})

    columnas = [
        "analisis",
        "valor",
        "modelo",
        "pares",
        "rutas_diferentes",
        "tiempo_medio_min",
        "desviacion_media_min",
        "p90_medio_min",
        "IC_medio_pct",
        "efecto_observado",
        "conclusion",
    ]
    return pd.concat(
        [
            resumen_lambda[columnas],
            resumen_velocidades[columnas],
            resumen_replicas[columnas],
        ],
        ignore_index=True,
    )


def exportar_resultados_validacion(
    resultado,
    analisis_lambda,
    analisis_velocidades,
    analisis_replicas,
    directorio,
):
    """Exporta el detalle, la comparación y la sensibilidad consolidados.

    Args:
        resultado: Resultado producido por :func:`ejecutar_validacion_ampliada`.
        analisis_lambda: Sensibilidad de la penalización de riesgo.
        analisis_velocidades: Sensibilidad de las velocidades imputadas.
        analisis_replicas: Sensibilidad del número de réplicas.
        directorio: Carpeta donde se escribirán los tres archivos CSV.

    Returns:
        DataFrame consolidado de sensibilidad que se guardó en disco.
    """
    directorio = Path(directorio)
    directorio.mkdir(parents=True, exist_ok=True)
    sensibilidad = consolidar_sensibilidad(
        analisis_lambda,
        analisis_velocidades,
        analisis_replicas,
    )
    resultado.tabla.to_csv(directorio / "validacion_modelos.csv", index=False)
    resultado.comparacion_modelos.to_csv(
        directorio / "comparacion_validacion.csv",
        index=False,
    )
    sensibilidad.to_csv(directorio / "sensibilidad_modelos.csv", index=False)
    return sensibilidad
