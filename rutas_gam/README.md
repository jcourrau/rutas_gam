# Paquete `rutas_gam`

`rutas_gam` concentra la lógica reutilizable del proyecto para que las libretas se enfoquen en explicar la investigación, ejecutar cada etapa y presentar resultados. El paquete separa la preparación de datos, los algoritmos, las funciones de costo, la simulación, la validación y la presentación.

## Modelos implementados

- **Menor tiempo:** utiliza el atributo de arco `travel_time_min`.
- **Ajustado por variabilidad:** utiliza `risk_adjusted_time_min`, definido como el tiempo del arco más $\lambda$ veces su desviación estándar lognormal estimada.

A* bidireccional resuelve cada función de costo. Dijkstra emplea exactamente el mismo peso y funciona como control de optimalidad. La simulación Monte Carlo se aplica después de seleccionar las rutas y no interviene en la búsqueda del camino.

## Módulos

| Módulo | Responsabilidad |
|---|---|
| `datos.py` | Cargar la red y las tablas, normalizar o imputar velocidades y calcular los costos de arco |
| `algoritmos.py` | Resolver caminos con A* bidireccional, Dijkstra y puntos intermedios |
| `modelos.py` | Declarar modelos, ejecutarlos de manera uniforme y comparar sus rutas |
| `metricas.py` | Resumir rutas, simular tiempos y calcular métricas Monte Carlo |
| `flujo.py` | Orquestar las etapas principales utilizadas por exploración y modelado |
| `validacion.py` | Preparar pares adicionales, verificar resultados y ejecutar sensibilidad |
| `presentacion.py` | Construir tablas compactas con nombres legibles |
| `visualizaciones.py` | Generar mapas, histogramas y gráficos comparativos |
| `__init__.py` | Exponer la interfaz pública utilizada por las libretas |

## Flujo principal

La interfaz de alto nivel permite mantener separadas la selección determinista y la evaluación estocástica. El siguiente ejemplo supone que `casos` ya contiene los pares con `nombre`, `origen` y `destino`:

```python
import rutas_gam as rg

datos = rg.cargar_datos_estudio(
    "data/raw/red_san_jose.graphml",
    "data/processed/paradas_importantes.csv",
    "data/processed/puntos_estudio.csv",
)

resultado_1 = rg.ejecutar_modelo_menor_tiempo(datos.grafo, casos)
ejecucion_2 = rg.ejecutar_modelo_ajustado(
    datos.grafo,
    casos,
    lambda_riesgo=6.5,
)

comparacion = rg.comparar_y_simular_modelos(
    ejecucion_2.grafo,
    [resultado_1, ejecucion_2.resultado],
    repeticiones=1000,
    semilla=2026,
)
```

`comparar_y_simular_modelos` conserva las rutas seleccionadas y las evalúa con el mismo diseño Monte Carlo. La semilla y los supuestos son comunes y reproducibles; los multiplicadores locales se generan a lo largo de cada recorrido y no representan una observación simultánea de tráfico para toda la red.

## Validación y sensibilidad

La validación ampliada también dispone de operaciones de alto nivel. Las rutas de archivos, las configuraciones nominales y los valores de $\lambda$ se proporcionan desde la libreta:

```python
preparacion = rg.preparar_validacion_ampliada(
    ruta_grafo,
    ruta_paradas,
    ruta_puntos,
    ruta_comparacion,
    configuraciones,
    valores_lambda,
    cantidad_adicional=30,
    semilla=2026,
)

resultado = rg.ejecutar_validacion_ampliada(
    preparacion,
    repeticiones=1000,
    semilla=2026,
)
```

`ResultadoValidacion` contiene:

- `tabla`: detalle de los dos modelos para todos los pares;
- `rutas`: recorridos seleccionados;
- `resumen_muestras`: cantidad de pares y rutas diferentes;
- `comparacion_modelos`: métricas agregadas por muestra y modelo.

Las funciones `analizar_sensibilidad_lambda`, `analizar_sensibilidad_velocidades` y `analizar_sensibilidad_replicas` devuelven un objeto con el detalle y el resumen de cada supuesto. `exportar_resultados_validacion` consolida y guarda los CSV finales.

## Incorporar otro modelo

Un modelo de ruta se define mediante un nombre y el atributo de arco que representa su función de costo:

```python
modelo_3 = rg.ModeloRuta(
    nombre="Nombre del modelo",
    peso="nombre_del_peso",
)
resultado_3 = rg.ejecutar_modelo(grafo, casos, modelo_3)
```

Antes de ejecutarlo, todos los arcos deben contener el atributo indicado en `peso`. Ese atributo debe representar costos positivos y aditivos para mantener la formulación de camino mínimo.

`rg.comparar_resultados_modelos` recibe dos o más resultados y utiliza el primero como referencia para identificar cambios de ruta:

```python
tabla, rutas = rg.comparar_resultados_modelos([
    resultado_1,
    ejecucion_2.resultado,
    resultado_3,
])
```

La heurística temporal predeterminada debe ser una cota inferior válida del nuevo costo. Cuando esa propiedad no pueda garantizarse, el modelo puede declararse con `escala_heuristica=0.0`; así la búsqueda conserva la optimalidad sin utilizar la estimación temporal.

## Convenciones

- Las semillas se crean con `numpy.random.default_rng`; el valor común del proyecto es `2026`.
- Los tiempos de arco se expresan en minutos, las distancias resumidas en kilómetros y las velocidades en kilómetros por hora.
- Las funciones públicas devuelven tablas o dataclasses y evitan depender del estado de una libreta.
- Las figuras se guardan únicamente cuando se proporciona una ruta de salida.
- El paquete trabaja con archivos locales del repositorio; la reconstrucción desde las fuentes externas corresponde a `scripts/generar_datos_osm.py`.

## Dependencias

Las dependencias se instalan desde la raíz del repositorio:

```bash
python -m pip install -r requirements.txt
```

El paquete está diseñado para importarse desde la raíz del proyecto:

```python
import rutas_gam as rg
```
