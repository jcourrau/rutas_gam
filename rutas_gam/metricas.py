"""Métricas deterministas y estocásticas de las rutas."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .datos import sigma_por_tipo


@dataclass(frozen=True)
class ResultadoMonteCarlo:
    """Agrupa los escenarios simulados y sus métricas resumidas.

    Attributes:
        tabla: Una fila de métricas por par y recorrido evaluado.
        escenarios: Un tiempo total por par, recorrido y repetición.
    """

    tabla: pd.DataFrame
    escenarios: pd.DataFrame


def arco_minimo(grafo, origen, destino, peso="travel_time_min"):
    """Obtiene el arco paralelo con el menor valor del peso indicado."""
    return min(
        grafo[origen][destino].values(),
        key=lambda datos: float(datos[peso]),
    )


def resumen_ruta(grafo, ruta, peso_seleccion="travel_time_min"):
    """Resume distancia, tiempo y costo de una ruta fija."""
    distancia, tiempo, costo = 0.0, 0.0, 0.0
    for origen, destino in zip(ruta[:-1], ruta[1:]):
        arco = arco_minimo(grafo, origen, destino, peso=peso_seleccion)
        distancia += float(arco["length"])
        tiempo += float(arco["travel_time_min"])
        costo += float(arco[peso_seleccion])
    return {
        "distancia_km": distancia / 1000,
        "tiempo_min": tiempo,
        "costo_objetivo": costo,
    }


def simular_tiempos(
    grafo,
    ruta,
    repeticiones=1000,
    semilla=2026,
    sigma_general=0.15,
    peso_seleccion="travel_time_min",
):
    """Simula tiempos de una ruta fija con variación lognormal.

    Args:
        grafo: Grafo con tiempos de viaje por arco.
        ruta: Secuencia fija de nodos.
        repeticiones: Cantidad de escenarios Monte Carlo.
        semilla: Semilla del generador reproducible.
        sigma_general: Dispersión de la condición compartida.
        peso_seleccion: Peso usado para identificar el arco paralelo recorrido.

    Returns:
        Arreglo con un tiempo total por escenario.
    """
    if repeticiones <= 1:
        raise ValueError("repeticiones debe ser mayor que uno.")
    if sigma_general < 0:
        raise ValueError("sigma_general no puede ser negativo.")

    generador = np.random.default_rng(semilla)
    totales = np.zeros(repeticiones)
    factor_general = generador.lognormal(
        -sigma_general**2 / 2,
        sigma_general,
        repeticiones,
    )
    for origen, destino in zip(ruta[:-1], ruta[1:]):
        arco = arco_minimo(grafo, origen, destino, peso=peso_seleccion)
        sigma = sigma_por_tipo(arco.get("highway"))
        multiplicador = generador.lognormal(
            -sigma**2 / 2,
            sigma,
            repeticiones,
        )
        totales += float(arco["travel_time_min"]) * multiplicador
    return totales * factor_general


def resumir_simulacion(tiempos):
    """Resume una distribución Monte Carlo con métricas comparables."""
    tiempos = np.asarray(tiempos, dtype=float)
    media = float(tiempos.mean())
    return {
        "media_simulada_min": media,
        "desviacion_simulada_min": float(tiempos.std(ddof=1)),
        "percentil_90_min": float(np.quantile(tiempos, 0.90)),
        "IC_pct": float(np.mean(tiempos <= 1.15 * media) * 100),
    }


def resumir_simulaciones(simulaciones):
    """Resume una tabla de escenarios por par y recorrido.

    Args:
        simulaciones: Tabla con las columnas ``par``, ``modelo`` y
            ``tiempo_min``.

    Returns:
        DataFrame con media, desviación, percentil 90 e índice de
        confiabilidad para cada recorrido.
    """
    requeridas = {"par", "modelo", "tiempo_min"}
    faltantes = requeridas.difference(simulaciones.columns)
    if faltantes:
        raise ValueError(
            "Faltan columnas en las simulaciones: "
            + ", ".join(sorted(faltantes))
        )
    if simulaciones.empty:
        raise ValueError("No hay escenarios Monte Carlo para resumir.")

    filas = []
    for (par, modelo), grupo in simulaciones.groupby(
        ["par", "modelo"], sort=False
    ):
        filas.append({
            "par": par,
            "modelo": modelo,
            **resumir_simulacion(grupo["tiempo_min"]),
        })
    return pd.DataFrame(filas)


def _especificaciones_rutas(comparacion):
    """Devuelve los recorridos y pesos incluidos en una comparación."""
    especificaciones = [
        (nombre, detalle["ruta"], detalle["peso"])
        for nombre, detalle in comparacion["modelos"].items()
    ]
    if "ruta_base" in comparacion:
        especificaciones.append((
            "Ruta base",
            comparacion["ruta_base"],
            "travel_time_min",
        ))
    return especificaciones


def comparar_simulaciones(grafo, rutas, repeticiones=1000, semilla=2026):
    """Reúne simulaciones de cualquier cantidad de modelos y la ruta base.

    Args:
        grafo: Red que contiene todos los pesos usados por los modelos.
        rutas: Comparaciones generadas por ``comparar_resultados_modelos``.
            Cada elemento puede incluir además una ``ruta_base``.
        repeticiones: Escenarios Monte Carlo por recorrido.
        semilla: Semilla base común para realizar una comparación reproducible.

    Returns:
        DataFrame largo con un tiempo por par, modelo y escenario.
    """
    registros = []
    for numero, comparacion in enumerate(rutas):
        for modelo, recorrido, peso in _especificaciones_rutas(comparacion):
            tiempos = simular_tiempos(
                grafo,
                recorrido,
                repeticiones=repeticiones,
                semilla=semilla + numero,
                peso_seleccion=peso,
            )
            registros.extend(
                {
                    "par": comparacion["nombre"],
                    "modelo": modelo,
                    "tiempo_min": tiempo,
                }
                for tiempo in tiempos
            )
    return pd.DataFrame(registros)


def evaluar_rutas_monte_carlo(
    grafo,
    rutas,
    repeticiones=1000,
    semilla=2026,
):
    """Evalúa rutas fijas bajo escenarios Monte Carlo comparables.

    La función recibe cualquier cantidad de modelos y una ruta base opcional.
    Todas las rutas de un mismo par utilizan la misma semilla para que la
    comparación se realice bajo condiciones reproducibles.

    Args:
        grafo: Red con tiempos de viaje y los pesos de selección utilizados.
        rutas: Comparaciones generadas por ``comparar_resultados_modelos``.
        repeticiones: Escenarios Monte Carlo por recorrido.
        semilla: Semilla base, incrementada únicamente entre pares.

    Returns:
        ResultadoMonteCarlo con métricas resumidas y escenarios individuales.
    """
    escenarios = comparar_simulaciones(
        grafo,
        rutas,
        repeticiones=repeticiones,
        semilla=semilla,
    )
    resumen_simulado = resumir_simulaciones(escenarios)

    deterministas = []
    for comparacion in rutas:
        for modelo, recorrido, peso in _especificaciones_rutas(comparacion):
            resumen = resumen_ruta(
                grafo,
                recorrido,
                peso_seleccion=peso,
            )
            deterministas.append({
                "par": comparacion["nombre"],
                "modelo": modelo,
                "distancia_km": resumen["distancia_km"],
                "tiempo_determinista_min": resumen["tiempo_min"],
                "costo_objetivo": resumen["costo_objetivo"],
            })

    tabla = pd.DataFrame(deterministas).merge(
        resumen_simulado,
        on=["par", "modelo"],
        how="left",
        validate="one_to_one",
    )
    return ResultadoMonteCarlo(tabla=tabla, escenarios=escenarios)


def incorporar_metricas_simuladas(tabla_modelos, evaluacion):
    """Añade a una tabla determinista las métricas Monte Carlo disponibles.

    Args:
        tabla_modelos: Resultado de ``comparar_resultados_modelos``.
        evaluacion: Resultado producido por ``evaluar_rutas_monte_carlo``.

    Returns:
        Copia de la tabla con métricas simuladas para cada par y modelo.
    """
    if not isinstance(evaluacion, ResultadoMonteCarlo):
        raise TypeError("evaluacion debe ser un ResultadoMonteCarlo.")

    columnas = [
        "par",
        "modelo",
        "media_simulada_min",
        "desviacion_simulada_min",
        "percentil_90_min",
        "IC_pct",
    ]
    combinada = tabla_modelos.merge(
        evaluacion.tabla[columnas],
        on=["par", "modelo"],
        how="left",
        validate="one_to_one",
    )
    metricas = columnas[2:]
    if combinada[metricas].isna().any().any():
        raise ValueError("No todas las rutas de los modelos fueron simuladas.")
    return combinada


def resumir_comparacion_con_ruta_base(
    tabla_modelos,
    tabla_ruta_base,
    modelos=None,
):
    """Resume tiempos simulados y mejoras respecto a una ruta base.

    Args:
        tabla_modelos: Resultados Monte Carlo de los modelos comparados.
        tabla_ruta_base: Resultados Monte Carlo de las rutas base.
        modelos: Nombres de los modelos y orden en que deben mostrarse. Si se
            omite, se conserva el orden de aparición en ``tabla_modelos``.

    Returns:
        DataFrame con una fila por par, las medias simuladas, las mejoras
        porcentuales respecto a la ruta base y una fila final de promedio.

    Raises:
        ValueError: Si faltan columnas, modelos, rutas base o valores para
            alguno de los pares comparados.
    """
    columnas_requeridas = {"par", "modelo", "media_simulada_min"}
    for nombre, tabla in (
        ("tabla_modelos", tabla_modelos),
        ("tabla_ruta_base", tabla_ruta_base),
    ):
        faltantes = columnas_requeridas.difference(tabla.columns)
        if faltantes:
            raise ValueError(
                f"Faltan columnas en {nombre}: " + ", ".join(sorted(faltantes))
            )

    pares = tabla_modelos["par"].drop_duplicates().tolist()
    modelos = (
        tabla_modelos["modelo"].drop_duplicates().tolist()
        if modelos is None
        else list(modelos)
    )
    if not pares:
        raise ValueError("No hay pares de rutas para resumir.")
    if not modelos or len(modelos) != len(set(modelos)):
        raise ValueError("Los modelos deben ser una lista no vacía y sin duplicados.")

    medias_modelos = tabla_modelos.loc[
        tabla_modelos["modelo"].isin(modelos),
        ["par", "modelo", "media_simulada_min"],
    ]
    medias_base = tabla_ruta_base.loc[
        tabla_ruta_base["modelo"] == "Ruta base",
        ["par", "modelo", "media_simulada_min"],
    ]
    medias = pd.concat([medias_modelos, medias_base], ignore_index=True)
    if medias.duplicated(["par", "modelo"]).any():
        raise ValueError("Cada par debe tener una única media por recorrido.")

    pivote = medias.pivot(
        index="par",
        columns="modelo",
        values="media_simulada_min",
    ).reindex(pares)
    columnas_esperadas = [*modelos, "Ruta base"]
    faltantes = [columna for columna in columnas_esperadas if columna not in pivote]
    if faltantes or pivote.reindex(columns=columnas_esperadas).isna().any().any():
        raise ValueError("Cada par debe incluir todos los modelos y una ruta base.")

    resumen = pd.DataFrame(index=pares)
    for numero, modelo in enumerate(modelos, start=1):
        resumen[f"Modelo {numero} (min)"] = pivote[modelo]
    resumen["Ruta base (min)"] = pivote["Ruta base"]
    for numero in range(1, len(modelos) + 1):
        resumen[f"Mejora Modelo {numero} (%)"] = (
            1
            - resumen[f"Modelo {numero} (min)"]
            / resumen["Ruta base (min)"]
        ) * 100

    resumen.index.name = "Par"
    resumen.loc["Promedio"] = resumen.mean(axis=0)
    return resumen


def evaluar_rutas(
    grafo,
    ruta_optima,
    ruta_base,
    nodos_explorados,
    semilla=2026,
    repeticiones=1000,
):
    """Calcula las métricas RT, RV, IC y NE definidas en el Avance 1."""
    optima = resumen_ruta(grafo, ruta_optima)
    base = resumen_ruta(grafo, ruta_base)
    simulada_optima = simular_tiempos(
        grafo, ruta_optima, repeticiones=repeticiones, semilla=semilla
    )
    simulada_base = simular_tiempos(
        grafo, ruta_base, repeticiones=repeticiones, semilla=semilla
    )
    reduccion_tiempo = (
        (base["tiempo_min"] - optima["tiempo_min"])
        / base["tiempo_min"]
        * 100
    )
    desviacion_optima = simulada_optima.std(ddof=1)
    desviacion_base = simulada_base.std(ddof=1)
    return pd.Series({
        "distancia_optima_km": optima["distancia_km"],
        "tiempo_optimo_min": optima["tiempo_min"],
        "tiempo_base_min": base["tiempo_min"],
        "RT_pct": reduccion_tiempo,
        "RV_pct": (1 - desviacion_optima / desviacion_base) * 100,
        "IC_pct": np.mean(
            simulada_optima <= 1.15 * simulada_optima.mean()
        ) * 100,
        "NE": nodos_explorados,
    })
