# Paquete `rutas_gam`

Este paquete reúne la lógica del proyecto para que el notebook se concentre en explicar el
problema, mostrar resultados e interpretar las gráficas. El código se separó en cuatro
módulos pequeños. No es necesario instalar el paquete: basta con conservar la carpeta
`rutas_gam` junto al notebook.

## 1. Estructura

- `datos.py`: carga la red, normaliza velocidades y prepara las paradas.
- `algoritmos.py`: contiene Dijkstra, A* bidireccional y la ruta base reproducible.
- `metricas.py`: calcula las métricas de éxito y el análisis de sensibilidad.
- `visualizaciones.py`: crea los mapas y gráficos del análisis.
- `__init__.py`: permite importar las funciones principales desde un solo lugar.

## 2. Preparación de los datos

La red vial se guarda en formato GraphML. Cada arco tiene una longitud en metros y puede
tener un límite de velocidad registrado en OpenStreetMap. `agregar_tiempos` convierte las
velocidades a km/h, imputa las faltantes según el tipo de vía y calcula:

```text
tiempo_min = longitud_m / velocidad_kph × 0.06
```

La tabla `paradas_importantes.csv` contiene las paradas utilizadas, la densidad poblacional
distrital atribuida y la cantidad de destinos estratégicos dentro de 500 metros. La columna
`fuente_densidad` permite rastrear el dato del INEC.

## 3. Importancia de las paradas

Las dos variables se normalizan entre cero y uno. Después se calcula:

```text
w_i = 0.6 × densidad_normalizada + 0.4 × destinos_normalizados
```

El índice no modifica el costo del camino. Se utiliza para identificar paradas relevantes y
elegir pares origen-destino útiles para un avance posterior.

Ejemplo:

```python
from rutas_gam import cargar_paradas, calcular_importancia

paradas = cargar_paradas("datos/paradas_importantes.csv")
paradas = calcular_importancia(paradas)
print(paradas[["nombre", "w_i"]].head())
```

## 4. A* bidireccional

La búsqueda utiliza dos fronteras. Una avanza desde el origen y otra desde el destino sobre
el grafo inverso. La heurística es la distancia geodésica dividida por la mayor velocidad de
la red. Esa estimación no supera el tiempo mínimo posible y, por ello, es admisible.

```python
from rutas_gam import astar_bidireccional

resultado = astar_bidireccional(grafo, nodo_origen, nodo_destino)
print(resultado["costo"])
print(resultado["nodos_explorados"])
```

Dijkstra usa exactamente los mismos pesos y sirve como control. Los dos algoritmos deben
obtener el mismo costo óptimo, aunque exploren cantidades distintas de nodos.

## 5. Ruta base

`ruta_por_puntos` une una secuencia documentada de nodos utilizando distancia. Esta ruta es
una referencia reproducible para calcular mejoras; no se presenta como una ruta oficial de
autobús.

## 6. Métricas de éxito

- **RT:** reducción porcentual del tiempo respecto a la ruta base.
- **RV:** reducción porcentual de la desviación estándar simulada.
- **IC:** porcentaje de escenarios donde el tiempo no supera en 15 % su valor esperado.
- **NE:** nodos explorados por A* bidireccional.

La simulación no cambia la ruta elegida. Solo estudia cómo podrían variar sus tiempos bajo
escenarios reproducibles. Se usa una distribución lognormal con variación moderada según la
clase vial y una semilla fija.

## 7. Limitaciones

- Los tiempos del modelo representan flujo libre, no registros históricos de 6:00–8:00 a. m.
- La densidad se asigna por distrito y no describe cambios dentro de cada distrito.
- La cantidad de destinos depende de la cobertura de OpenStreetMap.
- La ruta base es metodológica y no sustituye datos oficiales del recorrido de autobuses.

## 8. Extensiones posibles

En avances posteriores se pueden reemplazar los tiempos estimados por observaciones reales,
incorporar perfiles de hora pico, mejorar la densidad con unidades geográficas más pequeñas
y utilizar recorridos oficiales como referencia.
