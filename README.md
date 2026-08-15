# Optimización de rutas de autobuses intersectoriales en la GAM

**Integrantes:** Siloé Campos, Jason Corrau, Gabriel Corrales y David Mora  
**Curso:** BCD5105 Modelado Matemático, Lead University  
**Profesor:** Jordy Alfaro Brenes  
**Período:** II Cuatrimestre de 2026

## Descripción

Este proyecto académico estudia caminos entre puntos de San José sobre una red vial dirigida. Compara un modelo que minimiza el tiempo teórico de flujo libre con otro que añade una penalización por la variabilidad supuesta de cada clase vial. A* bidireccional resuelve ambos problemas, Dijkstra verifica sus costos óptimos y una simulación Monte Carlo evalúa las rutas seleccionadas.

## Alcance

La investigación constituye una primera aproximación metodológica. Utiliza velocidades registradas en OpenStreetMap (OSM) o imputadas según la clase vial y trabaja con tres pares origen–destino definidos para el estudio. Los resultados representan tiempos teóricos de flujo libre sobre la red vial de San José.

Las rutas base son referencias reproducibles construidas mediante puntos intermedios. El análisis actual utiliza datos geográficos y demográficos agregados; las conclusiones deben interpretarse dentro de ese alcance.

## Modelos y evaluación

- **Modelo 1 — menor tiempo:** minimiza la suma de los tiempos estimados de los arcos.
- **Modelo 2 — ajustado por variabilidad:** minimiza el tiempo más una penalización aditiva derivada de una distribución lognormal por clase vial.
- **Control algorítmico:** Dijkstra resuelve la misma función de costo que A* y permite comprobar la optimalidad numérica.
- **Evaluación:** Monte Carlo resume media, desviación estándar, percentil 90 e índice de confiabilidad para rutas previamente seleccionadas.
- **Validación equivalente:** los modelos se comparan en los tres pares originales y en 30 pares adicionales reproducibles.
- **Sensibilidad:** se modifican $\lambda$, las velocidades imputadas y el número de réplicas.

## Fuentes de datos

| Fuente | Uso | Fecha incorporada | Condiciones |
|---|---|---|---|
| [OpenStreetMap](https://www.openstreetmap.org/copyright) | Red vial dirigida, paradas y destinos estratégicos de San José | 20 de julio de 2026 | ODbL y atribución a sus colaboradores |
| [INEC: Estimaciones de Población y Vivienda 2022](https://inec.cr/calendario/publicaciones-estadisticas/estimacion-poblacion-vivienda-2022-distribucion-nivel) | Población y límites distritales utilizados para aproximar densidad | 20 de julio de 2026 | Datos públicos agregados |

Los archivos necesarios para reproducir el análisis están incluidos en `data/raw/`. La licencia MIT del repositorio cubre el código; los datos de terceros conservan las condiciones de sus fuentes.

## Reproducción

Se requiere Python 3.10 o superior. Desde la raíz del repositorio, instale las dependencias:

```bash
python -m pip install -r requirements.txt
```

Ejecute completamente las libretas en este orden:

1. `notebooks/01_exploracion.ipynb`: prepara la red, las velocidades y los puntos de estudio.
2. `notebooks/02_modelos.ipynb`: ejecuta los dos modelos, selecciona $\lambda$ y exporta la comparación principal.
3. `notebooks/03_validacion.ipynb`: verifica los resultados exportados, amplía la muestra y ejecuta la sensibilidad.

Las libretas localizan la raíz del repositorio mediante rutas relativas. Cada etapa guarda en `data/processed/` los resultados que necesita la siguiente. La selección aleatoria utiliza `numpy.random.default_rng(2026)`, por lo que produce los mismos pares cuando se mantienen los datos y la versión del entorno.

## Resultados principales

- Con $\lambda=6.5$, el Modelo 2 cambia 1 de los 3 recorridos originales y 11 de los 30 adicionales.
- A* y Dijkstra coinciden para ambos costos en los 33 pares, con una diferencia máxima aproximada de $2.2\times10^{-14}$ minutos.
- En la muestra adicional, el Modelo 1 obtiene una media simulada de 6.37 minutos y un percentil 90 de 7.66; el Modelo 2 obtiene 6.45 y 7.76 minutos, respectivamente.
- El Modelo 1 se selecciona como resultado principal bajo los supuestos actuales. El Modelo 2 se conserva como análisis de sensibilidad a la variabilidad.
- Las conclusiones son estables ante penalizaciones moderadas y con 1 000 réplicas, pero son más sensibles a las velocidades imputadas.

## Productos reproducibles

| Archivo | Contenido |
|---|---|
| `data/processed/resultados_rutas.csv` | Modelo 1 y comparación con las rutas base |
| `data/processed/comparacion_modelos.csv` | Resultados de ambos modelos en los tres pares originales |
| `data/processed/validacion_modelos.csv` | Detalle de los 33 pares y control A*–Dijkstra |
| `data/processed/comparacion_validacion.csv` | Resumen agregado por muestra y modelo |
| `data/processed/sensibilidad_modelos.csv` | Resultados de los tres análisis de sensibilidad |
| `figuras/` | Siete figuras generadas por las libretas |

## Estructura

```text
data/
  raw/                 Datos originales incluidos
  processed/           Entradas preparadas y resultados reproducibles
docs/
  avance_1/            Fuentes originales del primer avance
  borradores/          Copias de trabajo del documento
  Ampliaciones_Entrega_Final.md
  Entrega_Final_Rutas_GAM.docx
figuras/               Figuras generadas por el análisis
notebooks/
  01_exploracion.ipynb
  02_modelos.ipynb
  03_validacion.ipynb
rutas_gam/              Paquete con datos, modelos, métricas y validación
scripts/
  generar_datos_osm.py  Reconstrucción de los datos geográficos
```

## Documentación

- [Ampliaciones teóricas y metodológicas](docs/Ampliaciones_Entrega_Final.md): guía para integrar la investigación actual en el documento final.
- [README del paquete](rutas_gam/README.md): responsabilidades de los módulos y forma de extender los modelos.

## Licencia

El código se publica bajo la [licencia MIT](LICENSE). Los datos de OSM requieren la atribución correspondiente y permanecen sujetos a ODbL.
