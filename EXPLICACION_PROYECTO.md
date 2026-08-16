# Alva Logistics Tracker — Explicación completa del sistema

*Documento preparado el 09/08/2026, basado en la revisión completa del código del repositorio (`app.py`, `airtable_connection.py`, `consolidation_detector.py`, `config.py`, `truck_builder.html`), la estructura y automatizaciones reales de la base de Airtable, y una muestra de datos reales de producción (442 shipments registrados).*

> **Nota sobre la app desplegada**: intenté visitar `xlogisticstracker.streamlit.app` directamente, pero la app está protegida por el login de Streamlit Community Cloud (redirige a una pantalla de autenticación), así que no pude "verla" como la vería un usuario. Sin embargo, Streamlit es una herramienta donde **el código define exactamente lo que se ve** — no hay nada oculto ni generado de forma distinta en producción — así que todo lo que describo en la sección 3 sale de leer el código fuente completo, línea por línea, más los datos reales de Airtable a los que sí tuve acceso.

---

## 1. Qué es esto y para qué sirve

**Alva Logistics Tracker** es el sistema interno que usa una empresa de logística/corretaje de fletes (freight brokerage) para gestionar el envío de **tubería (pipe) y accesorios de tubería (elbows/codos)** desde sus propios almacenes hasta clientes en todo Estados Unidos, usando camiones de transportistas externos (carriers) contratados para cada viaje.

### El problema que resuelve

Antes de un sistema así, coordinar esto a mano (hojas de cálculo, correos sueltos, llamadas) es propenso a errores: se te puede olvidar cotizar un flete, se te puede pasar un envío que ya debería estar listo, o — el punto más valioso — se te pueden escapar oportunidades de **combinar dos envíos en un solo camión** para ahorrar dinero. El sistema centraliza todo el flujo:

1. Se registra un **Shipment** (envío) en un almacén: qué se manda, cuánto pesa, a dónde va.
2. Se piden **cotizaciones de flete** (Pricing) a distintos transportistas (carriers) para ese envío.
3. Se elige la mejor cotización y se convierte en un **Load** (una reserva real de camión con un transportista específico), que puede llevar uno o varios shipments a la vez.
4. El sistema detecta automáticamente si hay **oportunidades de consolidación** (dos envíos cercanos que podrían ir en el mismo camión).
5. Se registra un **historial de novedades** (Updates Log) por cada envío: retrasos, cambios de estado, problemas, facturación, etc.
6. Se visualiza todo en un **mapa en vivo** y se calcula cómo acomodar físicamente la carga en el camión con el **Truck Builder**.

### Qué revela el código sobre el tipo de operación

- **Producto**: tubería industrial (pipe) de diámetros de 1/2" hasta 8", en tramos de 10 o 20 pies, bajo especificación **SCH 40/80** (Schedule 40/80, un estándar de grosor de pared de tubería industrial), más "elbows" (codos/accesorios de tubería). Esto sale literalmente de la tabla de referencia `Bundle Dimensions` en Airtable y de las tablas de tamaños codificadas en el Truck Builder.
- **Almacenes propios**: solo dos, uno en **Texas** y otro en **Florida**. Todo el negocio gira en torno a estos dos puntos de despacho.
- **Alcance geográfico**: nacional. Revisando envíos reales en la base, hay destinos en Florida, Texas, Ohio, Indiana, Carolina del Sur, Carolina del Norte, Michigan, Arkansas, Wyoming, Maryland, Nevada, Illinois, Pennsylvania, Tennessee, Missouri, etc. — es decir, se despacha desde 2 almacenes hacia todo el país.
- **Tipos de camión (trailer)** que se usan: Hotshot 40', Flatbed 48'/53', Stepdeck 48'/53', Conestoga 48'/53', y LTL (carga consolidada de terceros). Cada uno tiene un límite de peso: 48,000 lbs para Flatbed/Stepdeck, 15,000 lbs para Hotshot.
- **Volumen real**: la base tiene **442 envíos registrados** históricamente — no es un prototipo vacío, es una herramienta en uso productivo real.
- **Tamaño del equipo**: todas las automatizaciones de Airtable (ver sección 5) envían las alertas a una sola dirección de correo (`alejandrojsuarezp@gmail.com`), la misma que recibe el reporte del detector de consolidaciones. Esto sugiere que hoy el sistema lo opera una persona o un equipo muy pequeño centralizado en un solo punto de contacto — no hay (todavía) una lista de distribución por rol (almacén, ventas, contabilidad, etc.).

---

## 2. Arquitectura general

### Las piezas y cómo se conectan

| Pieza | Qué es | Rol |
|---|---|---|
| **Airtable** | Base de datos tipo hoja de cálculo avanzada, en la nube | Es la "fuente de la verdad": ahí viven todos los datos (envíos, cargas, cotizaciones, novedades). |
| **`app.py` (Streamlit)** | Aplicación web en Python | La interfaz que usa el equipo día a día. Lee y escribe directamente en Airtable vía su API. |
| **`consolidation_detector.py`** | Script en Python | El "cerebro" que detecta qué envíos se pueden combinar. Se usa tanto desde dentro de la app (botón "Detect Opportunities") como de forma independiente (línea de comandos). |
| **`truck_builder.html`** | Página web independiente (HTML/CSS/JavaScript puro) | Herramienta visual para armar la carga dentro del camión. No se conecta a Airtable — funciona 100% en el navegador del usuario, con datos de tamaños de tubería ya escritos en el código. |
| **Airtable Automations** | Automatizaciones configuradas dentro de la propia Airtable (no en el código de este repositorio) | Vigilan cambios en los datos y mandan correos automáticos. |
| **GitHub** | Repositorio de código | Guarda el historial de cambios y es lo que conecta con los dos sitios de despliegue. |

Importante: **no hay una base de datos tradicional (Postgres, MySQL, etc.) ni un servidor "backend" separado.** Airtable hace las veces de base de datos, y `app.py` le habla directamente por su API REST usando peticiones HTTP normales (librería `requests` de Python) — no hay nada intermedio.

### Cómo fluyen los datos

```
                         ┌───────────────────────────────────┐
                         │             AIRTABLE               │
                         │   Base "ALVA LOGISTICS TRACKER"    │
                         │                                     │
                         │  Shipments · Loads · Pricing ·      │
                         │  Updates Log · Bundle Dimensions    │
                         └───────────▲─────────────▲───────────┘
                                     │             │
                     API REST (GET/PATCH/POST,     │  Automatizaciones internas
                     con token de acceso)           │  (viven dentro de Airtable,
                                     │               │  no en este código)
              ┌──────────────────────┴───┐         │
              │                          │         ▼
   ┌──────────┴───────────┐   ┌──────────┴──────┐   ┌────────────────────────┐
   │   app.py (Streamlit)  │   │ consolidation_   │   │  4 Automatizaciones     │
   │   Desplegado en       │   │ detector.py      │   │  activas (ver sección 5)│
   │   Streamlit Community │   │ (script standalone)│  │  → envían correo a      │
   │   Cloud:               │   │  → geocodifica con│  │  alejandrojsuarezp@     │
   │   xlogisticstracker.  │   │    Nominatim       │  │  gmail.com               │
   │   streamlit.app        │   │  → manda email con │  └────────────────────────┘
   │                        │   │    Gmail SMTP       │
   └──────────┬─────────────┘   └────────────────────┘
              │
              │  el usuario interactúa desde su navegador
              ▼
      Persona del equipo (dispatcher / logística)


   ┌─────────────────────────────┐
   │   truck_builder.html          │   No toca Airtable. Corre 100% en el
   │   Servido por GitHub Pages     │   navegador del usuario. Usa tamaños
   │   alejandrojsuarezp.github.io  │   de tubería ya escritos en el código.
   └─────────────────────────────┘
```

En resumen: **todo el tráfico de datos reales pasa por Airtable.** `app.py` lee de ahí para mostrar tablas y métricas, y escribe ahí cuando alguien crea un envío, actualiza un estado, o registra una cotización. El Truck Builder es la única pieza que vive completamente aislada — es una calculadora visual, no un sistema de datos.

### Dónde está desplegado y cómo se actualiza

- **`app.py`** está desplegado en **Streamlit Community Cloud** (`xlogisticstracker.streamlit.app`). Así es como funciona ese servicio: se conecta directamente al repositorio de GitHub y a una rama específica (aquí, `master`), y **cada vez que se hace `git push` a esa rama, Streamlit Cloud reconstruye y redespliega la app automáticamente** — no hace falta ningún archivo de automatización dentro del repo para esto (de hecho, confirmé que no existe ninguna carpeta `.github/workflows` en este proyecto; el auto-deploy lo maneja la plataforma de Streamlit por fuera del código). Esto también significa que **no hay ninguna prueba automática (tests) que se ejecute antes de desplegar** — si `app.py` tiene un error de sintaxis, la próxima vez que alguien abra la app en producción, se rompe directamente, sin red de seguridad.
- **`truck_builder.html`** se sirve mediante **GitHub Pages**, en `https://alejandrojsuarezp.github.io/alva-logistics-tracker/truck_builder.html`. GitHub Pages funciona de forma parecida: publica automáticamente el contenido del repositorio cada vez que se hace push, sin necesidad de un paso de compilación (es HTML/JS plano).
- Las **automatizaciones de Airtable** no dependen de ningún despliegue — viven dentro de la base de Airtable y están activas todo el tiempo, independientemente de si `app.py` está corriendo o no.
- El script **`consolidation_detector.py`**, cuando se ejecuta de forma standalone (`python consolidation_detector.py`, fuera de la app web), no tiene ningún disparador automático configurado en este repositorio — no hay ningún cron job ni GitHub Action que lo corra solo. Es decir, hoy en día, si alguien quiere el reporte por correo de consolidaciones fuera de la app, tendría que ejecutarlo manualmente (o programarlo por su cuenta en algún servidor/máquina).

---

## 3. Recorrido completo de la interfaz

La app tiene una barra de navegación superior con **8 secciones**. No hay menú lateral (está deliberadamente ocultado en el código) — todo se navega desde arriba. Hay un botón **"+ New"** arriba a la derecha que cambia según la página en la que estés (en Dashboard, Consolidaciones, Mapa y Truck Builder no hace nada porque esas páginas no crean registros nuevos).

### 3.1 Dashboard
**Qué se ve**: 5 tarjetas de métricas (Pending Print, In Progress, Ready, Shipped, Active Loads) con un contador y una barrita de color, y debajo dos tablas lado a lado: los primeros 8 "Active Shipments" (envíos activos) y los primeros 8 "Active Loads" (cargas activas, es decir con estado distinto a Shipped/Delivered).
**Acciones del usuario**: ninguna — es de solo lectura. No hay filtros ni botones de edición aquí.
**KPIs que calcula**: son conteos simples filtrando la lista completa de envíos/cargas por su estado actual — no hay fórmulas complejas, solo "cuántos hay en cada estado ahora mismo".

### 3.2 Shipments (Envíos)
**Qué se ve**: una barra de filtros (estado: Pending Print/In Progress/Ready/Shipped; almacén: Texas/Florida; filtros extra: "Pick Up only" y "No load"; y un buscador de texto libre por número o cliente), y debajo una tabla de envíos.
**Acciones**: cada fila tiene un botón "More" que despliega un panel de detalle completo justo debajo de esa fila (no al final de la tabla — el código está diseñado específicamente para que el panel aparezca pegado a la fila que clickeaste, con scroll automático hacia él). Dentro del panel de detalle, se puede:
- **Actualizar el estado del almacén** (Pending Print → In Progress → Ready → Shipped)
- **Agregar una entrada al historial de novedades** (Updates Log) con tipo, responsable, descripción, y una bandera de "requiere atención"
- **Crear una cotización de Pricing** directamente para ese envío (carrier, costo de flete, valor de venta, estado)
- **Asignar el envío a una carga (Load)** existente que aún no esté despachada

También hay un formulario de **"New Shipment"** (número de envío, cliente, email, fecha de entrega solicitada, almacén, dirección, tipo de trailer necesario, peso, bundles/elbows, si es pick-up o no, dimensiones, notas).

### 3.3 Loads (Cargas)
**Qué se ve**: un filtro por estado (Ready/Scheduled/In Transit/Shipped) y una tabla con número de carga, transportista, envíos incluidos, peso total, cantidad de bundles, estado, fecha estimada de recogida (ETA) y costo de flete.
**Acciones**: un desplegable para actualizar el estado de una carga, y un formulario "New Load" que obliga a elegir una **cotización ya "Pending" en Pricing** (o sea, una carga nace de una cotización que ya se pidió), a qué envíos incluye, tipo de trailer y fecha de recogida.

### 3.4 Pricing (Cotizaciones)
**Qué se ve**: una barra de resumen con 4 métricas (cotizaciones pendientes, seleccionadas, perdidas, y el **profit promedio del mes actual**), filtros (estado, almacén, orden por mejor profit o más reciente, buscador), y las cotizaciones **agrupadas por envío** — cada envío muestra hasta sus 3 mejores cotizaciones (ordenadas por profit) en tarjetas lado a lado, marcando cuál es la de mejor margen.
**Acciones**: en cada tarjeta de cotización hay botones **"Select"** (marcarla como la elegida) y **"Lost"** (marcarla como perdida). Y un formulario "New Quote" para crear una cotización nueva (elegir envío(s), transportista, estado, costo de flete, valor de venta).

### 3.5 Updates Log (Historial de novedades)
**Qué se ve**: un filtro por tipo de novedad (o solo las marcadas "Flagged"/con atención requerida) y una tabla con fecha/hora, envío, carga vinculada, tipo, descripción, responsable y si tiene bandera de atención.
**Acciones**: un formulario "New Entry" para agregar una novedad manualmente (elegir envío, carga opcional, tipo, responsable, descripción, y si requiere atención).

### 3.6 Consolidations (Consolidaciones)
Ver sección 4 completa — es la joya del sistema.

### 3.7 Live Map (Mapa en vivo)
**Qué se ve**: 4 métricas (cargas listas en Texas, en Florida, "pares consolidados", y total), y un mapa interactivo (usando la librería Folium) centrado en el sureste de EE.UU. Hay dos estrellas marcando los almacenes de Texas y Florida, y un círculo por cada destino de una carga que está en estado "Ready". Los círculos se pintan de **azul** si salen del almacén de Texas, **amarillo** si salen de Florida, y **naranja** si la carga es consolidada (lleva 2 o más envíos). Al hacer clic en un círculo aparece un popup con el número de carga, transportista, y — si es una carga consolidada — también lista los otros envíos que van en el mismo camión.
**Acciones**: solo interacción de mapa (zoom, clic para ver popups). También hay un expansor de "🔧 Debug" que muestra los datos crudos que llegaron de Airtable, pensado para depuración técnica, no para el uso diario del equipo.

### 3.8 Truck Builder
**Qué se ve**: solo un botón que **abre en una pestaña nueva** la herramienta externa (`truck_builder.html`). No está incrustada dentro de la app de Streamlit.
**Qué hace esa herramienta** (aunque vive fuera de la app principal, vale explicarla porque es parte del proyecto): dejás elegir un tipo de trailer, y después vas colocando "bundles" de tubería (por tamaño y longitud) en una cuadrícula que representa el piso del camión, dividido en secciones y niveles (para apilar), y en dos lados (derecho e izquierdo). La herramienta te dibuja en tiempo real una vista superior, vistas frontal y laterales, y una vista 3D rotable con el mouse, y te avisa si la altura de la carga supera el límite legal de **13'6"** (la altura máxima permitida en carreteras de EE.UU.) o el límite práctico de carga de 10'6". Es una calculadora de acomodo de carga, totalmente separada del resto del sistema.

### Sobre el auto-refresh (actualización automática)

La app tiene programado un refresco automático **cada 30 segundos** (`st_autorefresh`, un componente invisible que simplemente hace que la página se vuelva a ejecutar sola, sin que el usuario haga nada). En la práctica:

- **No es un parpadeo brusco de pantalla en blanco.** Streamlit vuelve a correr el código, pero como los datos más pesados (envíos, cargas, cotizaciones) están **guardados en caché por 20 a 60 segundos** (dependiendo de la página), la mayoría de esos refrescos de 30 segundos usan el dato que ya tenía guardado — no vuelven a pedirle nada a Airtable, así que se sienten casi instantáneos.
- Cuando el caché sí vence (cada 20-60 seg, según la página) y toca ir a buscar datos frescos a Airtable, aparece brevemente un mensaje de "Loading..." (spinner) mientras carga.
- El código se encarga explícitamente de **recordar qué panel tenías abierto, qué filtro tenías puesto, y qué formulario estabas llenando** (usando el "session state" de Streamlit), así que un refresco automático no te cierra lo que tenías abierto ni te borra lo que escribiste en un campo de texto ya confirmado.
- El punto flojo: como es un refresco de **página completa**, si estás a mitad de llenar un formulario largo y el temporizador de 30 segundos justo dispara un recálculo pesado, puede sentirse como una pequeña interrupción/parpadeo de layout, aunque no perdés los datos ya escritos en los campos.

---

## 4. El detector de consolidaciones — la joya del sistema

### En términos simples

Imaginate que hoy salen dos camiones medio vacíos desde el almacén de Florida hacia la misma ciudad (o ciudades muy cercanas), cada uno pagando su propio flete completo. Si alguien se hubiera dado cuenta a tiempo, esos dos envíos podrían haber ido en **un solo camión**, dividiendo el costo del flete entre los dos clientes/envíos en vez de pagarlo dos veces completo. Ese "darse cuenta a tiempo" es exactamente lo que hace este detector — pero de forma automática y para **todos** los envíos activos a la vez, no solo los que un dispatcher recuerde de memoria.

Es la funcionalidad más valiosa del sistema porque **ataca directamente el margen de ganancia** del negocio: cada consolidación exitosa es plata que se deja de gastar en flete duplicado.

### Cómo funciona técnicamente

1. **Toma los envíos activos**: solo los que están en estado *Pending Print*, *In Progress* o *Ready* (los que ya se despacharon —*Shipped*— no tiene sentido consolidarlos, ya se fueron).
2. **Excluye los que no aplican**:
   - Los marcados como **Pick Up = Yes** (el cliente los recoge directamente en el almacén, no hay logística de camión que optimizar).
   - Los que no tienen un almacén reconocido (Texas o Florida).
3. **Separa por almacén**: agrupa los envíos elegibles en dos grupos, Texas y Florida. **Un envío de Texas nunca se compara con uno de Florida** — no tendría sentido, porque no comparten punto de partida.
4. **Geocodifica cada dirección**: convierte la dirección (calle, ciudad, estado, código postal) en coordenadas de latitud/longitud usando el servicio gratuito **Nominatim** (de OpenStreetMap). La primera vez que se geocodifica un envío, el resultado se **guarda directamente en Airtable** (campo "Coordinates") para no tener que volver a pedirlo la próxima vez — esto también respeta el límite de uso de Nominatim, que pide no hacer más de 1 solicitud por segundo.
5. **Calcula distancias**: para cada envío, mide la distancia en línea recta ("geodésica", es decir, la distancia real sobre la curvatura de la Tierra, no la distancia manejando por carretera) hacia **todos los demás envíos de su mismo grupo (mismo almacén)**.
6. **Filtra por un radio máximo de 250 millas** (`DISTANCIA_MAX_MILLAS` en el código — este número se puede ajustar; el historial de cambios del proyecto muestra que en algún momento se subió de 150 a 250 millas).
7. **Se queda con los 3 más cercanos** de cada envío, ordenados de más cerca a más lejos, y los etiqueta "Best match", "2nd option", "3rd option".
8. Para cada posible pareja, muestra también el **peso combinado** de ambos envíos, para que el dispatcher pueda ver a simple vista si cabrían juntos dentro del límite de peso del trailer (48,000 lbs para Flatbed/Stepdeck, 15,000 lbs para Hotshot).

Todo esto corre bajo demanda: hay un botón **"Detect Opportunities"** en la página de Consolidaciones que dispara el análisis completo en el momento (no corre solo en segundo plano dentro de la app web).

### Ejemplo real (datos reales de la base, no inventados)

Al revisar los envíos activos reales en Airtable, encontré este caso, que es exactamente el tipo de par que el detector señalaría como "Best match":

| Campo | Envío A | Envío B |
|---|---|---|
| Número | SHPT-0013719 | SHPT-0013724 |
| Almacén de salida | Florida | Florida |
| Destino | Port Saint Lucie, FL | Port Saint Lucie, FL |
| Estado | In Progress | In Progress |
| Peso | 11,473.78 lbs | 18,358.05 lbs |
| Tipo de trailer necesario | Flatbed 48' | Flatbed 48' |

Ambos salen del mismo almacén (Florida), van literalmente **a la misma ciudad**, y ambos ya piden un Flatbed 48'. Si el detector los analizara:

- **Distancia**: ≈ 0.0 millas (mismo destino) → muy por debajo del límite de 250 millas.
- **Peso combinado**: 11,473.78 + 18,358.05 = **29,831.83 lbs** → muy por debajo del límite de 48,000 lbs de un Flatbed 48'.
- **Conclusión que vería el dispatcher en pantalla**: una tarjeta "Best match" mostrando SHPT-0013724 como el mejor candidato para consolidar con SHPT-0013719 (o viceversa), con "0.0 mi" de distancia y "29,832 lbs" de peso combinado — señal clara de que conviene mandarlos en el mismo camión en vez de dos viajes separados.

*(Nota: no puedo confirmar si estos dos envíos ya fueron consolidados manualmente por el equipo o si siguen sueltos — la instantánea de datos que revisé es de un momento puntual — pero ilustra perfectamente qué tipo de patrón detecta el sistema.)*

---

## 5. Las automatizaciones (Airtable Automations)

Estas automatizaciones **no viven en el código de este repositorio** — están configuradas directamente dentro de Airtable, y corren de forma independiente a si la app de Streamlit está abierta o no. En total hay **15 automatizaciones creadas**, pero solo **4 están activas ("deployed")**; las otras 11 existen como borradores apagados (ver nota al final de esta sección).

### 1. "Ready for Pickup" (Listo para recoger)
- **Qué la dispara**: cuando el campo "Warehouse Status" de un envío cambia a **"Ready"**.
- **Qué hace**:
  1. Busca la(s) carga(s) (Load) a las que ese envío está vinculado.
  2. Envía un correo a `alejandrojsuarezp@gmail.com` con asunto *"🟢 Shipment Ready for Pickup - [número de envío]"*, y el cuerpo incluye cliente, destino (ciudad y estado), peso, tipo de trailer necesario, la carga asignada (si tiene) y la fecha de la orden.
- **Para qué sirve**: avisar en el momento que un envío quedó listo en el almacén para que se coordine su recogida, sin que nadie tenga que estar revisando la tabla manualmente.

### 2. "Pickup Scheduled Confirmation" (Confirmación de recogida agendada)
- **Qué la dispara**: cuando se actualiza el campo **"ETA Pickup"** (fecha/hora estimada de recogida) de una carga.
- **Qué hace**:
  1. Actualiza el propio registro de esa carga.
  2. Envía un correo *"📋 Pickup Scheduled - [número de carga]"* con el transportista, la hora, la lista de envíos incluidos en esa carga, y un recordatorio de "Prepare BOLs for driver signature" (preparar los documentos de embarque para que el conductor los firme).
- **Nota técnica curiosa**: el primer paso de esta automatización deja **en blanco el campo "Load Number"** de la carga cada vez que se actualiza su ETA. Puede ser intencional (quizás una limpieza de algún campo auxiliar) pero, tal como está descrito en la configuración, borra el número de carga cada vez que alguien cambia la hora de recogida — vale la pena que el equipo lo revise si no era el comportamiento buscado.

### 3. "Shipment Marked as Shipped" (Envío marcado como despachado)
- **Qué la dispara**: cuando "Warehouse Status" de un envío pasa a **"Shipped"**.
- **Qué hace**:
  1. Busca la carga vinculada a ese envío.
  2. Busca la cotización de Pricing asociada a esa carga (para sacar el nombre del transportista real).
  3. Envía un correo *"✅ Shipment Shipped - [número]"* con todos los detalles del envío, número de carga, transportista, y la leyenda "Status: COMPLETED... This shipment is now in transit."
- **Para qué sirve**: confirmación de cierre de ciclo para ese envío — quedó documentado que salió y con qué transportista.

### 4. "Orders Status Report (7am)" (Reporte diario de estado de órdenes)
- **Qué la dispara**: un temporizador (cron) que corre todos los días a las **7:00 AM**.
- **Qué hace**: junta tres listas de envíos según su estado (Pending Print, In Progress, Ready) y manda un correo resumen *"📋 Orders Status - [fecha]"* con cada lista y el mensaje *"Priority: Check orders with upcoming delivery date"*.
- **Detalle a tener en cuenta**: el horario configurado en Airtable está en **zona horaria UTC**, no en hora de Texas o Florida. Eso significa que el correo probablemente no llega a las 7:00 AM hora local del equipo, sino más temprano (alrededor de la 1-2 AM hora Central, según la época del año) — vale la pena confirmarlo con el equipo y ajustar si el objetivo real era que llegara a las 7 AM hora local.

### Detalle común a las 4
Las cuatro le mandan el correo **únicamente a `alejandrojsuarezp@gmail.com`** — no hay todavía una lista de distribución por rol (por ejemplo, que el almacén reciba solo las suyas y ventas otras). Es la misma dirección que recibe el reporte del detector de consolidaciones cuando se corre manualmente.

### Automatizaciones creadas pero **no activas** (borradores)
Vale la pena mencionar que en Airtable existen otras 11 automatizaciones ya diseñadas pero apagadas — es básicamente una hoja de ruta de lo que el equipo ya pensó pero no ha activado todavía: *Preparation Reminder (2 hours before)*, *Late Pickup Alert*, *Billing Ready*, *Daily Operations Summary*, *Dispatch Confirmed (Customer Email)*, *Shipments Sent Yesterday*, *Shipments Sent Today (6PM Summary)*, *Shipments Scheduled for Tomorrow*, *Status Synchronization*, *Preparation Validation*, y *Consolidation Opportunity Alert*. Esta última en particular es interesante porque sugiere que en algún momento se pensó en automatizar el aviso de consolidaciones (hoy es un botón manual en la app), pero no se llegó a activar.

---

## 6. Todo lo demás que vale la pena saber

- **Es una aplicación de un solo archivo gigante.** `app.py` tiene más de 2,000 líneas y contiene absolutamente todo: el diseño visual (CSS incrustado), la navegación, y la lógica de las 8 páginas. No está dividido en módulos separados por página. Esto es común en proyectos que crecen rápido a partir de un prototipo funcional, pero significa que cualquier cambio requiere entender un archivo grande.
- **Airtable hace de "base de datos + panel de administración" a la vez.** No hay una base de datos tradicional. La ventaja de esto es que, si algo falla en la app de Streamlit, el equipo puede seguir viendo y hasta editando los datos directamente desde la interfaz normal de Airtable, sin depender de que la app esté funcionando.
- **No hay control de usuarios ni permisos dentro de la app.** Cualquier persona que entre a la app (una vez que pasa el login de Streamlit Cloud, si está activado) puede crear, editar o mover cualquier registro — no hay roles tipo "solo lectura" o "solo almacén".
- **Las credenciales están en texto plano en un archivo de configuración** (`.streamlit/secrets.toml`): el token de acceso a Airtable y la contraseña de aplicación de Gmail que usa el script de consolidaciones para mandar correos. Es la forma estándar de manejar secretos en Streamlit, pero conviene tenerlas presentes como información sensible.
- **La distancia de las consolidaciones es "en línea recta", no la distancia real manejando.** Esto es una simplificación consciente (calcular ruta real de manejo es mucho más caro y lento), pero significa que en casos con obstáculos geográficos (por ejemplo, cruzar una bahía o una zona montañosa) la distancia real en carretera podría ser bastante mayor a la que muestra el sistema.
- **El Truck Builder es la pieza más "artesanal" del proyecto.** Está escrito a mano en HTML/CSS/JavaScript puro (sin ningún framework), incluyendo sus propios dibujos en 2D y 3D hechos con `<canvas>` — no usa ninguna librería gráfica externa. Tiene las medidas exactas de 13 tamaños distintos de tubería (de 1/2" a 8") ya cargadas en el código, y valida en tiempo real si la altura de la carga se pasa del límite legal de 13'6" en carretera.
- **El sistema ya tiene uso real, no es un prototipo de prueba**: 442 envíos históricos registrados en Airtable, con nombres de ciudades y estados reales en todo el país.
- **El despliegue es directo, sin ambiente de pruebas.** Un `git push` a la rama principal actualiza la app en producción de inmediato (así funciona Streamlit Community Cloud), y no hay ninguna prueba automática (tests) que corra antes. Esto agiliza mucho el desarrollo, pero significa que un error de código se nota directamente en la herramienta que usa el equipo para trabajar.
- **El auto-refresh y el caché están balanceados a propósito** para no golpear demasiado la API de Airtable ni el servicio gratuito de geocodificación (Nominatim), que tiene límites estrictos de uso. Es un detalle técnico, pero explica por qué a veces los datos tardan hasta un minuto en reflejar un cambio hecho desde otro lado (por ejemplo, directamente en Airtable).
