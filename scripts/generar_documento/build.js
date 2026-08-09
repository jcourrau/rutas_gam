const fs = require("fs");
const path = require("path");
const H = require("./build_entrega_final.js");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  PageBreak, Header, Footer, PageNumber,
} = require("docx");
const { portada, h1, h2, p, b, i, t, caption, figure, table, MARGIN } = H;

const body = [];

// ---------------------------------------------------------------------------
// MEJORA RESPECTO AL AVANCE 1
// ---------------------------------------------------------------------------
body.push(h1("Mejora respecto al Avance 1"));
body.push(p([
  t("El profesor señaló tres vacíos en el avance y un punto conceptual. Los cuatro se atendieron así: "),
  b("(1) primer modelo, EDA y notebook incompletos"), t(" — el avance corregido ya incluía la aplicación de A* y Dijkstra, la simulación estocástica, las visualizaciones interpretadas y el notebook ejecutable; en esta entrega se reorganizó todo en tres notebooks numerados (exploración, modelos, validación) que corren de principio a fin de forma independiente. "),
  b("(2) mezcla entre camino mínimo y el problema del agente viajero"), t(" — se eliminó cualquier rastro de restricción de eliminación de subtours (MTZ) y de variables binarias "), i("x"), t("ᵢⱼ de diseño de recorrido. El modelo se formula exclusivamente como un problema de camino mínimo entre pares fijos, resuelto con A*/Dijkstra; la restricción de conservación de flujo del avance corregido ya correspondía a esta formulación. "),
  b("(3) referencias de métodos y de Prezi"), t(" — se agregaron y mantienen las referencias de osmnx (Boeing, 2017), NetworkX (Hagberg et al., 2008), A* (Hart et al., 1968), búsqueda bidireccional (Pohl, 1971) y Barabási (2016); no queda ninguna referencia a Prezi en la lista final."),
]));
body.push(p([
  t("Lo nuevo de esta entrega, exigido por el instructivo de la semana 15, es la incorporación de un "),
  b("segundo modelo"), t(" (la simulación Monte Carlo, formalizada como modelo estocástico independiente), la "),
  b("validación extendida"), t(" sobre pares adicionales, el "), b("análisis de sensibilidad"), t(", la "),
  b("comparación cuantitativa"), t(" entre ambos modelos y las secciones de ética y de conclusiones/recomendaciones."),
]));

// ---------------------------------------------------------------------------
// INTRODUCCIÓN
// ---------------------------------------------------------------------------
body.push(h1("1. Introducción y planteamiento del problema"));
body.push(p("La Gran Área Metropolitana (GAM) concentra más de la mitad de la población del país y es su principal núcleo urbano y económico (Museo Nacional de Costa Rica, s.f.). La movilidad es determinante para la calidad de vida y la competitividad nacional, pero la congestión y la fragmentación del transporte público dificultan los desplazamientos cotidianos. Entre 2018 y 2025 la cantidad de personas movilizadas en transporte público disminuyó un 42.2 %, mientras el parque vehicular superó los 2.1 millones de unidades con un crecimiento anual promedio del 4.2 % (Pomareda García, 2026; Allen M., 2026)."));
body.push(p("La teoría de grafos permite representar una red de transporte mediante nodos y arcos dirigidos ponderados por tiempo (Barabási, 2016). Este proyecto usa una extracción reproducible de la red vial de San José —nodos como intersecciones, arcos como tramos transitables— para calcular caminos de menor tiempo entre pares de puntos y evaluar su sensibilidad ante variaciones simuladas del tiempo de viaje. Es una primera aproximación al problema de movilidad de la GAM: no reproduce la topología operativa de las líneas de autobús ni sustituye datos oficiales de ARESEP."));

body.push(h1("2. Justificación"));
body.push(p("Más de 2.7 millones de personas residen en la GAM y muchas destinan entre una y dos horas diarias a trasladarse, sin integración plena entre modalidades de transporte público (UCR, 2024). La sectorización del transporte público del Área Metropolitana se discute desde 1998 sin resolver sus metas de conectividad, eficiencia y reducción de tiempos (UCR, 2023). El sector transporte concentra además una parte sustancial de las emisiones y el consumo de hidrocarburos del país (PNUD, 2022). Un modelo reproducible de caminos mínimos, evaluado bajo incertidumbre, aporta una base cuantitativa que usuarios, operadores e instituciones públicas pueden usar para comparar recorridos bajo criterios explícitos, como paso inicial hacia análisis con datos operativos y de demanda reales."));

body.push(h1("3. Objetivos"));
body.push(p([b("Objetivo general: "), t("desarrollar y evaluar una aproximación reproducible al problema de movilidad de la GAM mediante dos modelos complementarios —un camino mínimo determinista (A* bidireccional) y una simulación estocástica Monte Carlo— sobre la red vial dirigida de San José, comparando cuantitativamente su desempeño y su sensibilidad ante los supuestos del modelo.")]));
body.push(p([b("Objetivos específicos:")]));
const objetivos = [
  "Integrar la red vial de OpenStreetMap con información distrital del INEC y destinos estratégicos para preparar los costos temporales y priorizar los puntos de estudio.",
  "Calcular rutas de menor tiempo para tres pares origen-destino representativos mediante A* bidireccional, validado con Dijkstra, y construir para cada par una ruta base reproducible de referencia.",
  "Aplicar un modelo estocástico Monte Carlo sobre las rutas fijas para evaluar reducción de tiempo, reducción de variabilidad, confiabilidad y esfuerzo computacional, y comparar cuantitativamente ambos modelos sobre las mismas rutas.",
  "Validar la optimalidad de A* en un conjunto de pares adicionales al de estudio y realizar un análisis de sensibilidad sobre los supuestos que más afectan las conclusiones (número de réplicas, dispersión de la condición general del escenario y velocidad imputada por clase vial).",
];
objetivos.forEach((o, idx) => body.push(p([t(`${idx + 1}. `), t(o)])));

// ---------------------------------------------------------------------------
// MARCO TEÓRICO
// ---------------------------------------------------------------------------
body.push(h1("4. Marco teórico"));
body.push(h2("4.1 Modelo 1 — Camino mínimo determinista (A* bidireccional)"));
body.push(p("El Modelo 1 resuelve el problema clásico de camino mínimo: dado un grafo dirigido G(N, A), un origen o y un destino d, encontrar la secuencia de arcos consecutivos que minimiza el tiempo total de viaje. Cada arco (i, j) tiene un costo tij igual a su tiempo estimado de flujo libre:"));
body.push(p([i("tᵢⱼ = longitudᵢⱼ / velocidadᵢⱼ × 0.06"), t("   (longitud en metros, velocidad en km/h, resultado en minutos).")], { align: "center" }));
body.push(p("Cuando OSM reporta el límite de velocidad (maxspeed) se usa ese valor; si falta, se imputa según la clase vial (highway), con referencia en el artículo 98 de la Ley de Tránsito N.º 9078. Solo el 15 % de los arcos tiene velocidad registrada; el resto depende de este supuesto de imputación, retomado en la Sección 6."));
body.push(p("A* bidireccional mantiene dos fronteras de búsqueda: una avanza desde o sobre G y otra desde d sobre el grafo inverso. Cada nodo se prioriza con f(n) = g(n) + h(n), donde g(n) es el tiempo acumulado y h(n) la heurística geodésica dividida entre la velocidad máxima de la red:"));
body.push(p([i("h(n) = distancia_geodésica(n, meta) / velocidad_máxima")], { align: "center" }));
body.push(p("La distancia geodésica en línea recta nunca supera la distancia real sobre la red, por lo que h(n) nunca sobreestima el tiempo restante: la heurística es admisible y A* conserva la garantía de optimalidad. La búsqueda se detiene cuando la cota inferior de ambas fronteras abiertas no puede mejorar la mejor conexión encontrada. Dijkstra —el caso particular con h(n) = 0— corre en paralelo como control: bajo los mismos pesos, ambos algoritmos deben producir el mismo costo óptimo, aunque exploren cantidades distintas de nodos."));
body.push(p([b("Supuestos: "), t("el grafo conserva el sentido de circulación y existe al menos un camino factible entre cada par; los pesos representan condiciones de flujo libre sin congestión observada; los costos son siempre positivos, por lo que ningún ciclo puede mejorar la solución óptima.")]));

body.push(h2("4.2 Modelo 2 — Simulación Monte Carlo estocástica"));
body.push(p("El Modelo 2 no vuelve a resolver el camino mínimo: toma la ruta óptima y la ruta base ya fijas por el Modelo 1 y simula S = 1000 escenarios para estimar cómo varía su tiempo total bajo condiciones inciertas. Es un modelo distinto porque parte de un supuesto distinto sobre cómo se genera el tiempo de viaje —determinista de flujo libre en el Modelo 1, estocástico lognormal en el Modelo 2— y responde una pregunta distinta: no ‘¿cuál es la ruta más rápida?’ sino ‘¿qué tan confiable es esa ruta?’."));
body.push(p("En cada escenario s, el tiempo del arco (i, j) se multiplica por un factor lognormal cuyo parámetro σ_via depende de la clase vial (0.10 para autopistas hasta 0.22 para vías terciarias):"));
body.push(p([i("τᵢⱼ,ₛ = tᵢⱼ × exp(σ_via · Zᵢⱼ,ₛ − σ_via²/2),   Zᵢⱼ,ₛ ~ N(0,1)")], { align: "center" }));
body.push(p("El término −σ²/2 asegura que el valor esperado del multiplicador sea exactamente 1, de modo que la simulación introduce dispersión sin desplazar artificialmente el promedio. Cada escenario recibe además un factor general compartido por toda la ruta (lluvia, tráfico), con σ_general = 0.15:"));
body.push(p([i("Tₛ = γₛ · Σ(i,j)∈ruta τᵢⱼ,ₛ,   γₛ ~ lognormal(−σ_general²/2, σ_general)")], { align: "center" }));
body.push(p([b("Supuestos: "), t("las variaciones por arco son independientes entre sí; el factor general es común a toda la ruta en un mismo escenario; la simulación no cambia la ruta seleccionada por el Modelo 1, solo mide su sensibilidad; se usa una semilla fija (42 + número de par) para que los resultados sean reproducibles.")]));

body.push(h2("4.3 Métricas de éxito"));
body.push(table(
  ["Métrica", "Qué mide", "Modelo que la produce"],
  [
    ["RT (%)", "Reducción porcentual del tiempo determinista de la ruta óptima frente a la base", "Modelo 1"],
    ["RV (%)", "Reducción porcentual de la desviación estándar simulada frente a la base", "Modelo 2"],
    ["IC (%)", "% de escenarios donde el tiempo simulado no supera en 15 % el promedio de la ruta óptima", "Modelo 2"],
    ["NE", "Nodos explorados por A* (comparado contra Dijkstra)", "Modelo 1"],
  ],
  [1800, 5300, 2000],
));
body.push(p("A estas se agregan, para esta entrega, las métricas de comparación entre modelos (sesgo, ancho del intervalo de confianza al 90 % y cobertura de subestimación), definidas en la Sección 5."));

// ---------------------------------------------------------------------------
// DATOS Y EDA
// ---------------------------------------------------------------------------
body.push(h1("5. Datos y análisis exploratorio"));
body.push(p("La red vial se extrajo de OpenStreetMap el 19 de julio de 2026 (enlace verificable: openstreetmap.org, licencia ODbL); las paradas y destinos estratégicos, el 20 de julio de 2026. La densidad poblacional distrital proviene de las Estimaciones de Población y Vivienda 2022 del INEC (publicadas el 9 de noviembre de 2023, acceso público). El estudio es transversal: no contiene una serie histórica de tráfico."));
body.push(table(
  ["Variable", "Tipo", "Unidad", "Fuente"],
  [
    ["length", "Numérica continua", "metros", "OSM"],
    ["maxspeed / speed_kph", "Numérica continua", "km/h", "OSM (15 %) / imputada por clase vial (85 %)"],
    ["travel_time_min", "Numérica continua (derivada)", "minutos", "Calculada"],
    ["highway", "Categórica", "—", "OSM"],
    ["densidad_poblacional", "Numérica continua", "hab/km²", "INEC 2022"],
    ["destinos_estrategicos", "Numérica discreta", "conteo en 500 m", "OSM"],
    ["w_i", "Numérica continua [0,1] (derivada)", "índice", "Calculada"],
  ],
  [2600, 2400, 2200, 1900],
));
body.push(p("Procesamiento: las velocidades de OSM en mph se convierten a km/h; las faltantes se imputan por clase vial (Sección 4.1); cada punto geográfico se conecta al nodo vial más cercano (ox.distance.nearest_nodes); los duplicados de paradas por coordenada se eliminan; el índice w_i se calcula con normalización min-max de densidad y destinos, ponderados 0.6/0.4 (Sección 6.4 evalúa la sensibilidad de estos pesos)."));
body.push(...figure("01_velocidades_por_fuente.png", 480, "Figura 1. Velocidades registradas en OSM (naranja) frente a velocidades imputadas por clase vial (azul). Las imputadas se concentran en los valores discretos de la Ley 9078; las registradas son más dispersas."));
body.push(...figure("02_red_paradas_importantes.png", 400, "Figura 2. Red vial de San José y las 20 paradas priorizadas, coloreadas por el índice de importancia wᵢ. La concentración en el centro y el occidente revela menor cobertura en la periferia."));
body.push(...figure("03_importancia_paradas.png", 460, "Figura 3. Índice de importancia combinado de las 20 paradas seleccionadas. Las puntuaciones más altas se concentran en León XIII y el casco central."));

// ---------------------------------------------------------------------------
// MODELOS APLICADOS
// ---------------------------------------------------------------------------
body.push(h1("6. Modelos aplicados"));
body.push(h2("6.1 Configuración y pares de estudio"));
body.push(p("Los tres pares se fijaron manualmente con paradas reales de OSM en lados opuestos de Circunvalación, con cobertura oeste-este, norte-sur y suroeste-este: Estadio Oeste → San Pedro, Cuatro Reinas → Paso Ancho y Hatillo → Curridabat. No hay partición de entrenamiento/prueba en el sentido de aprendizaje supervisado —ambos modelos son de optimización y simulación, no de ajuste estadístico—, pero sí hay decisiones documentadas que afectan el resultado: la semilla de cada simulación (42 + número de par, 0/1/2), el número de réplicas (1000) y los pesos α = 0.6, β = 0.4 del índice de importancia."));
body.push(...figure("04_rutas_astar.png", 500, "Figura 4. Rutas obtenidas con A* bidireccional para los tres pares de estudio."));
body.push(p("A* y Dijkstra coincidieron en el costo óptimo en los tres pares (diferencia < 10⁻⁶ min), lo que valida la implementación del Modelo 1."));

body.push(h2("6.2 Resultados del Modelo 1 y el Modelo 2"));
body.push(table(
  ["Par", "T. óptimo (min)", "T. base (min)", "RT %", "RV %", "IC %", "NE (A*)", "NE (Dijkstra)"],
  [
    ["Estadio Oeste → San Pedro", "9.96", "11.11", "10.35", "9.16", "84.2", "4235", "4877"],
    ["Cuatro Reinas → Paso Ancho", "8.22", "8.59", "4.32", "4.34", "84.0", "3094", "3245"],
    ["Hatillo → Curridabat", "8.98", "12.45", "27.86", "27.72", "82.2", "3197", "4105"],
  ],
  [2600, 1300, 1300, 900, 900, 900, 1100, 1200],
));
body.push(...figure("05_simulacion_tiempos.png", 500, "Figura 5. Distribución de tiempos simulados (Modelo 2) en 1000 escenarios para las rutas óptimas y sus referencias base."));
body.push(...figure("06_metricas_exito.png", 480, "Figura 6. Métricas de éxito por par (izquierda) y esfuerzo computacional de A* frente a Dijkstra (derecha)."));
body.push(p("En promedio, las rutas óptimas redujeron el tiempo estimado en 14.18 % (RT) y la variabilidad simulada en 13.74 % (RV) frente a sus referencias base, con una confiabilidad promedio del 83.5 %. A* exploró en promedio 567 nodos menos que Dijkstra (13.9 % de reducción), aunque su ejecución fue más lenta en esta implementación por el costo de mantener dos fronteras y calcular la heurística en cada expansión."));

// ---------------------------------------------------------------------------
// VALIDACIÓN Y COMPARACIÓN
// ---------------------------------------------------------------------------
body.push(h1("7. Validación y comparación"));
body.push(h2("7.1 Validación extendida del Modelo 1"));
body.push(p("El avance solo verificó la coincidencia A*/Dijkstra en los tres pares de estudio. Para esta entrega se generaron 30 pares origen-destino adicionales, elegidos al azar entre los nodos de la red (semilla 2026, excluyendo los tres pares originales), como un conjunto de validación independiente del conjunto usado para ilustrar el método."));
body.push(...figure("07_validacion_extendida.png", 420, "Figura 7. Reducción de nodos explorados de A* frente a Dijkstra en los 30 pares de validación adicionales."));
body.push(p("A* y Dijkstra coincidieron en el costo óptimo en el 100 % de los 30 pares (diferencia < 10⁻⁶ min en todos los casos), lo que respalda la corrección del algoritmo más allá de los pares ilustrativos. La reducción de nodos explorados varió entre −5.9 % y 55.9 % según el par (promedio 28.8 %): en algunos casos A* exploró más nodos que Dijkstra, lo que confirma que su ventaja de eficiencia depende de la posición relativa de origen y destino y no está garantizada en todos los casos."));

body.push(h2("7.2 Estabilidad del Modelo 2 ante la semilla aleatoria"));
body.push(p("Como esquema de validación equivalente a una partición cruzada para un modelo de simulación, se repitió la simulación de 1000 escenarios en 5 particiones con semillas distintas por par."));
body.push(table(
  ["Par", "RV % (media ± σ)", "IC % (media ± σ)", "CV de RV"],
  [
    ["Estadio Oeste → San Pedro", "9.32 ± 0.38", "84.62 ± 0.34", "4.1 %"],
    ["Cuatro Reinas → Paso Ancho", "3.77 ± 0.66", "83.74 ± 0.84", "17.5 %"],
    ["Hatillo → Curridabat", "27.60 ± 0.29", "84.22 ± 0.67", "1.1 %"],
  ],
  [3400, 2200, 2200, 1400],
));
body.push(p("El coeficiente de variación (CV) de RV es menor al 5 % en dos de los tres pares. En Cuatro Reinas → Paso Ancho el CV es mayor (17.5 %) porque su RV base es pequeño (~4 %): una diferencia absoluta de pocas décimas se traduce en un porcentaje relativo grande. La conclusión cualitativa —las rutas óptimas son más estables que la base— se mantiene en los tres pares en todos los folds."));

body.push(h2("7.3 Comparación cuantitativa: Modelo 1 vs. Modelo 2"));
body.push(p("Ambos modelos se evaluaron sobre las mismas tres rutas. El Modelo 1 entrega un tiempo puntual determinista; el Modelo 2, una distribución de 1000 tiempos simulados. Se comparan con el sesgo entre ambos, el ancho del intervalo 5%-95% que solo el Modelo 2 puede expresar, y la cobertura de subestimación."));
body.push(table(
  ["Par", "Modelo 1 (min)", "Media Modelo 2 (min)", "Sesgo (%)", "IC90 (min)", "Subestimación"],
  [
    ["Estadio Oeste → San Pedro", "9.96", "9.93", "−0.24", "4.89", "47.0 %"],
    ["Cuatro Reinas → Paso Ancho", "8.22", "8.19", "−0.37", "4.17", "46.6 %"],
    ["Hatillo → Curridabat", "8.98", "9.05", "+0.77", "4.36", "49.0 %"],
  ],
  [3300, 1700, 1900, 1300, 1300, 1700],
));
body.push(p([b("Cuál modelo elegir y por qué: "), t("el sesgo entre ambos modelos es menor al 1 % en los tres pares —el Modelo 2 no distorsiona el valor esperado del Modelo 1—, así que ninguno ‘le gana’ al otro en precisión promedio. La diferencia está en lo que cada uno puede comunicar: el Modelo 1 no tiene forma de expresar que, en cerca de la mitad de los escenarios simulados (46.6 %-49.0 %), el tiempo real supera su propia predicción puntual, ni que la ruta puede tardar hasta ~4-5 minutos más en un escenario desfavorable (ancho de IC90). Para elegir la ruta más rápida basta el Modelo 1; para comunicar un tiempo de viaje con el que un operador o un usuario pueda planificar —incluyendo el riesgo de subestimación— es necesario el Modelo 2. Se recomienda usar ambos en conjunto: el Modelo 1 como motor de optimización y el Modelo 2 como capa de confiabilidad, no uno en sustitución del otro.")]));

// ---------------------------------------------------------------------------
// SENSIBILIDAD Y LIMITACIONES
// ---------------------------------------------------------------------------
body.push(h1("8. Análisis de sensibilidad y limitaciones"));
body.push(table(
  ["Supuesto movido", "Valores probados", "Efecto sobre la métrica principal"],
  [
    ["Réplicas de Monte Carlo", "200 / 1000 / 5000", "RV_pct de Hatillo→Curridabat: 26.2 % / 27.7 % / 27.3 %. Se estabiliza a partir de 1000; con 200 réplicas la estimación oscila más."],
    ["σ_general (condición compartida del escenario)", "0.05 / 0.15 / 0.30", "IC_pct de Estadio Oeste→San Pedro: 99.3 % / 84.2 % / 74.4 %. A mayor dispersión, menor confiabilidad estimada."],
    ["Velocidad imputada por clase vial", "×0.85 / ×1.0 / ×1.15", "RT_pct de Hatillo→Curridabat: 29.8 % / 27.9 % / 26.2 %. Cambia varios puntos porcentuales en los tres pares."],
    ["Pesos α/β del índice wᵢ", "(0.6,0.4) / (0.5,0.5) / (0.8,0.2) / (0.3,0.7)", "El top-20 de paradas priorizadas no cambia (100 % de superposición) en ninguna combinación probada."],
  ],
  [2600, 2200, 4400],
));
body.push(...figure("08_sensibilidad_velocidades.png", 440, "Figura 8. Sensibilidad de RT al factor aplicado sobre la velocidad imputada por clase vial."));
body.push(p([b("¿Es el modelo robusto o frágil? "), t("Es "), b("robusto"), t(" ante el número de réplicas (a partir de 1000) y ante los pesos del índice de importancia: la selección de paradas no depende críticamente de esa elección puntual. Es "), b("sensible"), t(" a σ_general y, sobre todo, a la velocidad imputada: como el 85 % de los arcos no tiene velocidad registrada en OSM, buena parte del valor numérico de RT depende de un supuesto legal (Ley 9078) y no de una medición directa. Esto implica que las conclusiones cualitativas del proyecto —las rutas óptimas son más rápidas y más confiables que la referencia base— son estables, pero las cifras exactas de RT no deben citarse como una medición de campo.")]));
body.push(h2("8.1 Limitaciones"));
body.push(p("El modelo no captura congestión observada, tiempos de espera, frecuencia de buses, transbordos ni demanda real de pasajeros: los tiempos representan flujo libre. La densidad poblacional se asigna por distrito y no describe variación dentro de cada distrito. La cantidad de destinos estratégicos depende de la cobertura de OSM, que —como se documenta en la Sección 9— no es uniforme en el espacio. La ruta base es una referencia metodológica (mínima distancia por un punto intermedio), no un recorrido oficial de autobús, así que RT y RV miden la diferencia frente a esa referencia, no una mejora del sistema de transporte público real. Con más tiempo y datos operativos de ARESEP (recorridos, paradas, pasajeros movilizados, horarios), el modelo podría evolucionar de un problema de camino mínimo hacia uno de diseño y frecuencia de rutas."));

// ---------------------------------------------------------------------------
// ÉTICA
// ---------------------------------------------------------------------------
body.push(h1("9. Consideraciones éticas y gobernanza de datos"));
body.push(p([b("Origen y permiso. "), t("La red vial y las paradas provienen de OpenStreetMap bajo licencia ODbL, que permite copiar, redistribuir y adaptar los datos siempre que se atribuya la fuente y —si se publica una base de datos derivada sustancial— se mantenga la misma licencia; este documento y el repositorio citan la fuente y su fecha de consulta. La densidad poblacional del INEC es de acceso público (Estimaciones de Población y Vivienda 2022). Ninguna de las dos fuentes restringe su uso académico ni la publicación del repositorio.")]));
body.push(p([b("Privacidad. "), t("No se manejan datos personales ni reidentificables: las paradas de bus, hospitales, escuelas y demás destinos son infraestructura pública, y la densidad poblacional está agregada a nivel de distrito, no de vivienda ni de persona.")]));
body.push(p([b("Sesgo. "), t("La cobertura de OpenStreetMap no es uniforme: las zonas centrales de San José —donde de hecho se concentran las paradas de mayor wᵢ (Figuras 2 y 3)— suelen estar mejor mapeadas que la periferia, con más destinos etiquetados y más velocidades registradas. Esto puede generar un sesgo de retroalimentación: si el índice de importancia se usara para decidir dónde invertir, las zonas ya mejor documentadas —no necesariamente las de mayor necesidad— tendrían más probabilidad de aparecer como prioritarias, dejando fuera a distritos periféricos con menor densidad de datos, no necesariamente menor necesidad de transporte.")]));
body.push(p([b("Uso indebido. "), t("El riesgo principal es que alguien use el tiempo determinista del Modelo 1 —construido en un 85 % sobre velocidades imputadas legales, no medidas— como si fuera un tiempo de viaje observado, para prometer tiempos de recorrido a pasajeros o para justificar decisiones de inversión sin datos operativos reales. La salvaguarda que recomienda este proyecto es doble: (1) no usar el modelo como única fuente para decisiones operativas o de inversión sin complementarlo con datos de ARESEP y mediciones de campo, y (2) comunicar siempre el intervalo de incertidumbre del Modelo 2 junto con el valor puntual del Modelo 1, tal como se hace en la Sección 7.3.")]));

// ---------------------------------------------------------------------------
// CONCLUSIONES Y RECOMENDACIONES
// ---------------------------------------------------------------------------
body.push(h1("10. Conclusiones y recomendaciones"));
body.push(p([b("Sobre el objetivo 1 (integración de datos): "), t("se integraron exitosamente la red de OSM, la densidad distrital del INEC y los destinos estratégicos en un índice único wᵢ que prioriza 20 paradas; el índice resultó robusto a la elección de sus pesos (Sección 8), aunque limitado por la cobertura desigual de OSM (Sección 9).")]));
body.push(p([b("Sobre el objetivo 2 (Modelo 1): "), t("A* bidireccional y Dijkstra coincidieron en el costo óptimo en los 3 pares de estudio y en 30 pares de validación adicionales (100 % de coincidencia), confirmando la corrección de la implementación. A* redujo en promedio 567 nodos explorados (13.9 %) frente a Dijkstra, aunque a costa de mayor tiempo de ejecución por el manejo de dos fronteras.")]));
body.push(p([b("Sobre el objetivo 3 (Modelo 2 y comparación): "), t("la simulación estocástica mostró que el Modelo 1 subestima el tiempo real posible en 46.6 %-49.0 % de los escenarios y no puede expresar un intervalo de incertidumbre de hasta ~4.9 minutos. Ningún modelo es categóricamente mejor: se recomienda su uso conjunto (Sección 7.3).")]));
body.push(p([b("Sobre el objetivo 4 (sensibilidad): "), t("las conclusiones cualitativas del proyecto son robustas al número de réplicas y a los pesos del índice de importancia, pero sensibles a la dispersión de la condición general del escenario y, sobre todo, a la velocidad imputada por clase vial —la limitación más importante del proyecto, porque afecta directamente la magnitud de RT.")]));
body.push(h2("10.1 Recomendaciones prácticas"));
const recs = [
  "Para el MOPT/ARESEP: antes de usar cifras de RT para justificar cambios operativos, contrastar las velocidades imputadas del modelo con mediciones de campo en al menos los corredores de los tres pares de estudio, dado que el 85 % de los arcos depende de ese supuesto.",
  "Para futuras entregas del curso o del proyecto: ampliar la cobertura de OSM verificada (maxspeed real) en la periferia de la GAM antes de extender el índice de importancia a esas zonas, para no heredar el sesgo de cobertura documentado en la Sección 9.",
  "Para cualquier equipo que reutilice este repositorio: reportar siempre el par (tiempo determinista, intervalo de confianza simulado) y no solo el tiempo puntual, siguiendo el criterio de la Sección 7.3.",
  "Para una siguiente fase del proyecto: incorporar datos de ARESEP sobre recorridos, paradas, pasajeros movilizados y horarios, y migrar el problema de camino mínimo hacia uno de diseño y frecuencia de rutas de transporte público.",
];
recs.forEach((r) => body.push(p([t("• "), t(r)])));

// ---------------------------------------------------------------------------
// NOTA IA
// ---------------------------------------------------------------------------
body.push(h1("11. Nota sobre uso de asistentes de inteligencia artificial"));
body.push(p("Se usó un asistente de IA (Claude, Anthropic) como apoyo en: (a) depuración y extensión del código del paquete rutas_gam (módulo de validación, comparación de modelos y análisis de sensibilidad, construido sobre la lógica ya escrita por el grupo en el avance); (b) reorganización del repositorio a la estructura exigida por el instructivo; (c) redacción de un borrador de las secciones nuevas de este documento (marco teórico del Modelo 2, validación, sensibilidad, ética) a partir de los resultados numéricos generados por el código, revisado y editado por el grupo. Todo el contenido entregado fue revisado y es explicable por los integrantes."));

// ---------------------------------------------------------------------------
// REFERENCIAS
// ---------------------------------------------------------------------------
body.push(h1("Referencias"));
const refs = [
  "Allen M., J. (2026, 18 de mayo). La cuenta regresiva: Costa Rica avanza hacia el punto de no retorno en movilidad urbana. El Financiero. https://www.elfinancierocr.com/economia-y-politica/la-cuenta-regresiva-costa-rica-avanza-hacia-el/23VBZ6TTPZF4RAVQUW6AK4ABZY/story/",
  "Asamblea Legislativa de la República de Costa Rica. (2012, 26 de octubre). Ley de Tránsito por Vías Públicas Terrestres y Seguridad Vial, Ley N.º 9078, artículo 98. Sistema Costarricense de Información Jurídica. https://pgrweb.go.cr/Scij/Busqueda/Normativa/Normas/nrm_articulo.aspx?nValor1=1&nValor2=73504&nValor3=139716&nValor5=99&param1=NRA",
  "Barabási, A.-L. (2016). Network science. Cambridge University Press. https://networksciencebook.com/",
  "Boeing, G. (2017). OSMnx: New methods for acquiring, constructing, analyzing, and visualizing complex street networks. Computers, Environment and Urban Systems, 65, 126–139. https://doi.org/10.1016/j.compenvurbsys.2017.05.004",
  "Fundación Friedrich Ebert. (2015). El transporte público en la Gran Área Metropolitana de Costa Rica. https://library.fes.de/pdf-files/bueros/fesamcentral/12310.pdf",
  "Hagberg, A. A., Schult, D. A., & Swart, P. J. (2008). Exploring network structure, dynamics, and function using NetworkX. Proceedings of the 7th Python in Science Conference, 11–15.",
  "Hart, P. E., Nilsson, N. J., & Raphael, B. (1968). A formal basis for the heuristic determination of minimum cost paths. IEEE Transactions on Systems Science and Cybernetics, 4(2), 100–107. https://doi.org/10.1109/TSSC.1968.300136",
  "Instituto Nacional de Estadística y Censos. (2023, 9 de noviembre). INEC publica distribución a nivel de distrito de las Estimaciones de Población y Vivienda 2022. https://admin.inec.cr/noticias/inec-publica-distribucion-nivel-distrito-las-estimaciones-poblacion-vivienda-2022",
  "Museo Nacional de Costa Rica. (s.f.). Descripción Gran Área Metropolitana. https://www.museocostarica.go.cr/nuestro-trabajo/investigaciones/historia-natural/gam/descripcion/",
  "Open Knowledge Foundation. (2011). Open Database License (ODbL) v1.0. https://opendatacommons.org/licenses/odbl/1-0/",
  "OpenStreetMap contributors. (2026). OpenStreetMap [Conjunto de datos]. https://www.openstreetmap.org/",
  "Ortiz Madrigal, G. A. (2024, 23 de febrero). El grave problema de movilidad del GAM requiere una solución de largo plazo. Delfino.cr. https://delfino.cr/2024/02/el-grave-problema-de-movilidad-del-gam-requiere-una-solucion-de-largo-plazo",
  "Pohl, I. (1971). Bidirectional search. En B. Meltzer y D. Michie (Eds.), Machine intelligence 6 (pp. 127–140). Edinburgh University Press.",
  "Pomareda García, F. (2026, 17 de marzo). Personas movilizadas por transporte público bajó un 42.2 % mientras la cantidad de vehículos creció un 62.1 % en los últimos 12 años. Semanario Universidad. https://semanariouniversidad.com/pais/personas-movilizadas-por-transporte-publico-bajo-un-42-2-mientras-la-cantidad-de-vehiculos-crecio-un-62-1-en-los-ultimos-12-anos/",
  "Programa de las Naciones Unidas para el Desarrollo. (2022, 31 de mayo). 20 municipalidades de la GAM se unen para mejorar movilidad de las personas y restaurar paisaje urbano. https://www.undp.org/es/costa-rica/press-releases/20-municipalidades-de-la-gam-se-unen-para-mejorar-movilidad-de-las-personas-y-restaurar-paisaje-urbano",
  "Universidad de Costa Rica. (2023, 23 de abril). Costa Rica está varada en un sistema de transporte público obsoleto. https://www.ucr.ac.cr/noticias/2023/4/23/costa-rica-esta-varada-en-un-sistema-de-transporte-publico-obsoleto.html",
  "Universidad de Costa Rica. (2024, 11 de abril). La UCR propone impulsar el desarrollo urbano orientado al transporte público en el país. https://www.ucr.ac.cr/noticias/2024/4/11/la-ucr-propone-impulsar-el-desarrollo-urbano-orientado-al-transporte-publico-en-el-pais.html",
  "Vásquez Gómez, E. P., Quevedo Buitrago, J. E., Méndez Pineda, D. O., Merchán Hernández, A. E., & Gordillo Ochoa, W. D. (2026). Teoría de grafos para optimizar la red de cobertura a instituciones educativas públicas de la Provincia Sur del Sumapaz (Colombia). Revista de la Universidad del Zulia, 17(48), 298–319. https://doi.org/10.5281/zenodo.18210299",
];
refs.forEach((r) => body.push(new Paragraph({
  spacing: { after: 140, line: 360 },
  indent: { left: 400, hanging: 400 },
  children: [new TextRun({ text: r, size: 22 })],
})));

module.exports = { body };
