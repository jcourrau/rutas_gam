"""Visualizaciones utilizadas por el notebook y el documento."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import osmnx as ox


COLORES_MODELOS = (
    "#2563eb",
    "#d97706",
    "#0f766e",
    "#7c3aed",
    "#dc2626",
    "#0891b2",
)
ESTILOS_MODELOS = ("-", "--", "-.", ":")


def _guardar(figura, ruta):
    if ruta:
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)
        figura.savefig(
            ruta,
            dpi=180,
            bbox_inches="tight",
            facecolor="white",
            transparent=False,
        )


def graficar_red_y_paradas(grafo, paradas, ruta=None):
    """Muestra la red vial y las veinte paradas seleccionadas."""
    fig, ax = ox.plot_graph(
        grafo, node_size=0, edge_color="#b8c1cc", edge_linewidth=0.35,
        bgcolor="white", show=False, close=False, figsize=(10, 7),
    )
    fig.patch.set_visible(True)
    fig.patch.set_facecolor("white")
    fig.patch.set_alpha(1)
    ax.set_facecolor("white")
    ax.patch.set_alpha(1)
    puntos = ax.scatter(
        paradas["longitud"], paradas["latitud"], c=paradas["w_i"],
        cmap="viridis", s=28 + paradas["w_i"] * 55, zorder=4,
    )
    barra_color = fig.colorbar(puntos, ax=ax, label="Índice de importancia w_i")
    barra_color.ax.set_facecolor("white")
    barra_color.ax.patch.set_alpha(1)
    ax.set_title("Red vial y 20 paradas importantes de San José", color="black")
    _guardar(fig, ruta)
    return fig


def graficar_importancia(paradas, ruta=None):
    """Compara la importancia de las paradas seleccionadas."""
    datos = paradas.head(20).sort_values("w_i")
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(datos["nombre"], datos["w_i"], color="#0f766e")
    ax.set_xlabel("Índice de importancia w_i")
    ax.set_title("Importancia combinada de las paradas seleccionadas")
    fig.tight_layout()
    _guardar(fig, ruta)
    return fig


def graficar_rutas(grafo, resultados, ruta=None):
    """Dibuja las rutas optimizadas de los pares analizados."""
    _, arcos = ox.graph_to_gdfs(grafo)
    fig, ejes = plt.subplots(1, len(resultados), figsize=(15, 5))
    colores = ["#2563eb", "#0f766e", "#d97706"]
    for eje, resultado, color in zip(np.atleast_1d(ejes), resultados, colores):
        arcos.plot(ax=eje, color="#d1d5db", linewidth=0.3)
        nodos = resultado["ruta"]
        eje.plot(
            [grafo.nodes[n]["x"] for n in nodos],
            [grafo.nodes[n]["y"] for n in nodos],
            color=color, linewidth=2,
        )
        eje.set_title(resultado["nombre"], fontsize=9)
        eje.set_axis_off()
    fig.suptitle("Rutas obtenidas con A* bidireccional")
    fig.tight_layout()
    _guardar(fig, ruta)
    return fig


def graficar_rutas_modelos(grafo, resultados, ruta=None):
    """Superpone las rutas elegidas por todos los modelos recibidos."""
    _, arcos = ox.graph_to_gdfs(grafo)
    fig, ejes = plt.subplots(1, len(resultados), figsize=(15, 5))
    for eje, resultado in zip(np.atleast_1d(ejes), resultados):
        arcos.plot(ax=eje, color="#d1d5db", linewidth=0.3)
        for indice, (etiqueta, detalle) in enumerate(
            resultado["modelos"].items()
        ):
            nodos = detalle["ruta"]
            eje.plot(
                [grafo.nodes[nodo]["x"] for nodo in nodos],
                [grafo.nodes[nodo]["y"] for nodo in nodos],
                color=COLORES_MODELOS[indice % len(COLORES_MODELOS)],
                linestyle=ESTILOS_MODELOS[indice % len(ESTILOS_MODELOS)],
                linewidth=2.2,
                label=etiqueta,
            )
        eje.set_title(resultado["nombre"], fontsize=9)
        eje.set_axis_off()
    controles, etiquetas = np.atleast_1d(ejes)[0].get_legend_handles_labels()
    fig.legend(
        controles,
        etiquetas,
        loc="lower center",
        ncol=len(resultados[0]["modelos"]),
        frameon=False,
    )
    fig.suptitle("Rutas obtenidas con los modelos")
    fig.tight_layout(rect=(0, 0.08, 1, 0.94))
    _guardar(fig, ruta)
    return fig


def _agrupar_distribuciones(datos_par, columna_modelo, tipos):
    """Agrupa modelos con exactamente los mismos tiempos simulados."""
    grupos = []
    for tipo in tipos:
        valores = datos_par.loc[
            datos_par[columna_modelo] == tipo,
            "tiempo_min",
        ].to_numpy()
        if valores.size == 0:
            continue

        grupo_coincidente = None
        if tipo != "Ruta base":
            grupo_coincidente = next(
                (
                    grupo
                    for grupo in grupos
                    if "Ruta base" not in grupo["modelos"]
                    and np.array_equal(grupo["valores"], valores)
                ),
                None,
            )

        if grupo_coincidente is None:
            grupos.append({"modelos": [tipo], "valores": valores})
        else:
            grupo_coincidente["modelos"].append(tipo)
    return grupos


def graficar_simulaciones(simulaciones, ruta=None):
    """Compara las distribuciones simuladas de cada par de rutas."""
    columna_modelo = (
        "tipo_ruta" if "tipo_ruta" in simulaciones.columns else "modelo"
    )
    columnas_requeridas = {"par", columna_modelo, "tiempo_min"}
    faltantes = columnas_requeridas.difference(simulaciones.columns)
    if faltantes:
        raise ValueError(
            "Faltan columnas para graficar las simulaciones: "
            + ", ".join(sorted(faltantes))
        )

    pares = simulaciones["par"].drop_duplicates().tolist()
    tipos = simulaciones[columna_modelo].drop_duplicates().tolist()
    if not pares or not tipos:
        raise ValueError("No hay simulaciones para graficar.")

    fig, ejes = plt.subplots(1, len(pares), figsize=(14, 4.5), sharey=True)
    ejes = np.atleast_1d(ejes)
    colores = {
        tipo: COLORES_MODELOS[indice % len(COLORES_MODELOS)]
        for indice, tipo in enumerate(tipos)
    }
    for eje, par in zip(ejes, pares):
        datos_par = simulaciones[simulaciones["par"] == par]
        grupos = _agrupar_distribuciones(datos_par, columna_modelo, tipos)
        coincidencias = []
        for grupo in grupos:
            nombres = grupo["modelos"]
            valores = grupo["valores"]
            color = colores[nombres[0]]
            if len(nombres) > 1:
                coincidencias.append(
                    "Modelo 1 = Modelo 2"
                    if len(nombres) == 2
                    else f"{len(nombres)} modelos coinciden"
                )
            eje.hist(
                valores, bins=28, density=True, alpha=0.45,
                color=color, edgecolor="white",
            )
            eje.axvline(valores.mean(), color=color, linewidth=1.8, linestyle="--")
        if coincidencias:
            eje.text(
                0.03,
                0.96,
                "\n".join(coincidencias),
                transform=eje.transAxes,
                va="top",
                fontsize=8,
                color="#374151",
                bbox={
                    "boxstyle": "round,pad=0.3",
                    "facecolor": "white",
                    "edgecolor": "#d1d5db",
                    "alpha": 0.9,
                },
            )
        eje.set_title(par, fontsize=10, fontweight="bold")
        eje.set_xlabel("Tiempo simulado (min)")
        eje.grid(axis="y", color="#e5e7eb", linewidth=0.8)
        eje.set_axisbelow(True)
        eje.spines[["top", "right"]].set_visible(False)
    ejes[0].set_ylabel("Densidad")
    controles = [
        Patch(
            facecolor=colores[tipo],
            edgecolor="white",
            alpha=0.55,
            label=tipo,
        )
        for tipo in tipos
    ]
    fig.legend(
        handles=controles, loc="lower center", ncol=min(3, len(controles)),
        frameon=False, bbox_to_anchor=(0.5, -0.02),
    )

    conteos = simulaciones.groupby(["par", columna_modelo]).size()
    if conteos.nunique() == 1:
        cantidad = f"{int(conteos.iloc[0]):,}".replace(",", " ")
        titulo = f"Distribución de tiempos en {cantidad} escenarios"
    else:
        titulo = "Distribución de tiempos simulados"
    fig.suptitle(
        titulo,
        fontsize=15, fontweight="bold",
    )
    fig.tight_layout(rect=(0, 0.1, 1, 0.92), w_pad=2)
    _guardar(fig, ruta)
    return fig


def graficar_comparacion_modelos(tabla, ruta=None):
    """Compara media y percentil 90 de todos los modelos recibidos."""
    modelos = tabla["modelo"].drop_duplicates().tolist()
    pares = tabla["par"].drop_duplicates().tolist()
    if not modelos or not pares:
        raise ValueError("No hay resultados de modelos para graficar.")

    colores = {
        modelo: COLORES_MODELOS[indice % len(COLORES_MODELOS)]
        for indice, modelo in enumerate(modelos)
    }
    posiciones = np.arange(len(pares))
    etiquetas_pares = [par.replace(" → ", "\n→ ") for par in pares]
    ancho_barra = 0.56 / len(modelos)
    desplazamientos = (
        np.arange(len(modelos)) - (len(modelos) - 1) / 2
    ) * ancho_barra

    fig, ejes = plt.subplots(1, 2, figsize=(14, 5.5))
    controles = []
    for eje, metrica, titulo in (
        (ejes[0], "media_simulada_min", "Tiempo medio simulado"),
        (ejes[1], "percentil_90_min", "Percentil 90 del tiempo"),
    ):
        pivote = tabla.pivot(index="par", columns="modelo", values=metrica)
        pivote = pivote.reindex(index=pares, columns=modelos)
        for indice, modelo in enumerate(modelos):
            barras = eje.bar(
                posiciones + desplazamientos[indice],
                pivote[modelo].to_numpy(),
                width=ancho_barra * 0.9,
                color=colores[modelo],
                label=modelo,
            )
            eje.bar_label(
                barras,
                fmt="%.2f",
                padding=3,
                fontsize=8,
                color="#374151",
            )
            if eje is ejes[0]:
                controles.append(barras[0])

        maximo = float(pivote.max().max())
        eje.set_ylim(0, maximo * 1.14 if maximo > 0 else 1)
        eje.set_title(titulo, fontsize=10, fontweight="bold")
        eje.set_xlabel("")
        eje.set_ylabel("Minutos")
        eje.set_xticks(posiciones, etiquetas_pares, rotation=0, ha="center")
        eje.tick_params(axis="both", labelsize=9)
        eje.grid(axis="y", color="#e5e7eb", linewidth=0.8)
        eje.set_axisbelow(True)
        eje.spines[["top", "right"]].set_visible(False)

    fig.legend(
        controles,
        modelos,
        loc="lower center",
        ncol=min(3, len(modelos)),
        frameon=False,
        bbox_to_anchor=(0.5, -0.02),
    )
    fig.suptitle("Comparación de los modelos de ruta", fontsize=15, fontweight="bold")
    fig.tight_layout(rect=(0, 0.12, 1, 0.92), w_pad=2)
    _guardar(fig, ruta)
    return fig


def graficar_metricas(tabla, ruta=None):
    """Compara las cuatro métricas de éxito por par."""
    colores = ["#2563eb", "#0f766e", "#d97706"]
    fig, ejes = plt.subplots(
        1, 2, figsize=(13, 5.4), gridspec_kw={"width_ratios": [1.55, 1]}
    )
    fig.patch.set_facecolor("white")

    metricas = ["RT_pct", "RV_pct", "IC_pct"]
    etiquetas = ["Reducción de tiempo", "Reducción de variabilidad", "Confiabilidad"]
    posiciones = np.arange(len(metricas))
    ancho = 0.22
    for indice, (_, fila) in enumerate(tabla.iterrows()):
        valores = fila[metricas].astype(float).to_numpy()
        barras = ejes[0].bar(
            posiciones + (indice - 1) * ancho,
            valores,
            ancho,
            color=colores[indice],
            label=fila["par"],
        )
        ejes[0].bar_label(barras, fmt="%.1f", padding=3, fontsize=8)

    ejes[0].set_xticks(posiciones, etiquetas)
    ejes[0].set_ylabel("Porcentaje (%)")
    ejes[0].set_title("Métricas de desempeño", loc="left", fontweight="bold")
    ejes[0].grid(axis="y", color="#e5e7eb", linewidth=0.8)
    ejes[0].set_axisbelow(True)

    algoritmos = ["A* bidireccional", "Dijkstra"]
    columnas_nodos = ["NE", "NE_dijkstra"]
    posiciones_nodos = np.arange(len(algoritmos))
    for indice, (_, fila) in enumerate(tabla.iterrows()):
        valores = fila[columnas_nodos].astype(float).to_numpy()
        barras = ejes[1].bar(
            posiciones_nodos + (indice - 1) * ancho,
            valores,
            ancho,
            color=colores[indice],
        )
        ejes[1].bar_label(barras, fmt="%.0f", padding=3, fontsize=8)

    ejes[1].set_xticks(posiciones_nodos, algoritmos)
    ejes[1].set_ylabel("Nodos explorados")
    ejes[1].set_title("Esfuerzo computacional", loc="left", fontweight="bold")
    ejes[1].grid(axis="y", color="#e5e7eb", linewidth=0.8)
    ejes[1].set_axisbelow(True)

    for eje in ejes:
        eje.spines[["top", "right"]].set_visible(False)
        eje.tick_params(colors="#374151")
    fig.legend(
        loc="lower center", bbox_to_anchor=(0.5, -0.02), ncol=3,
        frameon=False, title="Pares origen–destino",
    )
    fig.suptitle("Comparación de métricas de éxito", fontsize=15, fontweight="bold")
    fig.tight_layout(rect=(0, 0.12, 1, 0.94), w_pad=3)
    _guardar(fig, ruta)
    return fig


def graficar_sensibilidad_modelos(
    resumen_lambda,
    resumen_velocidades,
    resumen_replicas,
    valores_lambda,
    ruta=None,
):
    """Reúne los tres análisis de sensibilidad en una figura."""
    colores = {
        "Menor tiempo": "#2563eb",
        "Ajustada por variabilidad": "#0f766e",
    }
    valores_lambda = tuple(valores_lambda)
    salto = max(1, int(np.ceil(len(valores_lambda) / 6)))
    marcas_lambda = set(valores_lambda[::salto])
    marcas_lambda.update((valores_lambda[0], valores_lambda[-1]))
    cambios_lambda = resumen_lambda.loc[
        resumen_lambda["rutas_diferentes"].diff().fillna(0).ne(0),
        "lambda_riesgo",
    ]
    marcas_lambda.update(cambios_lambda)

    fig, ejes = plt.subplots(1, 3, figsize=(15, 4.5))

    ejes[0].plot(
        resumen_lambda["lambda_riesgo"],
        resumen_lambda["rutas_diferentes"],
        marker="o",
        color="#0f766e",
        linewidth=2,
    )
    ejes[0].set(
        title="Sensibilidad al riesgo",
        xlabel="lambda",
        ylabel="Rutas diferentes",
        xticks=sorted(marcas_lambda),
    )

    for modelo, datos in resumen_velocidades.groupby("modelo", sort=False):
        ejes[1].plot(
            datos["factor_velocidad_imputada"],
            datos["tiempo_medio_min"],
            marker="o",
            linewidth=2,
            color=colores[modelo],
            label=modelo,
        )
    ejes[1].set(
        title="Velocidades imputadas",
        xlabel="Factor de velocidad",
        ylabel="Tiempo medio (min)",
        xticks=[0.85, 1.0, 1.15],
    )

    for modelo, datos in resumen_replicas.groupby("modelo", sort=False):
        ejes[2].plot(
            datos["repeticiones"],
            datos["p90_medio_min"],
            marker="o",
            linewidth=2,
            color=colores[modelo],
            label=modelo,
        )
    ejes[2].set(
        title="Estabilidad Monte Carlo",
        xlabel="Réplicas",
        ylabel="Percentil 90 medio (min)",
        xticks=[200, 1000, 5000],
    )

    for eje in ejes:
        eje.grid(axis="y", color="#e5e7eb")
        eje.spines[["top", "right"]].set_visible(False)
    ejes[1].legend(frameon=False, fontsize=8)
    ejes[2].legend(frameon=False, fontsize=8)
    fig.suptitle(
        "Análisis de sensibilidad de los modelos",
        fontsize=15,
        fontweight="bold",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.93), w_pad=2)
    _guardar(fig, ruta)
    return fig
