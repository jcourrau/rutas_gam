# Ampliaciones teóricas, metodológicas y resultados de la entrega final

## Propósito del documento

Este documento resume las correcciones y ampliaciones que transforman el documento `Avance 1.pdf` en la entrega final del proyecto **Optimización de rutas de transporte público en la GAM mediante teoría de grafos**. Su propósito es servir como guía para actualizar manualmente el documento final: reúne el alcance realmente implementado, las formulaciones matemáticas vigentes, la metodología, los resultados obtenidos, la validación, la sensibilidad y las limitaciones que deben aparecer en la versión entregable.

La entrega final conserva el problema, los datos y las principales limitaciones del Avance 1. La ampliación central consiste en pasar de una única regla de decisión —escoger el camino de menor tiempo estimado— a comparar dos modelos de optimización:

1. un modelo determinista de camino mínimo;
2. un modelo de camino mínimo cuyo costo incorpora una penalización por variabilidad.

Los dos modelos se evaluaron mediante el mismo diseño Monte Carlo. Dijkstra se mantuvo como mecanismo de validación algorítmica y no se presenta como un modelo diferente.

## Resumen ejecutivo

La entrega final conserva la red vial dirigida de San José, los datos de OSM e INEC y los tres pares origen–destino. La ampliación incorpora un segundo criterio de decisión, una validación sobre 30 pares adicionales y tres análisis formales de sensibilidad.

| Resultado central | Evidencia obtenida |
|---|---|
| Valor exploratorio seleccionado | $\lambda=6.5$, primer valor positivo probado que modifica una ruta original |
| Validación algorítmica | A* y Dijkstra coinciden en ambos costos para los 33 pares |
| Cambios de ruta | 1 de 3 pares originales y 11 de 30 pares adicionales |
| Comparación en la muestra adicional | Media de 6.37 min para el Modelo 1 y 6.45 min para el Modelo 2 |
| Percentil 90 en la muestra adicional | 7.66 min para el Modelo 1 y 7.76 min para el Modelo 2 |
| Modelo seleccionado | Modelo 1, por sus menores tiempos y confiabilidad prácticamente equivalente |
| Principal fuente de sensibilidad | Velocidades imputadas en los arcos sin `maxspeed` |

El Modelo 2 aporta una comparación metodológica útil, pero la penalización empleada no genera una mejora cuantitativa bajo los supuestos actuales. Esta conclusión corresponde a tiempos teóricos de flujo libre y sirve como punto de partida para una etapa posterior con observaciones reales.

## 1. Alcance de la investigación

El proyecto continúa siendo una investigación inicial sobre movilidad realizada a partir de una red vial dirigida de San José. La red se obtuvo de OpenStreetMap (OSM) y se complementó con información distrital del Instituto Nacional de Estadística y Censos (INEC) y con destinos estratégicos registrados en OSM.

Los tiempos utilizados representan condiciones aproximadas de **flujo libre**. Cuando OSM contiene el atributo `maxspeed`, se emplea ese límite de velocidad. Cuando no se encuentra disponible, se imputa una velocidad de acuerdo con la clase vial indicada por `highway`, tomando como referencia los límites generales de la Ley de Tránsito de Costa Rica.

Se conservan los tres pares origen–destino definidos en el Avance 1:

- Estadio Oeste–San Pedro;
- Cuatro Reinas–Paso Ancho;
- Hatillo–Curridabat.

El alcance no incluye recorridos oficiales de autobuses, datos operativos de ARESEP, observaciones históricas de tráfico, demanda de pasajeros, horarios, frecuencias, tiempos de espera ni transbordos. Por ello, los resultados no describen el funcionamiento real del sistema de transporte público y no deben interpretarse como recomendaciones operativas definitivas.

### 1.1 Correcciones de alcance respecto al Avance 1

El Avance 1 formuló varias variables como si existieran tiempos históricos de hora pico, recorridos actuales de autobús y estimaciones empíricas de variabilidad. Esos datos no forman parte del conjunto disponible. La entrega final debe corregir esas afirmaciones y describir únicamente lo que fue implementado:

| Formulación o expectativa del Avance 1 | Corrección aplicada en la entrega final |
|---|---|
| Red de transporte público de toda la GAM | Red vial dirigida de San José utilizada como primera aproximación espacial |
| Tiempos históricos entre las 6:00 y las 8:00 a. m. | Tiempos teóricos de flujo libre calculados con longitud y velocidad |
| Desviaciones estándar estimadas con observaciones de tráfico | Dispersiones lognormales supuestas según la clase vial |
| Datos de MIDEPLAN y tiempos históricos como insumos efectivos | Datos utilizados: OSM e INEC; no se incorporaron registros históricos ni un conjunto adicional de MIDEPLAN |
| Costo $t_{ij}+\lambda\sigma_{ij}+\gamma(1/w_j)$ | El índice $w_j$ se usa para priorizar puntos, no para alterar artificialmente el costo de una ruta |
| Comparación con la ruta actualmente utilizada por autobuses | Comparación con una ruta base reproducible construida mediante un punto intermedio |
| Recomendaciones para modificar rutas oficiales | Resultados exploratorios que no deben sustentar decisiones operativas sin datos reales |
| Restricciones explícitas de flujo y eliminación de subtours | El camino factible se resuelve directamente sobre el grafo dirigido; con costos positivos, un ciclo solo aumenta el costo |

La formulación original de tiempo más variabilidad no se descarta por completo. Se convierte en el segundo modelo, pero la variabilidad deja de presentarse como una estimación empírica y se deriva de los supuestos lognormales utilizados en la simulación.

## 2. Base metodológica conservada del Avance 1

### 2.1 Representación de la red

La red vial se representa mediante un grafo dirigido:

$$
G=(V,E),
$$

donde $V$ es el conjunto de nodos y $E$ es el conjunto de arcos dirigidos. Los nodos representan intersecciones o puntos conectados con la red, mientras que cada arco $(i,j)$ representa un tramo transitable desde el nodo $i$ hasta el nodo $j$. El carácter dirigido permite respetar calles de un solo sentido.

Cada arco contiene una longitud $d_{ij}$, expresada en metros, y una velocidad $v_{ij}$, expresada en kilómetros por hora. El tiempo aproximado de flujo libre se calcula mediante:

$$
t_{ij}
=
\frac{d_{ij}}{v_{ij}}
\left(\frac{60\ \text{min}}{1000\ \text{m}}\right)
=
\frac{d_{ij}}{v_{ij}}(0.06).
$$

Este tiempo es el peso principal del arco. No representa un tiempo observado de viaje, sino una aproximación construida con la longitud de la vía y su velocidad registrada o imputada.

### 2.2 Priorización de paradas

El Avance 1 combina dos variables para identificar paradas relevantes:

- $DP_i$: densidad poblacional del distrito asociado con la parada $i$;
- $DE_i$: cantidad de destinos estratégicos registrados dentro de 500 metros.

Después de normalizar ambas variables entre cero y uno, se calcula:

$$
w_i
=
0.6DP_i^{\mathrm{norm}}
+
0.4DE_i^{\mathrm{norm}}.
$$

El índice $w_i$ se utiliza exclusivamente para priorizar paradas. No forma parte del costo de los arcos y no concede una ventaja artificial a una parada durante la búsqueda de una ruta.

### 2.3 Modelo 1: camino de menor tiempo

Sea $P_{OD}$ el conjunto de caminos dirigidos factibles entre un origen $O$ y un destino $D$. El primer modelo asigna a cada arco el costo:

$$
c_{ij}^{(1)}=t_{ij}.
$$

La ruta seleccionada es:

$$
R_1^*
=
\arg\min_{R\in P_{OD}}
\sum_{(i,j)\in R}t_{ij}.
$$

Este modelo responde la pregunta: **¿cuál es el camino con menor tiempo estimado de flujo libre?** Se trata de un modelo determinista porque, una vez definidos los tiempos de los arcos, cada ruta tiene un único costo fijo.

La búsqueda se realiza con A* bidireccional. Para orientar la exploración se usa la heurística temporal:

$$
h(n)
=
\frac{\operatorname{dist}_{\mathrm{geo}}(n,D)}{v_{\max}}(0.06),
$$

donde $\operatorname{dist}_{\mathrm{geo}}(n,D)$ es la distancia geodésica entre el nodo actual y el destino, y $v_{\max}$ es la mayor velocidad asignada en la red. La distancia en línea recta no supera la distancia que debe recorrerse sobre la red y dividirla entre la mayor velocidad posible produce una cota inferior del tiempo restante. Por esta razón, la heurística es admisible.

Dijkstra utiliza los mismos costos, pero no emplea una heurística. Su función en el proyecto es comprobar que A* obtiene el mismo costo óptimo. A* y Dijkstra no se consideran modelos diferentes porque parten de la misma función objetivo y de los mismos supuestos; son dos procedimientos para resolver el mismo problema matemático.

### 2.4 Ruta base y métricas originales

Para cada par también se conserva una ruta base reproducible que pasa por un punto intermedio y minimiza la distancia de cada segmento. Esta referencia permite calcular mejoras, pero no representa un recorrido oficial de autobús.

Las métricas definidas en el Avance 1 son:

**Reducción de tiempo:**

$$
RT
=
\frac{T_{\mathrm{base}}-T_{A^*}}
{T_{\mathrm{base}}}
\times100.
$$

**Reducción de variabilidad:**

$$
RV
=
\left(1-\frac{s_{A^*}}{s_{\mathrm{base}}}\right)
\times100.
$$

**Índice de confiabilidad:**

$$
IC
=
\frac{1}{S}
\sum_{s=1}^{S}
\mathbb{I}
\left(
T_R^{(s)}\leq1.15\overline{T}_R
\right)
\times100.
$$

**Nodos explorados:**

$$
NE
=
\left|C_{\mathrm{origen}}\cup C_{\mathrm{destino}}\right|.
$$

$RT$ compara la ruta seleccionada con la referencia base; $RV$ e $IC$ describen el comportamiento de los escenarios simulados; y $NE$ mide el espacio de búsqueda explorado por el algoritmo.

Las referencias se reconstruyeron en la entrega final y produjeron los siguientes resultados para el Modelo 1:

| Par | Tiempo Modelo 1 | Tiempo de ruta base | $RT$ | $RV$ | $IC$ |
|---|---:|---:|---:|---:|---:|
| Estadio Oeste → San Pedro | 9.96 min | 11.11 min | 10.35 % | 9.12 % | 83.80 % |
| Cuatro Reinas → Paso Ancho | 8.22 min | 8.59 min | 4.32 % | 3.86 % | 82.90 % |
| Hatillo → Curridabat | 8.98 min | 12.45 min | 27.86 % | 27.82 % | 84.40 % |
| **Promedio** | — | — | **14.18 %** | **13.60 %** | **83.70 %** |

Estas reducciones se calculan contra referencias metodológicas, no contra rutas oficiales. No deben redactarse como mejoras comprobadas del sistema de autobuses.

## 3. Segundo modelo: camino mínimo ajustado por variabilidad

### 3.1 Motivación

El Modelo 1 considera únicamente el tiempo central estimado. Dos arcos con el mismo valor de $t_{ij}$ reciben el mismo costo, aunque uno pertenezca a una clase vial a la que se ha asignado mayor variabilidad. El segundo modelo incorpora esa diferencia y responde otra pregunta: **¿qué camino ofrece el mejor equilibrio entre tiempo estimado y variabilidad supuesta?**

Este cambio no consiste en sustituir A* por otro algoritmo. Consiste en modificar la función matemática que define qué se entiende por una ruta preferible.

### 3.2 Distribución del tiempo de un arco

El Avance 1 supone que, en el escenario $s$, el tiempo de un arco cambia mediante un multiplicador lognormal:

$$
\tau_{ij}^{(s)}
=
t_{ij}
\exp\left(
\sigma_{\mathrm{vía}}Z_{ij}^{(s)}
-
\frac{\sigma_{\mathrm{vía}}^2}{2}
\right),
\qquad
Z_{ij}^{(s)}\sim\mathcal{N}(0,1).
$$

El parámetro $\sigma_{\mathrm{vía}}$ depende de la clase vial. Los supuestos utilizados son:

| Clase vial | $\sigma_{\mathrm{vía}}$ |
|---|---:|
| Autopista (`motorway`) | 0.10 |
| Troncal (`trunk`) | 0.12 |
| Primaria (`primary`) | 0.18 |
| Secundaria (`secondary`) | 0.20 |
| Terciaria (`tertiary`) | 0.22 |
| Residencial (`residential`) | 0.16 |
| Servicio (`service`) | 0.14 |
| Otras clases | 0.18 |

El término $-\sigma_{\mathrm{vía}}^2/2$ corrige la media del multiplicador. De esta forma:

$$
\mathbb{E}\left[
\exp\left(
\sigma_{\mathrm{vía}}Z
-
\frac{\sigma_{\mathrm{vía}}^2}{2}
\right)
\right]
=1,
$$

y, por tanto:

$$
\mathbb{E}[\tau_{ij}]=t_{ij}.
$$

La desviación estándar correspondiente es:

$$
s_{ij}
=
t_{ij}
\sqrt{e^{\sigma_{\mathrm{vía}}^2}-1}.
$$

Así, $t_{ij}$ representa el tiempo central del arco y $s_{ij}$ representa la magnitud de su variabilidad bajo los supuestos de la simulación.

### 3.3 Función de costo ajustada por variabilidad

El segundo modelo asigna a cada arco el costo:

$$
c_{ij}^{(2)}
=
t_{ij}+\lambda s_{ij},
$$

o, de manera equivalente:

$$
c_{ij}^{(2)}
=
t_{ij}
\left[
1+\lambda
\sqrt{e^{\sigma_{\mathrm{vía}}^2}-1}
\right].
$$

La ruta seleccionada por el segundo modelo es:

$$
R_2^*
=
\arg\min_{R\in P_{OD}}
\sum_{(i,j)\in R}c_{ij}^{(2)}.
$$

Los componentes de esta función tienen la siguiente interpretación:

- $t_{ij}$ es el tiempo estimado de flujo libre;
- $s_{ij}$ es la desviación estándar derivada de la dispersión supuesta para la clase vial;
- $\lambda$ indica cuánto se penaliza la variabilidad;
- $\lambda=0$ elimina la penalización y reproduce exactamente el Modelo 1;
- $\lambda=1$ añade al costo de cada arco una desviación estándar derivada;
- valores mayores de $\lambda$ favorecen recorridos más conservadores, aunque puedan tener un tiempo central ligeramente mayor.

El Modelo 2 se ejecuta primero con $\lambda=1$, que representa una penalización equivalente a una desviación estándar derivada por arco. Después se comparan valores entre $0$ y $10$ con incrementos de $0.5$ mediante resultados deterministas promedio. El criterio consiste en utilizar el menor valor positivo probado que modifique al menos una de las tres rutas originales. Los recorridos se mantienen hasta $\lambda=6$; con $\lambda=6.5$ cambia un par y el tiempo determinista promedio apenas pasa de $9.05$ a $9.06$ minutos. Desde $\lambda=9.5$ cambian dos rutas y el promedio aumenta a $9.84$ minutos. Por esta razón se utiliza $\lambda=6.5$ para el Modelo 2 y para su evaluación posterior.

Esta selección permite estudiar una decisión diferente sin adoptar el mayor valor evaluado. No constituye una calibración empírica del riesgo: depende de las dispersiones supuestas por clase vial y se reporta como una decisión metodológica exploratoria.

Esta formulación no calcula un cuantil exacto del tiempo total de la ruta ni resuelve un problema de peor caso. La suma de las desviaciones de los arcos tampoco equivale, en general, a la desviación estándar exacta de la suma. Se utiliza como una aproximación conservadora, separable y fácil de interpretar: penaliza de forma acumulativa los tramos asociados con mayor incertidumbre.

La propiedad aditiva es importante porque conserva la estructura de camino mínimo. Además, para $\lambda\geq0$ se cumple:

$$
c_{ij}^{(2)}\geq t_{ij}>0.
$$

Por ello, la heurística temporal del Modelo 1 continúa siendo una cota inferior válida para el costo ajustado por variabilidad. A* bidireccional puede resolver ambos modelos y Dijkstra puede verificar el óptimo utilizando, en cada caso, el costo correspondiente.

## 4. Justificación de la elección del segundo modelo

El camino mínimo ajustado por variabilidad se eligió por las siguientes razones:

1. **Continúa el trabajo del Avance 1.** La formulación parte de los tiempos, las clases viales y las distribuciones lognormales ya definidas. No cambia el problema de investigación ni requiere construir un conjunto de datos nuevo.
2. **Introduce un supuesto diferente.** El Modelo 1 supone que basta con minimizar el tiempo central. El Modelo 2 supone que la variabilidad también es relevante y que una ruta ligeramente más lenta puede ser preferible si evita tramos considerados más inciertos.
3. **Produce una decisión comparable.** Ambos modelos devuelven una ruta entre el mismo origen y destino, pero lo hacen con funciones objetivo distintas.
4. **Permanece dentro de las limitaciones actuales.** La penalización utiliza supuestos explícitos de simulación; no pretende presentarlos como observaciones reales de congestión.
5. **Mantiene una formulación sencilla.** El costo continúa siendo positivo y aditivo, por lo que no es necesario cambiar el problema a una formulación de diseño de redes, programación entera o metaheurísticas.
6. **Permite analizar estabilidad.** La comparación determina si las rutas de menor tiempo permanecen seleccionadas al incorporar variabilidad o si el nuevo criterio modifica los recorridos.

La selección de una ruta distinta no se considera automáticamente una mejora. Se verifica si el aumento del tiempo central se acompaña de una reducción en la dispersión o en los tiempos simulados desfavorables. De igual manera, cuando ambos modelos eligen la misma ruta, el resultado se interpreta como estabilidad de la decisión bajo la penalización estudiada.

## 5. Metodología de la entrega final

### 5.1 Preparación común

Los dos modelos utilizan exactamente la misma red, los mismos sentidos de circulación, las mismas longitudes, las mismas velocidades y los mismos pares origen–destino. Esta condición evita atribuir a la función objetivo diferencias producidas por cambios en los datos.

La metodología se ejecuta en este orden:

1. Cargar la extracción fija de la red vial de San José.
2. Normalizar las velocidades disponibles en OSM.
3. Imputar las velocidades faltantes según la clase vial.
4. Calcular $t_{ij}$ para cada arco.
5. Conectar los puntos de estudio con el nodo vial más cercano.
6. Resolver el Modelo 1 minimizando $t_{ij}$.
7. Ejecutar inicialmente el Modelo 2 con $\lambda=1$.
8. Comparar resultados deterministas para valores entre $0$ y $10$ con incrementos de $0.5$.
9. Seleccionar $\lambda=6.5$ como el menor valor probado que modifica una ruta.
10. Volver a resolver el Modelo 2 con el valor seleccionado.
11. Verificar ambas soluciones mediante Dijkstra.
12. Evaluar las rutas resultantes con el mismo diseño Monte Carlo.

### 5.2 Casos de estudio y casos adicionales

Los tres pares originales se mantienen para asegurar continuidad con el Avance 1. Además, se seleccionan 30 pares adicionales entre los nodos de la red mediante:

$$
\operatorname{default\_rng}(2026).
$$

El valor `2026` funciona como semilla reproducible: al conservar los mismos datos y entorno, la selección aleatoria genera los mismos pares en cada ejecución.

Se excluyen pares sin un camino dirigido factible y los tres casos originales. La muestra adicional no sustituye los casos del avance ni se utiliza para escoger ejemplos favorables. Su finalidad es comprobar si los resultados observados se mantienen más allá de tres recorridos seleccionados manualmente.

Estos 30 casos son pares sintéticos de nodos viales. No representan demanda, viajes observados ni pares de paradas oficiales. En consecuencia, fortalecen la comprobación algorítmica y la comparación interna, pero no constituyen una muestra representativa del transporte público.

### 5.3 Evaluación mediante Monte Carlo

Después de obtener las rutas, ambas permanecen fijas durante la simulación. Para una ruta $R$, el tiempo total de la réplica $s$ es:

$$
T_R^{(s)}
=
G^{(s)}
\sum_{(i,j)\in R}
t_{ij}M_{ij}^{(s)},
$$

donde:

$$
M_{ij}^{(s)}
=
\exp\left(
\sigma_{\mathrm{vía}}Z_{ij}^{(s)}
-
\frac{\sigma_{\mathrm{vía}}^2}{2}
\right)
$$

representa la variación local del arco y:

$$
G^{(s)}
\sim
\operatorname{LogNormal}
\left(
-\frac{\sigma_G^2}{2},
\sigma_G
\right),
\qquad
\sigma_G=0.15,
$$

representa una condición general compartida, como lluvia o mayor volumen de tránsito.

El factor $G^{(s)}$ no se incorpora en la función usada para escoger la ruta. Una condición general multiplicativa cambia la magnitud de los tiempos, pero no el costo relativo usado durante la selección determinista. Su función es evaluar el comportamiento de una ruta ya seleccionada.

Los dos modelos se comparan con la misma semilla, el mismo número de réplicas y los mismos supuestos probabilísticos. El factor general es reproducible y común para los recorridos de un par. Los multiplicadores locales, en cambio, se generan a lo largo de cada recorrido y no representan una realización simultánea de tráfico para todos los arcos de la red. Por ello, la expresión *mismo diseño Monte Carlo* es más precisa que afirmar que se observa un único escenario completo de la red.

### 5.4 Métricas de comparación

Para cada modelo y cada par se reportan:

- **Tiempo determinista:** suma de $t_{ij}$ sobre la ruta seleccionada.
- **Media simulada:**
  $$
  \overline{T}_R=\frac{1}{S}\sum_{s=1}^{S}T_R^{(s)}.
  $$
- **Desviación estándar simulada:** dispersión de los tiempos obtenidos.
- **Percentil 90:** valor que no supera el 90 % de los escenarios simulados.
- **Índice de confiabilidad:** porcentaje de réplicas que no excede el 115 % de la media de la propia ruta:
  $$
  IC=\frac{1}{S}\sum_{s=1}^{S}\mathbb{I}\left(T_R^{(s)}\leq1.15\overline{T}_R\right)\times100.
  $$
- **Cambio de ruta:** indicador de si $R_2^*$ contiene una secuencia de nodos diferente de $R_1^*$.
- **Frecuencia de cambio:** porcentaje de pares adicionales en los que el segundo modelo modifica la decisión.

El $IC$ es relativo a la distribución simulada de cada ruta. Describe estabilidad interna, pero no es una medición empírica de puntualidad. La elección considera conjuntamente tiempo central, dispersión y percentil 90, además de esta medida relativa.

## 6. Validación de los modelos

La validación cruzada tradicional divide observaciones en entrenamiento y prueba. Ese esquema no corresponde a este proyecto porque los modelos no aprenden parámetros a partir de ejemplos etiquetados. Se aplica un esquema equivalente adecuado para un problema de optimización y simulación.

### 6.1 Validación algorítmica

Para cada función de costo se compara el resultado de A* bidireccional con Dijkstra:

$$
\left|
C_{A^*}(R^*)-C_{Dijkstra}(R^*)
\right|<\varepsilon,
$$

con $\varepsilon=10^{-6}$ minutos. A* y Dijkstra coincidieron en los dos costos para los 33 pares. La coincidencia verifica que A* encontró el costo óptimo bajo el modelo correspondiente. No demuestra que los tiempos representen la realidad; valida únicamente la implementación del problema matemático definido.

### 6.2 Validación sobre casos adicionales

La verificación se realizó sobre:

- los tres pares originales;
- 30 pares adicionales reproducibles.

En los tres pares originales se obtuvo:

| Par | Modelo | Tiempo determinista | Media simulada | Desviación | Percentil 90 | $IC$ | Ruta distinta |
|---|---|---:|---:|---:|---:|---:|---|
| Estadio Oeste → San Pedro | Menor tiempo | 9.96 | 10.00 | 1.59 | 12.06 | 83.80 % | Sí |
| Estadio Oeste → San Pedro | Ajustado por variabilidad | 9.98 | 10.03 | 1.59 | 12.07 | 83.90 % | Sí |
| Cuatro Reinas → Paso Ancho | Menor tiempo | 8.22 | 8.26 | 1.34 | 10.04 | 82.90 % | No |
| Cuatro Reinas → Paso Ancho | Ajustado por variabilidad | 8.22 | 8.26 | 1.34 | 10.04 | 82.90 % | No |
| Hatillo → Curridabat | Menor tiempo | 8.98 | 8.93 | 1.37 | 10.75 | 84.40 % | No |
| Hatillo → Curridabat | Ajustado por variabilidad | 8.98 | 8.93 | 1.37 | 10.75 | 84.40 % | No |

Con $\lambda=6.5$, el Modelo 2 cambió 1 de los 3 pares originales y 11 de los 30 pares adicionales. La tabla agregada de validación fue:

| Muestra adicional | Pares | Tiempo determinista promedio | Media simulada promedio | Desviación promedio | Percentil 90 promedio | IC promedio |
|---|---:|---:|---:|---:|---:|---:|
| Modelo 1: menor tiempo | 30 | 6.36 min | 6.37 min | 0.98 min | 7.66 min | 83.57 % |
| Modelo 2: ajustado por variabilidad | 30 | 6.44 min | 6.45 min | 1.00 min | 7.76 min | 83.58 % |

El resultado distingue entre dos situaciones:

- si $R_1^*=R_2^*$, la decisión es estable ante la penalización utilizada;
- si $R_1^*\neq R_2^*$, existe un intercambio entre menor tiempo central y menor exposición a la variabilidad supuesta.

### 6.3 Elección sustentada del modelo

Con los datos y supuestos actuales se selecciona el **Modelo 1** como resultado principal. En los 30 pares adicionales presenta menores tiempos deterministas y simulados, además de un percentil 90 menor, sin una pérdida relevante en el índice de confiabilidad. El Modelo 2 conserva valor metodológico porque muestra cómo una penalización explícita puede modificar la decisión, pero no produce una mejora cuantitativa bajo la simulación disponible.

Esta selección no demuestra que el Modelo 1 sea superior en tránsito real. Únicamente indica que, bajo tiempos de flujo libre y dispersiones supuestas por clase vial, la penalización empleada no generó una ventaja simulada.

### 6.4 Estabilidad de la evaluación estocástica

La simulación se repitió con distintas cantidades de réplicas. Entre 1 000 y 5 000, la media agregada cambió aproximadamente $0.01$ minutos y el percentil 90 alrededor de $0.08$ minutos. La evaluación se considera razonablemente estable con 1 000 réplicas, mientras que 200 presenta mayor variación.

## 7. Análisis de sensibilidad

El análisis de sensibilidad determina cuánto cambia la conclusión cuando se modifica un supuesto importante. Los tres supuestos se alteran por separado sobre los tres pares originales para atribuir cada efecto al cambio evaluado.

### 7.1 Importancia de la variabilidad

Se evaluó:

$$
\lambda\in\{0,0.5,1,\ldots,9.5,10\}.
$$

- Con $\lambda=0$, el segundo costo debe reproducir el Modelo 1.
- Entre $\lambda=1$ y $\lambda=6$, se estudia si la decisión permanece estable ante penalizaciones crecientes.
- Con $\lambda=6.5$, se evalúa la especificación principal seleccionada.
- Con $\lambda=9.5$ y $\lambda=10$, se observa el segundo cambio de decisión.

Los recorridos no cambiaron entre $\lambda=0$ y $\lambda=6$. Con $\lambda=6.5$ cambió un par y la media agregada pasó de $9.06$ a $9.07$ minutos. Desde $\lambda=9.5$ cambiaron dos pares, la media aumentó a $9.85$ minutos y el percentil 90 a $11.86$ minutos. La decisión es estable ante penalizaciones moderadas y sensible a partir del umbral observado de $6.5$.

### 7.2 Velocidades imputadas

Como una proporción alta de los arcos no contiene una velocidad registrada en OSM, se evaluaron los factores:

$$
f_v\in\{0.85,1.00,1.15\}.
$$

El factor se aplica únicamente a las velocidades imputadas. Al pasar de $0.85$ a $1.15$, la media del Modelo 1 disminuyó de $9.59$ a $8.67$ minutos y la del Modelo 2 de $10.14$ a $8.68$ minutos. Con el factor $0.85$ cambiaron dos rutas; con $1.00$ y $1.15$ cambió una. La magnitud de los tiempos y la selección de al menos un recorrido son sensibles a la imputación, por lo que este es el principal supuesto frágil del análisis.

### 7.3 Número de réplicas

Se comparó:

$$
S\in\{200,1000,5000\}.
$$

El número de réplicas no modifica la ruta, porque la optimización ocurre antes de la simulación. Al aumentar de 1 000 a 5 000 réplicas, las métricas agregadas cambiaron poco; por ello, 1 000 se considera suficiente para esta investigación inicial. Con 200 réplicas se observó mayor variación Monte Carlo.

### 7.4 Forma de reportar la sensibilidad

Cada supuesto se resume mediante:

| Supuesto modificado | Valores probados | Efecto sobre la métrica principal | Interpretación |
|---|---|---|---|
| Penalización por variabilidad | $\lambda=0,0.5,1,\ldots,9.5,10$ | Cambio de ruta, media y percentil 90 | Estabilidad de la decisión ante el riesgo supuesto |
| Velocidad imputada | $f_v=0.85,1.00,1.15$ | Cambio en tiempos y rutas | Dependencia respecto a la imputación |
| Réplicas Monte Carlo | $S=200,1000,5000$ | Cambio en métricas simuladas | Estabilidad numérica de la simulación |

En conjunto, la selección de ruta es robusta ante valores moderados de $\lambda$ y las métricas son razonablemente estables con 1 000 réplicas. La conclusión es más frágil ante las velocidades imputadas, porque estas afectan tanto la magnitud de los tiempos como algunas rutas seleccionadas.

## 8. Interpretación, limitaciones y gobernanza de datos

Los resultados deben interpretarse dentro de las siguientes restricciones:

1. Los tiempos son estimaciones de flujo libre y no mediciones realizadas en carretera.
2. Las dispersiones por clase vial son supuestos razonables de simulación, no parámetros estimados con datos históricos de tráfico.
3. El costo ajustado por variabilidad es una aproximación aditiva y no un intervalo de confianza ni un cuantil exacto de la ruta.
4. Una ruta seleccionada por el Modelo 2 no equivale a un recorrido oficial ni garantiza un mejor desempeño operativo.
5. Las rutas base son referencias metodológicas construidas mediante puntos intermedios.
6. La densidad poblacional se encuentra agregada por distrito y no representa variaciones internas.
7. La cobertura de OSM puede ser desigual, especialmente en velocidades, paradas y destinos estratégicos.
8. El modelo no incluye demanda, capacidad, costos operativos, horarios, espera ni transbordos.
9. Los 30 pares adicionales son nodos viales seleccionados aleatoriamente, no una muestra de viajes o demanda de pasajeros.
10. Los multiplicadores locales Monte Carlo no forman una observación simultánea de tráfico para toda la red.
11. El $IC$ utiliza como umbral el 115 % de la media de cada ruta y no equivale a puntualidad observada.

En materia de gobernanza, deben abordarse cuatro aspectos concretos:

- **Origen y permiso:** la red y los elementos geográficos provienen de OSM y requieren atribución conforme con la licencia ODbL. Los datos demográficos proceden del INEC y deben citarse con su fuente y fecha.
- **Privacidad:** la información del INEC está agregada por distrito y no contiene datos personales ni reidentificables.
- **Sesgo y representación:** la cobertura de OSM y la selección de nodos pueden favorecer sectores con mayor densidad de datos. Los 30 pares adicionales tampoco representan la distribución real de viajes.
- **Uso indebido y salvaguarda:** un error podría utilizarse para justificar cambios operativos sin conocer demanda, tráfico o recorridos reales. La salvaguarda recomendada es presentar siempre los resultados como exploratorios y exigir validación de campo antes de cualquier decisión.

## 9. Síntesis de las ampliaciones

| Elemento | Avance 1 | Entrega final |
|---|---|---|
| Alcance espacial | Red vial dirigida de San José | Se conserva sin ampliar a toda la GAM |
| Datos | OSM, INEC y velocidades imputadas | Se conservan los mismos datos |
| Modelo de decisión | Camino de menor tiempo | Camino de menor tiempo y camino ajustado por variabilidad |
| Función objetivo principal | $\sum t_{ij}$ | Se conserva como Modelo 1 |
| Segunda función objetivo | No existía | $\sum(t_{ij}+\lambda s_{ij})$ |
| A* bidireccional | Método principal | Resuelve ambos modelos |
| Dijkstra | Control del resultado de A* | Valida ambos modelos; no se presenta como modelo distinto |
| Monte Carlo | Sensibilidad posterior de la ruta A* y la ruta base | Evaluación reproducible de las rutas seleccionadas por ambos modelos |
| Casos analizados | Tres pares seleccionados manualmente | Tres pares originales y 30 pares adicionales reproducibles |
| Validación | Coincidencia A*–Dijkstra en tres pares | Coincidencia en ambos costos para 33 pares y comparación agregada por modelo |
| Sensibilidad | Escenarios simulados sobre rutas fijas | Variación de $\lambda$, velocidades imputadas y número de réplicas |
| Interpretación | Primera aproximación de flujo libre | Se mantiene la misma limitación y se formaliza la incertidumbre |

En síntesis, la entrega final no cambia el propósito exploratorio del proyecto ni pretende resolver el sistema real de transporte público. La ampliación compara dos criterios matemáticos de selección sobre la misma red: uno orientado exclusivamente al menor tiempo central y otro que incorpora una penalización explícita por variabilidad. La validación adicional mostró que ambos algoritmos resuelven correctamente sus costos, mientras que la comparación cuantitativa favoreció al Modelo 1 bajo los supuestos actuales. La sensibilidad identificó las velocidades imputadas como la principal fuente de fragilidad.

## 10. Guía para actualizar el documento final

Esta sección indica qué debe trasladarse manualmente a `Entrega_Final_Rutas_GAM.docx`. No se debe copiar el Avance 1 sin corregir las afirmaciones que dependían de datos inexistentes.

### 10.1 Contenido que debe reemplazarse

1. Sustituir toda referencia a tiempos históricos de hora pico por **tiempos teóricos de flujo libre**.
2. Sustituir toda afirmación de que $\sigma_{ij}$ fue estimada con tráfico por **dispersión lognormal supuesta según clase vial**.
3. Eliminar $\gamma(1/w_j)$ de la función de costo. El índice $w_i$ solo prioriza puntos.
4. Aclarar que la red representa vías de San José y no rutas operativas de autobuses de toda la GAM.
5. Presentar las rutas base como referencias reproducibles mediante puntos intermedios, no como recorridos actuales.
6. Evitar recomendaciones sobre modificar, eliminar o agregar líneas oficiales con los datos actuales.

### 10.2 Secciones que deben incorporarse

El documento final debe contener, como mínimo:

1. **Marco teórico:** grafo dirigido, tiempos de arco, A* bidireccional, heurística admisible, Modelo 1, Modelo 2 y distribución lognormal.
2. **Modelos aplicados:** resultados de ambos modelos, criterio de selección de $\lambda=6.5$ y aclaración de que no fue calibrado con tráfico.
3. **Validación y comparación:** Dijkstra, tres pares originales, 30 adicionales, tabla agregada y elección explícita del Modelo 1.
4. **Análisis de sensibilidad:** $\lambda$, velocidades imputadas y réplicas, con una conclusión de robustez o fragilidad para cada supuesto.
5. **Limitaciones:** alcance de flujo libre, muestra sintética, rutas base, $IC$ relativo y diseño Monte Carlo.
6. **Ética y gobernanza:** licencia ODbL, datos agregados del INEC, sesgos de cobertura, riesgo de uso indebido y salvaguardas.
7. **Conclusiones y recomendaciones:** responder los objetivos con resultados numéricos y recomendar recopilación de datos reales antes de decisiones operativas.
8. **Declaración de uso de asistentes de IA:** indicar de manera breve y transparente las tareas en las que fueron utilizados.

### 10.3 Tablas y figuras que deben utilizarse

Los archivos reproducibles que respaldan el documento son:

| Recurso | Uso recomendado en el documento |
|---|---|
| `data/processed/resultados_rutas.csv` | Comparación del Modelo 1 con las rutas base |
| `data/processed/comparacion_modelos.csv` | Resultados de los dos modelos en los tres pares originales |
| `data/processed/validacion_modelos.csv` | Detalle de los 33 pares y control A*–Dijkstra |
| `data/processed/comparacion_validacion.csv` | Tabla agregada de ambos modelos por muestra |
| `data/processed/sensibilidad_modelos.csv` | Resultados de los tres análisis de sensibilidad |
| `figuras/04_rutas_modelos.png` | Cambio y coincidencia espacial de las rutas |
| `figuras/05_simulacion_modelos.png` | Distribuciones Monte Carlo y rutas base |
| `figuras/06_comparacion_modelos.png` | Comparación de media y percentil 90 |
| `figuras/07_sensibilidad_modelos.png` | Efectos de $\lambda$, velocidades y réplicas |

Cada figura debe llevar número, título, fuente y un párrafo que explique qué se observa y qué implica para el modelado.

### 10.4 Conclusión central que debe conservarse

La conclusión sustentada no es que el modelo ajustado por variabilidad sea mejor por producir rutas diferentes. Con $\lambda=6.5$, modifica 1 de los 3 casos originales y 11 de los 30 adicionales, pero obtiene una media y un percentil 90 ligeramente mayores en la muestra adicional. Por ello, el Modelo 1 se selecciona como resultado principal dentro del alcance actual, mientras que el Modelo 2 demuestra la sensibilidad de la decisión a una penalización explícita de incertidumbre.

Antes de entregar, el documento Word debe actualizarse con estas formulaciones y resultados, convertirse a PDF, mantenerse entre 12 y 16 páginas sin anexos, incluir al menos diez referencias APA 7 citadas en el texto y contener el enlace visible al repositorio público.

## 11. Recomendaciones para una etapa futura con datos reales

Una siguiente etapa debe incorporar observaciones que permitan estimar los tiempos y la variabilidad de cada tramo. Se recomienda recopilar registros GPS de autobuses, tiempos reales de viaje y condiciones asociadas con el horario, el día de la semana, el tráfico y el clima. Con estas observaciones, $t_{ij}$ y $s_{ij}$ podrían estimarse por arco y período en lugar de derivarse únicamente de velocidades de flujo libre y dispersiones supuestas.

También conviene integrar recorridos oficiales, paradas, horarios y frecuencias. Esta información permitiría construir referencias operativas y considerar tiempos de espera, transbordos y restricciones propias del servicio. La demanda puede incorporarse mediante datos agregados de ascensos y descensos, matrices origen–destino o encuestas de movilidad, de modo que los pares analizados respondan a desplazamientos relevantes para los usuarios.

El parámetro $\lambda$ debería calibrarse con un criterio observable. Una alternativa consiste en relacionarlo con metas de puntualidad o con la disposición institucional a aceptar un aumento en el tiempo esperado a cambio de reducir retrasos. La calibración y la evaluación deben utilizar períodos o recorridos diferentes para comprobar el desempeño fuera de la muestra empleada durante el ajuste.

La simulación puede ampliarse mediante escenarios definidos para toda la red. En cada réplica, cada arco conservaría una perturbación común para todas las rutas que lo utilizan y podrían incorporarse correlaciones espaciales o temporales. Esto permitiría representar con mayor fidelidad eventos compartidos como congestión localizada, lluvia o cierres viales.

La validación futura debe comparar los tiempos calculados con observaciones mediante métricas como error absoluto medio, error porcentual, cobertura de intervalos y cumplimiento de umbrales de puntualidad. Además, debe evaluar por separado distintos períodos, sectores y grupos de usuarios para identificar posibles sesgos de cobertura.

Con estas ampliaciones, el proyecto podría avanzar desde una comparación metodológica de caminos sobre una red vial hacia una herramienta de apoyo para la planificación del transporte público. Cualquier uso operativo debe acompañarse de validación de campo, revisión institucional y documentación de la procedencia, licencia y calidad de los datos.
