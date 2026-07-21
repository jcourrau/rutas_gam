"""Algoritmos de caminos mínimos utilizados en el proyecto."""

from __future__ import annotations

import heapq
import math
import time


def _peso_minimo(arcos, atributo):
    return min(float(datos[atributo]) for datos in arcos.values())


def _distancia_geodesica(latitud_1, longitud_1, latitud_2, longitud_2):
    radio = 6_371_009
    phi_1, phi_2 = math.radians(latitud_1), math.radians(latitud_2)
    cambio_phi = math.radians(latitud_2 - latitud_1)
    cambio_lambda = math.radians(longitud_2 - longitud_1)
    valor = (
        math.sin(cambio_phi / 2) ** 2
        + math.cos(phi_1) * math.cos(phi_2) * math.sin(cambio_lambda / 2) ** 2
    )
    return 2 * radio * math.asin(math.sqrt(valor))


def _heuristica(grafo, nodo, destino, velocidad_maxima):
    actual = grafo.nodes[nodo]
    final = grafo.nodes[destino]
    distancia = _distancia_geodesica(
        actual["y"], actual["x"], final["y"], final["x"]
    )
    return distancia / velocidad_maxima * 0.06


def astar_bidireccional(grafo, origen, destino, peso="travel_time_min"):
    """Encuentra un camino mínimo mediante A* bidireccional."""
    inicio = time.perf_counter()
    velocidad_maxima = max(
        float(datos["speed_kph"])
        for _, _, _, datos in grafo.edges(keys=True, data=True)
    )
    inverso = grafo.reverse(copy=False)
    dist_frente, dist_atras = {origen: 0.0}, {destino: 0.0}
    padre_frente, padre_atras = {origen: None}, {destino: None}
    cola_frente = [(_heuristica(grafo, origen, destino, velocidad_maxima), 0.0, origen)]
    cola_atras = [(_heuristica(grafo, destino, origen, velocidad_maxima), 0.0, destino)]
    cerrados_frente, cerrados_atras = set(), set()
    mejor_costo, encuentro = math.inf, None

    def limpiar(cola, distancias, cerrados):
        while cola and (
            cola[0][2] in cerrados or cola[0][1] != distancias.get(cola[0][2])
        ):
            heapq.heappop(cola)

    while cola_frente and cola_atras:
        limpiar(cola_frente, dist_frente, cerrados_frente)
        limpiar(cola_atras, dist_atras, cerrados_atras)
        if not cola_frente or not cola_atras:
            break
        if max(cola_frente[0][0], cola_atras[0][0]) >= mejor_costo:
            break

        hacia_adelante = cola_frente[0][0] <= cola_atras[0][0]
        cola = cola_frente if hacia_adelante else cola_atras
        distancias = dist_frente if hacia_adelante else dist_atras
        otras_distancias = dist_atras if hacia_adelante else dist_frente
        padres = padre_frente if hacia_adelante else padre_atras
        cerrados = cerrados_frente if hacia_adelante else cerrados_atras
        red = grafo if hacia_adelante else inverso
        meta = destino if hacia_adelante else origen

        _, costo_actual, nodo = heapq.heappop(cola)
        if nodo in cerrados or costo_actual != distancias[nodo]:
            continue
        cerrados.add(nodo)
        if nodo in otras_distancias and costo_actual + otras_distancias[nodo] < mejor_costo:
            mejor_costo = costo_actual + otras_distancias[nodo]
            encuentro = nodo

        for vecino, arcos in red.adj[nodo].items():
            nuevo_costo = costo_actual + _peso_minimo(arcos, peso)
            if nuevo_costo < distancias.get(vecino, math.inf):
                distancias[vecino] = nuevo_costo
                padres[vecino] = nodo
                estimado = nuevo_costo + _heuristica(
                    grafo, vecino, meta, velocidad_maxima
                )
                heapq.heappush(cola, (estimado, nuevo_costo, vecino))
            if vecino in otras_distancias:
                costo_completo = nuevo_costo + otras_distancias[vecino]
                if costo_completo < mejor_costo:
                    mejor_costo, encuentro = costo_completo, vecino

    if encuentro is None:
        raise ValueError("No existe un camino dirigido entre los nodos indicados.")

    izquierda, nodo = [], encuentro
    while nodo is not None:
        izquierda.append(nodo)
        nodo = padre_frente[nodo]
    izquierda.reverse()
    derecha, nodo = [], padre_atras[encuentro]
    while nodo is not None:
        derecha.append(nodo)
        nodo = padre_atras[nodo]
    return {
        "ruta": izquierda + derecha,
        "costo": mejor_costo,
        "nodos_explorados": len(cerrados_frente | cerrados_atras),
        "milisegundos": (time.perf_counter() - inicio) * 1000,
    }


def dijkstra(grafo, origen, destino, peso="travel_time_min"):
    """Calcula un camino mínimo con Dijkstra para validar A*."""
    inicio = time.perf_counter()
    distancias, padres = {origen: 0.0}, {origen: None}
    cola, cerrados = [(0.0, origen)], set()
    while cola:
        costo, nodo = heapq.heappop(cola)
        if nodo in cerrados or costo != distancias[nodo]:
            continue
        cerrados.add(nodo)
        if nodo == destino:
            break
        for vecino, arcos in grafo.adj[nodo].items():
            nuevo_costo = costo + _peso_minimo(arcos, peso)
            if nuevo_costo < distancias.get(vecino, math.inf):
                distancias[vecino] = nuevo_costo
                padres[vecino] = nodo
                heapq.heappush(cola, (nuevo_costo, vecino))
    if destino not in distancias:
        raise ValueError("No existe un camino dirigido entre los nodos indicados.")
    ruta, nodo = [], destino
    while nodo is not None:
        ruta.append(nodo)
        nodo = padres[nodo]
    return {
        "ruta": ruta[::-1],
        "costo": distancias[destino],
        "nodos_explorados": len(cerrados),
        "milisegundos": (time.perf_counter() - inicio) * 1000,
    }


def ruta_por_puntos(grafo, puntos, peso="length"):
    """Construye una ruta base que pasa por una lista de nodos."""
    import networkx as nx

    ruta = []
    for origen, destino in zip(puntos[:-1], puntos[1:]):
        segmento = nx.shortest_path(grafo, origen, destino, weight=peso)
        ruta.extend(segmento if not ruta else segmento[1:])
    return ruta
