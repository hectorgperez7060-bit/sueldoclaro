# SUELDO CLARO — Manual de uso

**Para contadores, estudios contables y empresas**
Versión de prueba · Agosto 2026

Dirección de acceso: **https://my-project-six-rho-76.vercel.app**

---

## Antes de empezar: qué es y qué NO es (todavía)

Sueldo Claro es una plataforma para liquidar sueldos de Argentina. Le cargás los empleados una sola vez, elegís el convenio de cada uno y con un botón obtenés la liquidación completa con todos los descuentos.

**Importante — leer una sola vez:** esta es una **versión de prueba**. Las escalas salariales y los porcentajes están cargados como **ejemplos sin verificar**. No sirve todavía para pagar sueldos reales. Cuando un contador matriculado cargue las escalas vigentes de cada gremio, quedará lista para uso real. Mientras tanto, sirve para probar el circuito completo y ver cómo calcula.

Vas a ver un cartel amarillo arriba de la pantalla que te recuerda esto. No se va a ir hasta que los valores estén verificados.

---

## 1. Crear tu cuenta (una sola vez)

1. Entrá a la dirección de acceso.
2. Tocá la pestaña **"Crear cuenta"**.
3. Completá:
   - **Nombre del estudio o empresa** — por ejemplo "Estudio Contable Pérez" o "Distribuidora del Sur SA".
   - **CUIT** — 11 dígitos. Podés escribirlo con guiones o todo junto; el sistema los ignora. Debe ser un CUIT válido.
   - **Email** y **Contraseña** (mínimo 8 caracteres).
4. Tocá **"Crear cuenta gratis"**.

Con eso quedás adentro. Tu cuenta es tu espacio privado: **nadie más puede ver tus datos**. Si sos un estudio con varios clientes, más adelante vas a poder tener cada empresa separada (eso llega en una etapa próxima).

**Para volver a entrar otro día:** usá la pestaña **"Ingresar"** con tu email y contraseña.

> La sesión dura un rato por seguridad. Si te pide ingresar de nuevo, es normal: volvés a poner email y contraseña.

---

## 2. Cargar empleados

En el panel principal, sección **Empleados**:

1. Tocá **"+ Agregar empleado"**.
2. Completá los datos:

| Campo | Qué poner |
|---|---|
| **Nombre** y **Apellido** | Los del empleado. |
| **CUIL** | 11 dígitos. Con o sin guiones. El sistema valida que sea correcto (si te dice "inválido", revisá que sean 11 dígitos y que empiece con 20, 23, 24, 27, 30, 33 o 34). |
| **Fecha de ingreso** | La fecha real de alta. Con esto el sistema calcula la **antigüedad** automáticamente. |
| **Convenio / Sindicato** | Elegí de la lista (ver punto 3). |
| **Categoría** | Se llena sola según el convenio elegido. |
| **Jornada** | "Completa" o "Media jornada". Si es media jornada, todo el recibo se calcula proporcionalmente. |

3. Tocá **"Guardar empleado"**. Aparece en la tabla de abajo.

Repetí para cada empleado. Los vas viendo en la lista con su convenio y categoría.

---

## 3. Los convenios disponibles

Cada empleado se liquida según **su** convenio. Hoy están cargados estos seis:

| Convenio | Sindicato | Categorías de ejemplo | Particularidad |
|---|---|---|---|
| Comercio 130/75 | FAECYS | Administrativo A/B, Vendedor B, Maestranza A | Cuota sindical 2% |
| Metalúrgicos 260/75 | UOM | Operario, Medio Oficial, Oficial | Cuota sindical 2,5% |
| Construcción 76/75 | UOCRA | Ayudante, Medio Oficial, Oficial | **Sin presentismo** (así es en la construcción) |
| Gastronómicos 389/04 | UTHGRA | Camarera/o, Cocinero/a, Recepcionista | Cuota sindical 2,5% |
| Sanidad 122/75 | FATSA | Administrativo, Enfermero/a | Cuota sindical 3% |
| Camioneros 40/89 | Fed. Camioneros | Chofer 1ra, Acompañante | Cuota sindical 2,5% |

Cada convenio tiene sus propias categorías, su cuota sindical y su tratamiento de amparos judiciales. **No es "todo igual a Comercio"**: cada gremio liquida distinto.

> ¿Falta tu convenio o una categoría? Se agrega fácil. Es cargar datos, no reprogramar. Pedilo y se suma.

---

## 4. Liquidar el mes

En la sección **Liquidar sueldos**:

1. Elegí el **mes a liquidar**.
2. Tocá **"Liquidar todos los empleados"**.

En unos segundos aparece, para cada empleado, el detalle completo del recibo:

- **Haberes** (lo que suma): sueldo básico, antigüedad, presentismo, horas extra si corresponde.
- **Descuentos** (lo que se le resta al empleado).
- **Aportes del empleador** (lo que paga la empresa aparte, no se le descuenta al empleado).
- **Bruto**, **total de descuentos** y **Neto a cobrar** bien destacado.

Si un concepto está suspendido por un **amparo judicial**, aparece con una etiqueta violeta indicando el artículo (por ejemplo "amparo L27802:131"). Esto te da la trazabilidad de por qué ese ítem no se cobró.

---

## 5. Qué descuentos calcula (y cuáles faltan)

**Descuentos al empleado que ya calcula — reales y obligatorios:**

- **Jubilación (11%)** — aporte jubilatorio (SIPA).
- **Ley 19.032 / PAMI (3%)** — aporte al INSSJP.
- **Obra Social (3%)** — la obra social sindical del convenio.
- **Cuota sindical** — solo si el empleado está afiliado (2% a 3% según el gremio).

Estos cuatro son los que aparecen en cualquier recibo real.

**Aportes que paga el empleador (no se le descuentan al empleado):**

- Contribución jubilatoria, obra social, PAMI, asignaciones familiares. El sistema los muestra en el detalle para que veas el **costo laboral total**.

**Descuentos reales que existen pero el sistema TODAVÍA no calcula (próximas etapas):**

- **Impuesto a las Ganancias (4ª categoría)** — solo a sueldos que superan el mínimo. Es el más importante que falta.
- **Descuentos particulares del empleado** — anticipos, embargos, cuotas, seguros adicionales.
- **Seguro de vida obligatorio (SCVO)** — lo paga el empleador, no se descuenta.

---

## 6. Preguntas frecuentes

**¿Me dice "CUIT inválido" o "CUIL inválido"?**
Revisá que sean exactamente 11 dígitos y que empiece con un prefijo válido (20, 23, 24, 27 para personas; 30, 33, 34 para empresas). Podés escribirlo con guiones o puntos, el sistema los limpia. Si tiene 8 dígitos, eso es un DNI, no un CUIL.

**¿Otra empresa puede ver mis empleados?**
No. Cada cuenta está completamente aislada. Está verificado técnicamente: una empresa nunca puede ver, buscar ni exportar datos de otra.

**¿Puedo usar esto para pagar sueldos de verdad ahora?**
Todavía no. Los valores son de ejemplo (cartel amarillo). El circuito funciona; faltan las escalas verificadas por un profesional.

**¿Los cálculos son confiables?**
El motor está probado con casos de control validados. Si mañana cambia una escala, las liquidaciones ya hechas no se modifican solas: cada liquidación guarda una "foto" de los valores que usó. Esto es clave ante una inspección.

**¿Cuánto cuesta?**
La versión de prueba está funcionando sin costo. El modelo comercial se define más adelante.

---

## 7. Lo que viene (por etapas)

El desarrollo avanza de a una capa, verificando cada una antes de seguir:

1. ✅ **Convenios por sindicato** — hecho (esta versión).
2. ⏳ **Circuito de aprobación** — simular → borrador → comparar con el mes anterior → un responsable aprueba → cierre definitivo.
3. ⏳ **Novedades completas** — ausencias, licencias, premios, anticipos, embargos, descuentos particulares por empleado.
4. ⏳ **Recibo PDF oficial** — formato Anexo III del Decreto 407/2026, con gráfico y descarga/envío por email.
5. ⏳ **Liquidación final / despido** — con fecha libre e indemnizaciones.
6. ⏳ **Roles y seguridad reforzada** — aprobador, auditor, contador revisor, doble factor.
7. ⏳ **Impuesto a las Ganancias** y conceptos configurables por vos.

---

## 8. Soporte

Ante cualquier duda, error o pedido (agregar un convenio, una categoría, un concepto), anotalo y se resuelve. La plataforma está pensada para que **la complejidad viva en el sistema, no sobre vos**: no necesitás ser especialista laboral para usarla.

*Sueldo Claro — Primero claro. Después completo. Siempre seguro.*
