"""Genera la tabla fija de paradas y destinos estratégicos desde OSM."""

from pathlib import Path
import unicodedata

import geopandas as gpd
import osmnx as ox
import pandas as pd


RAIZ = Path(__file__).resolve().parent
RUTA_POBLACION = RAIZ.parent / "data" / "raw" / "poblacion_distritos_costa_rica_2022.csv"
RUTA_SALIDA = RAIZ.parent / "data" / "processed" / "paradas_importantes.csv"
CAJA = (-84.120, 9.962, -84.038, 9.905)


def punto_representativo(geometria):
    """Devuelve un punto contenido en la geometría recibida."""
    return geometria if geometria.geom_type == "Point" else geometria.representative_point()


def normalizar_nombre(nombre):
    """Normaliza un nombre para enlazar las fuentes INEC y OSM."""
    texto = unicodedata.normalize("NFKD", str(nombre))
    return (
        "".join(letra for letra in texto if not unicodedata.combining(letra))
        .casefold()
        .strip()
    )


def cargar_distritos():
    """Carga las densidades del CSV y las vincula con los límites de OSM."""
    poblacion = pd.read_csv(RUTA_POBLACION).rename(
        columns={"Distrito": "distrito", "Densidad poblacional": "densidad_poblacional"}
    )
    poblacion["clave_provincia"] = poblacion["Provincia"].map(normalizar_nombre)
    poblacion["clave_canton"] = poblacion["Cantón"].map(normalizar_nombre)
    poblacion["clave_distrito"] = poblacion["distrito"].map(normalizar_nombre)

    limites = ox.features.features_from_bbox(
        CAJA, {"boundary": "administrative", "admin_level": "8"}
    )
    limites = limites[limites.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
    limites = limites[limites["boundary"].eq("administrative")].copy()
    distritos = limites[limites["admin_level"].astype(str).eq("8")].copy()
    cantones = limites[limites["admin_level"].astype(str).eq("6")].copy()
    provincias = limites[limites["admin_level"].astype(str).eq("4")].copy()

    distritos = gpd.GeoDataFrame(distritos, geometry="geometry", crs=limites.crs).to_crs(5367)
    cantones = gpd.GeoDataFrame(cantones, geometry="geometry", crs=limites.crs).to_crs(5367)
    provincias = gpd.GeoDataFrame(provincias, geometry="geometry", crs=limites.crs).to_crs(5367)

    distritos["clave_distrito"] = distritos["name"].map(normalizar_nombre)
    puntos_distrito = distritos.geometry.apply(punto_representativo)
    distritos["clave_canton"] = puntos_distrito.apply(
        lambda punto: normalizar_nombre(asignar_distrito(punto, cantones)["name"])
    )
    distritos["clave_provincia"] = puntos_distrito.apply(
        lambda punto: normalizar_nombre(asignar_distrito(punto, provincias)["name"])
    )
    distritos = distritos.merge(
        poblacion[[
            "clave_provincia", "clave_canton", "clave_distrito",
            "distrito", "densidad_poblacional",
        ]],
        on=["clave_provincia", "clave_canton", "clave_distrito"],
        how="inner",
    )
    if distritos.empty:
        raise RuntimeError("No fue posible vincular los distritos de OSM con el archivo de población.")
    return gpd.GeoDataFrame(distritos, geometry="geometry", crs=5367)


def asignar_distrito(punto, distritos):
    """Busca el distrito que contiene el punto o, en su defecto, el más cercano."""
    contiene = distritos[distritos.geometry.covers(punto)]
    if not contiene.empty:
        return contiene.iloc[0]
    return distritos.loc[distritos.geometry.distance(punto).idxmin()]


def main():
    """Consulta OSM y guarda las veinte paradas de mayor importancia."""
    distritos = cargar_distritos()
    paradas = ox.features.features_from_bbox(
        CAJA, {"highway": "bus_stop", "public_transport": "platform"}
    )
    destinos = ox.features.features_from_bbox(
        CAJA,
        {
            "amenity": [
                "hospital", "clinic", "school", "college", "university",
                "townhall", "courthouse", "marketplace",
            ]
        },
    )
    paradas = paradas[~paradas.geometry.is_empty].copy().to_crs(5367)
    destinos = destinos[~destinos.geometry.is_empty].copy().to_crs(5367)
    destinos["geometry"] = destinos.geometry.apply(punto_representativo)
    registros = []
    for indice, fila in paradas.iterrows():
        punto = punto_representativo(fila.geometry)
        cercanos = destinos.geometry.distance(punto).le(500).sum()
        wgs84 = gpd.GeoSeries([punto], crs=5367).to_crs(4326).iloc[0]
        distrito = asignar_distrito(punto, distritos)
        nombre = fila.get("name")
        if not isinstance(nombre, str) or not nombre.strip():
            nombre = f"Parada OSM {indice[-1] if isinstance(indice, tuple) else indice}"
        registros.append({
            "osm_id": indice[-1] if isinstance(indice, tuple) else indice,
            "nombre": nombre,
            "latitud": wgs84.y,
            "longitud": wgs84.x,
            "distrito": distrito["distrito"],
            "densidad_poblacional": distrito["densidad_poblacional"],
            "destinos_estrategicos": int(cercanos),
            "fuente_densidad": "INEC, estimaciones distritales 2022",
            "fuente_geografica": "OpenStreetMap, consulta 2026-07-20",
        })
    tabla = pd.DataFrame(registros).drop_duplicates(subset=["latitud", "longitud"])
    densidad = (tabla["densidad_poblacional"] - tabla["densidad_poblacional"].min())
    densidad /= max(tabla["densidad_poblacional"].max() - tabla["densidad_poblacional"].min(), 1)
    destinos_norm = tabla["destinos_estrategicos"] - tabla["destinos_estrategicos"].min()
    destinos_norm /= max(tabla["destinos_estrategicos"].max() - tabla["destinos_estrategicos"].min(), 1)
    tabla["w_i_preliminar"] = 0.6 * densidad + 0.4 * destinos_norm
    tabla = tabla.sort_values("w_i_preliminar", ascending=False).head(20)
    ruta = RUTA_SALIDA
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(ruta, index=False)
    print(tabla[["nombre", "distrito", "destinos_estrategicos", "w_i_preliminar"]])


if __name__ == "__main__":
    main()
