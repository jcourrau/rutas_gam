# Optimización de rutas de transporte público en el GAM mediante teoría de grafos

**Curso:** BCD5105 Modelado Matemático — Lead University, II Cuatrimestre 2026
**Carril temático:** #3, Optimización de rutas de transporte público
**Integrantes:** Siloé Campos, Jason Corrau, Gabriel Corrales, David Mora
**Profesor:** Jordy Alfaro Brenes

## Descripción del problema

El proyecto calcula rutas de menor tiempo entre pares de puntos de la red vial de San José
(Modelo 1: A* bidireccional, validado con Dijkstra) y evalúa qué tan confiables son esas
rutas ante variaciones aleatorias del tiempo de viaje (Modelo 2: simulación Monte Carlo). Es
una primera aproximación reproducible al problema de movilidad de la Gran Área Metropolitana,
no un rediseño del sistema de autobuses ni una sustitución de datos operativos oficiales.

## Datos

| Fuente | Contenido | Descarga |
|---|---|---|
| OpenStreetMap (OSM), consulta 19-20 de julio de 2026 | Red vial dirigida de San José y paradas/destinos estratégicos | `data/raw/red_san_jose.graphml`, generado con `scripts/generar_datos_osm.py` |
| INEC, Estimaciones de Población y Vivienda 2022 (publicado 9 nov. 2023) | Densidad poblacional por distrito | `data/raw/poblacion_distritos_costa_rica_2022.csv` y `data/raw/reResultadosEstimacionPoblacionVivienda2022_3.xlsx` |

Los datos de OSM se distribuyen bajo licencia ODbL (Open Database License): permite su
redistribución y reutilización citando la fuente, condición que se cumple en el documento y en
este README. Los datos del INEC son de acceso público. Ninguno de los dos conjuntos contiene
información personal o reidentificable: son agregados a nivel de distrito o infraestructura
pública.

## Resultados principales

A* bidireccional y Dijkstra coincidieron en el costo óptimo en los 3 pares del estudio y en 30
pares adicionales generados para la validación extendida (100% de coincidencia). Las rutas
óptimas redujeron el tiempo estimado en 14.2% y la variabilidad simulada en 13.7% en promedio
frente a una ruta base de referencia. El modelo estocástico (Monte Carlo) muestra que el modelo
determinista subestima el tiempo real posible en ~46%-49% de los escenarios, lo que justifica
reportar ambos modelos en lugar de solo el determinista.

## Estructura de carpetas

```
rutas_gam/
  README.md
  LICENSE
  requirements.txt
  data/
    raw/            datos originales sin modificar (OSM, INEC)
    processed/       paradas priorizadas, resultados y tablas derivadas
  notebooks/
    01_exploracion.ipynb   carga de datos y análisis exploratorio
    02_modelos.ipynb       Modelo 1 (A*/Dijkstra) y Modelo 2 (Monte Carlo)
    03_validacion.ipynb    validación extendida, comparación de modelos y sensibilidad
  src/rutas_gam/     paquete con la lógica reutilizable (datos, algoritmos, métricas, visualizaciones, validación)
  scripts/           script de generación de datos desde OSM (opcional, no requerido para reproducir)
  figuras/           figuras generadas por los notebooks
  docs/              documento final en PDF y el avance 1 (referencia histórica)
```

## Cómo reproducir

1. Clonar el repositorio.
2. Instalar dependencias: `pip install -r requirements.txt`
3. Abrir en Google Colab (o Jupyter local) y ejecutar en orden, cada uno de principio a fin:
   `notebooks/01_exploracion.ipynb` → `notebooks/02_modelos.ipynb` → `notebooks/03_validacion.ipynb`.
   Cada notebook carga sus propios datos desde `data/` y no depende del estado en memoria de
   los anteriores.
4. Las semillas aleatorias están fijas y declaradas en el código (42 + número de par para las
   simulaciones por ruta; 2026 para el muestreo de pares de validación).
5. No es necesario ejecutar `scripts/generar_datos_osm.py`: sus salidas ya están en
   `data/processed/`. Ese script solo se documenta para trazabilidad y requiere conexión a
   internet (consulta en vivo a OSM).

## Nota sobre uso de asistentes de IA

Se declara en el documento final, sección correspondiente.
