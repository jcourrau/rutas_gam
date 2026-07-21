"""Visualizaciones utilizadas por el notebook y el documento."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import osmnx as ox


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
