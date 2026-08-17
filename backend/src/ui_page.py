"""Pantalla web de SUELDOCLARO (interfaz simple en español, servida en "/").

Capa 1: selector de convenio/sindicato con categorías dinámicas (GET /convenios).
"""

HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SUELDOCLARO — Liquidación de sueldos</title>
<style>
  :root{--verde:#0f766e;--verde2:#0d9488;--gris:#f4f6f8;--txt:#1f2937;--borde:#e5e7eb}
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;background:var(--gris);color:var(--txt)}
  header{background:var(--verde);color:#fff;padding:14px 20px;display:flex;justify-content:space-between;align-items:center}
  header h1{font-size:1.25rem;letter-spacing:.2px}
  .marca{display:flex;align-items:center;gap:9px}
  .marca svg{width:38px;height:38px;flex:none}
  header small{opacity:.85}
  .contenedor{max-width:960px;margin:24px auto;padding:0 16px}
  .tarjeta{background:#fff;border:1px solid var(--borde);border-radius:12px;padding:20px;margin-bottom:20px;box-shadow:0 1px 3px rgba(0,0,0,.06)}
  h2{font-size:1.05rem;margin-bottom:12px;color:var(--verde)}
  label{display:block;font-size:.85rem;margin:10px 0 4px;color:#374151}
  input,select,textarea{width:100%;padding:9px 10px;border:1px solid var(--borde);border-radius:8px;font-size:.95rem;background:#fff;font-family:inherit}
  input:focus,select:focus,textarea:focus{outline:2px solid var(--verde2);border-color:transparent}
  .fila{display:grid;grid-template-columns:1fr 1fr;gap:12px}
  @media(max-width:640px){.fila{grid-template-columns:1fr}}
  button{background:var(--verde);color:#fff;border:0;border-radius:8px;padding:10px 18px;font-size:.95rem;cursor:pointer;margin-top:14px}
  button:hover{background:var(--verde2)}
  button.secundario{background:#fff;color:var(--verde);border:1px solid var(--verde)}
  button.chico{padding:6px 12px;font-size:.85rem;margin-top:0}
  .tabs{display:flex;gap:8px;margin-bottom:16px}
  .tabs button{margin-top:0;flex:1}
  .tabs button.inactivo{background:#e5e7eb;color:#374151}
  table{width:100%;border-collapse:collapse;font-size:.9rem;margin-top:10px}
  th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--borde)}
  th{background:#f9fafb;font-weight:600}
  td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
  .aviso{background:#fef3c7;border:1px solid #fcd34d;color:#92400e;border-radius:8px;padding:10px 14px;font-size:.85rem;margin-bottom:16px}
  .error{background:#fee2e2;border:1px solid #fca5a5;color:#991b1b;border-radius:8px;padding:10px 14px;font-size:.9rem;margin-top:12px;display:none}
  .ok{background:#d1fae5;border:1px solid #6ee7b7;color:#065f46;border-radius:8px;padding:10px 14px;font-size:.9rem;margin-top:12px;display:none}
  .neto{font-size:1.4rem;font-weight:700;color:var(--verde)}
  .etiqueta{display:inline-block;background:#e0f2f1;color:var(--verde);border-radius:999px;padding:2px 10px;font-size:.75rem;margin-left:6px}
  .amparo{background:#ede9fe;color:#5b21b6}
  #app{display:none}
  .cabecera-seccion{display:flex;justify-content:space-between;align-items:center}
  .detalle{margin-top:14px;border:1px solid var(--borde);border-radius:10px;padding:14px}
  .acciones-tabla{display:flex;gap:6px;white-space:nowrap}
  .estado-edicion{display:block;color:#6b7280;font-size:.75rem;margin-top:4px}
  @media(max-width:640px){
    .contenedor{padding:0 10px;margin:14px auto}
    .tarjeta{padding:16px}
    .cabecera-seccion{align-items:flex-start;gap:10px}
    table.tabla-movil thead{display:none}
    table.tabla-movil,table.tabla-movil tbody,table.tabla-movil tr,table.tabla-movil td{display:block;width:100%}
    table.tabla-movil tr{border:1px solid var(--borde);border-radius:9px;margin:10px 0;padding:7px 10px}
    table.tabla-movil td{display:grid;grid-template-columns:minmax(105px,40%) 1fr;gap:8px;padding:7px 0;border-bottom:1px solid var(--borde);overflow-wrap:anywhere}
    table.tabla-movil td:last-child{border-bottom:0}
    table.tabla-movil td::before{content:attr(data-label);font-weight:600;color:#374151}
    table.tabla-movil td.acciones-celda{display:block}
    table.tabla-movil td.acciones-celda::before{display:none}
    .acciones-tabla button{flex:1;min-height:38px}
  }
</style>
</head>
<body>
<header>
  <div class="marca">
    <svg viewBox="0 0 64 64" role="img" aria-label="Logo Sueldo Claro">
      <path d="M12 7h27l10 10v25H12z" fill="none" stroke="#fff" stroke-width="5" stroke-linejoin="round"/>
      <path d="M39 7v11h10M20 24h19M20 33h12" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="m31 45 8 8 15-18" fill="none" stroke="#fbbf24" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <h1>Sueldo Claro</h1>
  </div>
  <small id="quien"></small>
</header>
<div class="contenedor">
  <div class="aviso">⚠️ Versión de prueba con <b>parámetros de EJEMPLO</b> (escalas y alícuotas sin verificar por contador). No usar para sueldos reales todavía.</div>

  <div id="auth">
    <div class="tarjeta" style="max-width:460px;margin:0 auto">
      <div class="tabs">
        <button id="tabIngresar" onclick="mostrarTab('ingresar')">Ingresar</button>
        <button id="tabCrear" class="inactivo" onclick="mostrarTab('crear')">Crear cuenta</button>
      </div>
      <div id="formIngresar">
        <label>Email</label><input id="liEmail" type="email" placeholder="tu@email.com">
        <label>Contraseña</label><input id="liPass" type="password">
        <button onclick="ingresar()" style="width:100%">Ingresar</button>
      </div>
      <div id="formCrear" style="display:none">
        <label>Nombre del estudio o empresa</label><input id="rzRazon" placeholder="Estudio Contable Pérez">
        <label>CUIT (11 dígitos)</label><input id="rzCuit" placeholder="30123456789" maxlength="13">
        <label>Email</label><input id="rzEmail" type="email" placeholder="tu@email.com">
        <label>Contraseña (mínimo 8)</label><input id="rzPass" type="password">
        <button onclick="crearCuenta()" style="width:100%">Crear cuenta gratis</button>
      </div>
      <div class="error" id="authError"></div>
    </div>
  </div>

  <div id="app">
    <div class="tarjeta">
      <div class="cabecera-seccion">
        <h2>Empleados</h2>
        <div style="display:flex;gap:6px;flex-wrap:wrap">
          <button class="chico secundario" onclick="toggleAlta()">+ Agregar manual</button>
          <label class="chico secundario" style="cursor:pointer;display:inline-flex;align-items:center;margin:0">+ Importar Excel (.xlsx)<input type="file" id="inputExcel" accept=".xlsx" style="display:none" onchange="subirExcelPreview(this)"></label>
          <button class="chico secundario" onclick="descargarPlantillaExcel()" title="Descargar plantilla para importar empleados">📥 Plantilla de empleados</button>
          <button class="chico secundario" onclick="salir()">Salir</button>
        </div>
      </div>

      <div id="vistaPreviaExcel" style="display:none;border:1px solid var(--borde);border-radius:10px;padding:14px;margin-top:12px;background:#fafafa">
        <h3 style="font-size:1rem;color:var(--verde);margin:0 0 6px">📄 Vista previa de importación de Excel</h3>
        <p id="resumenExcel" style="font-size:.9rem;color:#4b5563;margin-bottom:10px"></p>

        <div id="boxValidos" style="margin-bottom:14px">
          <h4 style="font-size:.85rem;color:#059669;margin:6px 0">🟢 Filas válidas para importar (<span id="countValidos">0</span>)</h4>
          <table id="tablaValidos" style="margin-top:4px"><thead><tr><th>Fila</th><th>Apellido y nombre</th><th>CUIL</th><th>Convenio</th><th>Categoría</th><th>Ingreso</th></tr></thead><tbody></tbody></table>
        </div>

        <div id="boxErrores" style="margin-bottom:14px">
          <h4 style="font-size:.85rem;color:#dc2626;margin:6px 0">🔴 Filas con errores que serán omitidas (<span id="countErrores">0</span>)</h4>
          <table id="tablaErrores" style="margin-top:4px"><thead><tr><th>Fila</th><th>CUIL / Nombre</th><th>Errores detectados</th></tr></thead><tbody></tbody></table>
        </div>

        <div style="display:flex;gap:8px;margin-top:12px">
          <button class="chico ok" id="btnConfirmarImport" onclick="confirmarImportacionExcel()">Confirmar e importar</button>
          <button class="chico secundario" onclick="cancelarVistaPreviaExcel()">Cancelar</button>
        </div>
        <div class="error" id="excelError" style="margin-top:8px"></div>
        <div class="ok" id="excelOk" style="margin-top:8px"></div>
      </div>

      <div id="alta" style="display:none;border:1px dashed var(--borde);border-radius:10px;padding:14px;margin-top:12px">
        <h3 style="font-size:.9rem;color:var(--verde);margin:4px 0 6px">Datos personales</h3>
        <div class="fila">
          <div><label>Nombre</label><input id="eNombre"></div>
          <div><label>Apellido</label><input id="eApellido"></div>
          <div><label>CUIL (11 dígitos)</label><input id="eCuil" placeholder="20123456786" maxlength="13"></div>
          <div><label>Fecha de nacimiento</label><input id="eNacimiento" type="text" inputmode="numeric" placeholder="DD/MM/AAAA" maxlength="10" oninput="formatearFecha(this)"><small style="color:#6b7280">Escribí solo números: 15081974 se transforma en 15/08/1974.</small></div>
          <div><label>Sexo</label><select id="eSexo"><option value="">—</option><option value="M">Masculino</option><option value="F">Femenino</option><option value="X">X</option></select></div>
          <div><label>Estado civil</label><select id="eEstadoCivil"><option value="">—</option><option>Soltero/a</option><option>Casado/a</option><option>Divorciado/a</option><option>Viudo/a</option><option>Unión convivencial</option></select></div>
          <div style="grid-column:1/-1"><label>Domicilio</label><input id="eDomicilio" placeholder="Calle, número, localidad"></div>
        </div>

        <h3 style="font-size:.9rem;color:var(--verde);margin:14px 0 6px">Cargas de familia</h3>
        <div class="fila">
          <div><label>Cantidad de hijos</label><input id="eHijos" type="number" min="0" value="0"></div>
          <div><label>¿Cónyuge a cargo?</label><select id="eConyuge"><option value="false">No</option><option value="true">Sí</option></select></div>
        </div>

        <h3 style="font-size:.9rem;color:var(--verde);margin:14px 0 6px">Datos laborales</h3>
        <div class="fila">
          <div><label>Fecha de ingreso</label><input id="eFecha" type="text" inputmode="numeric" placeholder="DD/MM/AAAA" maxlength="10" oninput="formatearFecha(this)"><small style="color:#6b7280">Escribí solo números.</small></div>
          <div><label>Legajo</label><input id="eLegajo" placeholder="0001"></div>
          <div><label>Actividad del establecimiento</label>
            <select id="eActividad" onchange="llenarConvenios()"></select></div>
          <div><label>Convenio colectivo aplicable</label>
            <select id="eConvenio" onchange="llenarCategorias()"></select></div>
          <div><label>Sindicato / federación del convenio</label>
            <input id="eSindicato" readonly placeholder="Se completa según el convenio"></div>
          <div><label>Categoría</label>
            <select id="eCategoria"></select></div>
          <div><label>Modalidad de contrato</label>
            <select id="eModalidad"><option>Tiempo indeterminado</option><option>Plazo fijo</option><option>Eventual</option><option>Temporada</option><option>Período de prueba</option></select></div>
          <div><label>Horas semanales pactadas</label>
            <input id="eHorasSemanales" type="number" min="1" max="48" step="0.5" value="48">
            <small style="color:#6b7280">En Comercio la jornada completa es 48. Para este empleado escribí 30.</small></div>
          <div><label>Obra social (independiente del sindicato)</label><input id="eObraSocial" list="obrasSociales" placeholder="Elegí o escribí la obra social"><datalist id="obrasSociales"><option value="OSADEF - Obra Social de las Asociaciones de Empleados de Farmacia"><option value="OSPSA - Obra Social del Personal de la Sanidad Argentina"><option value="OSECAC - Obra Social de Empleados de Comercio"><option value="OSPF - Obra Social del Personal de Farmacia"></datalist></div>
          <div><label>Lugar de trabajo / sucursal</label><input id="eLugar" placeholder="Casa central"></div>
          <div><label>Remuneración pactada (si supera el básico)</label><input id="eRemun" type="number" min="0" placeholder="opcional"></div>
        </div>

        <h3 style="font-size:.9rem;color:var(--verde);margin:14px 0 6px">Datos de pago</h3>
        <div class="fila">
          <div><label>Forma de pago * (la exige ARCA)</label>
            <select id="eFormaPago" onchange="toggleCbu()"><option value="">Elegí una opción…</option><option value="1">Efectivo</option><option value="2">Cheque</option><option value="3">Acreditación en cuenta (CBU)</option><option value="4">Otra</option></select></div>
          <div><label id="lblCbu">CBU (22 dígitos)</label><input id="eCbu" maxlength="22" placeholder="opcional"></div>
        </div>

        <h3 style="font-size:.9rem;color:var(--verde);margin:14px 0 6px">Datos sindicales (para cuota de afiliado según el convenio)</h3>
        <div class="fila">
          <div><label>Localidad / jurisdicción</label><input id="eLocalidad" placeholder="Ej.: CABA, Rosario, Córdoba"></div>
          <div><label>Filial sindical (si aplica)</label><input id="eFilial" placeholder="opcional"></div>
        </div>

        <div style="display:flex;gap:8px;margin-top:10px">
          <button class="chico" id="btnGuardarEmp" onclick="crearEmpleado()">Guardar empleado</button>
          <button class="chico secundario" id="btnCancelarEmp" style="display:none" onclick="cancelarEdicion()">Cancelar edición</button>
        </div>
        <div class="error" id="empError"></div>
        <div class="ok" id="empOk"></div>
      </div>
      <table id="tablaEmpleados" class="tabla-movil"><thead><tr><th>Apellido y nombre</th><th>CUIL</th><th>Convenio</th><th>Categoría</th><th>Ingreso</th><th></th></tr></thead><tbody></tbody></table>
      <p id="sinEmpleados" style="margin-top:10px;color:#6b7280;font-size:.9rem">Todavía no cargaste empleados.</p>
    </div>

    <div class="tarjeta">
      <div class="cabecera-seccion">
        <h2>Novedades mensuales</h2>
        <button class="chico secundario" onclick="toggleNovedad()">+ Cargar novedad</button>
      </div>
      <div class="fila">
        <div><label>Mes</label><input id="novPeriodo" type="month" onchange="cargarNovedades()"></div>
        <div style="display:flex;align-items:end"><button class="secundario" onclick="cargarNovedades()" style="width:100%">Ver novedades del mes</button></div>
      </div>

      <div id="formNovedad" style="display:none;border:1px dashed var(--borde);border-radius:10px;padding:14px;margin-top:12px">
        <h3 id="tituloNovedad" style="font-size:.9rem;color:var(--verde);margin:4px 0 6px">Nueva novedad</h3>
        <div class="fila">
          <div style="grid-column:1/-1"><label>Empleado</label><select id="novEmpleado" onchange="actualizarAdicionalesConvenio()"></select></div>
          <div><label>Días trabajados</label><input id="novDias" type="number" min="0" value="0"></div>
          <div><label>Faltas justificadas</label><input id="novFaltasJ" type="number" min="0" value="0"></div>
          <div><label>Faltas injustificadas</label><input id="novFaltasI" type="number" min="0" value="0"></div>
          <div><label>Licencias (días)</label><input id="novLicencias" type="number" min="0" value="0"></div>
          <div><label>Vacaciones (días)</label><input id="novVacaciones" type="number" min="0" value="0"></div>
          <div><label>Horas extra al 50%</label><input id="novHE50" type="number" min="0" step="0.01" value="0"></div>
          <div><label>Horas extra al 100%</label><input id="novHE100" type="number" min="0" step="0.01" value="0"></div>
          <div><label>Feriados trabajados (días)</label><input id="novFeriados" type="number" min="0" step="1" value="0"></div>
          <div><label>Feriados no trabajados (días)</label><input id="novFeriadosNoTrab" type="number" min="0" step="1" value="0"><small style="color:#6b7280">Calcula automáticamente el plus feriado.</small></div>
          <div><label>Premios ($)</label><input id="novPremios" type="number" min="0" step="0.01" value="0"></div>
          <div><label>Tratamiento del premio</label><select id="novTipoPremio"><option value="pendiente">Pendiente de definir (no calcular)</option><option value="remunerativo">Remunerativo (integra aportes)</option><option value="no_remunerativo">No remunerativo</option></select></div>
          <div><label>Descuentos adicionales ($)</label><input id="novDescuentos" type="number" min="0" step="0.01" value="0"></div>
          <div id="novFarmacia" style="display:none;grid-column:1/-1;border:1px solid var(--borde);border-radius:8px;padding:12px">
            <b>Adicionales Farmacia — CCT 414/05</b>
            <p style="font-size:.82rem;color:#6b7280;margin:5px 0 10px">Marcá únicamente las condiciones reales del trabajador. La app aplica los porcentajes del convenio.</p>
            <label>Función especial</label>
            <select id="novRolFarmacia">
              <option value="">Ninguna</option>
              <option value="director">Dirección técnica</option>
              <option value="auxiliar_con">Auxiliar con bloqueo de título</option>
              <option value="auxiliar_sin">Auxiliar sin bloqueo de título</option>
            </select>
            <div class="fila" style="margin-top:8px">
              <label><input id="novTituloFarmaceutico" type="checkbox"> Título farmacéutico</label>
              <label><input id="novTituloAuxiliar" type="checkbox"> Título auxiliar</label>
              <label><input id="novTituloSecundario" type="checkbox"> Título secundario</label>
              <label><input id="novCajero" type="checkbox"> Función de cajero</label>
              <label><input id="novAdminPerfumeria" type="checkbox"> Administración o perfumería</label>
              <label><input id="novBicicleta" type="checkbox"> Uso de bicicleta/ciclomotor</label>
              <label><input id="novFallaCaja" type="checkbox" onchange="actualizarFallaCaja()"> Fondo por falla de caja</label>
              <div id="novFallaCajaDatos" style="display:none"><label>Faltantes absorbidos por el fondo ($)</label><input id="novFaltanteCaja" type="number" min="0" step="0.01" value="0"></div>
              <div><label>Idiomas usados en la tarea</label><input id="novIdiomas" type="number" min="0" step="1" value="0"></div>
            </div>
            <div style="margin-top:10px;border-top:1px solid var(--borde);padding-top:10px">
              <label><input id="novNocturnoVoluntario" type="checkbox" onchange="actualizarNocturnoFarmacia()"> Servicio nocturno voluntario o extendido (21 a 6)</label>
              <div id="novNocturnoDatos" class="fila" style="display:none;margin-top:8px">
                <div><label>Horas nocturnas del mes</label><input id="novHorasNocturnas" type="number" min="0" step="0.01" value="0"></div>
                <div><label>Horas totales trabajadas del mes</label><input id="novHorasTotales" type="number" min="0" step="0.01" value="0"></div>
              </div>
              <p style="font-size:.78rem;color:#6b7280;margin:6px 0 0">No marcar para turno obligatorio, sereno ni vigilancia: el art. 17 los excluye del recargo del 100%.</p>
            </div>
          </div>
          <div id="novSanidad" style="display:none;grid-column:1/-1;border:1px solid var(--borde);border-radius:8px;padding:12px">
            <b>Adicionales Sanidad — CCT 122/75</b>
            <p style="font-size:.82rem;color:#6b7280;margin:5px 0 10px">Marcá solamente condiciones efectivamente trabajadas. Los regímenes de sector son alternativos entre sí.</p>
            <label>Régimen especial de sector</label>
            <select id="novSectorSanidad">
              <option value="">Ninguno</option>
              <option value="TERAPIA_8H">Enfermería en terapia, clímax, coronaria, nursery o riñón artificial (8 h)</option>
              <option value="MUCAMA_SECTOR_ESPECIAL">Mucama en sector especial</option>
              <option value="MENTAL_ENFERMERIA">Salud mental con tareas de enfermería</option>
              <option value="MENTAL_TERAPIA">Salud mental: terapia, vigilancia o aislamiento</option>
              <option value="MENTAL_OTRAS_TAREAS">Otras tareas en área de salud mental</option>
            </select>
            <div class="fila" style="margin-top:8px">
              <label><input id="novElectricistaSanidad" type="checkbox"> Electricista con título habilitante</label>
              <label><input id="novOperadorSanidad" type="checkbox"> Operador de máquinas contables</label>
              <label><input id="novLaboratorioSanidad" type="checkbox"> Laboratorio en área cerrada</label>
              <label><input id="novRayosSanidad" type="checkbox"> Jornada de 48 h en rayos o laboratorio</label>
            </div>
            <div style="margin-top:10px;border-top:1px solid var(--borde);padding-top:10px">
              <label><input id="novNocturnidadSanidad" type="checkbox" onchange="actualizarNocturnidadSanidad()"> Trabajo entre las 22:00 y las 06:00</label>
              <div id="novNocturnidadSanidadDatos" class="fila" style="display:none;margin-top:8px">
                <div><label>Horas nocturnas del mes</label><input id="novHorasNocturnasSanidad" type="number" min="0" step="0.01" value="0"></div>
                <div><label>Horas totales trabajadas del mes</label><input id="novHorasTotalesSanidad" type="number" min="0" step="0.01" value="0"></div>
              </div>
            </div>
          </div>
          <div style="grid-column:1/-1"><label>Observaciones</label><textarea id="novObservaciones" rows="3" placeholder="Detalle opcional"></textarea></div>
        </div>
        <div style="display:flex;gap:8px;margin-top:10px">
          <button class="chico" id="btnGuardarNovedad" onclick="guardarNovedad()">Guardar novedad</button>
          <button class="chico secundario" onclick="cancelarNovedad()">Cancelar</button>
        </div>
        <div class="error" id="novFormError"></div>
      </div>

      <div class="error" id="novError"></div>
      <div class="ok" id="novOk"></div>
      <table id="tablaNovedades" class="tabla-movil" style="display:none"><thead><tr><th>Empleado</th><th>Días</th><th>Faltas</th><th>Extras</th><th>Premios / descuentos</th><th></th></tr></thead><tbody></tbody></table>
      <p id="sinNovedades" style="margin-top:10px;color:#6b7280;font-size:.9rem">No hay novedades cargadas para este mes.</p>
    </div>

    <div class="tarjeta">
      <h2>Liquidar sueldos</h2>
      <div class="fila">
        <div><label>Mes a liquidar</label><input id="periodo" type="month" onchange="cargarConvenios();cargarCarpetas();mostrarEstadoNormativo()"></div>
        <div style="display:flex;align-items:end"><button onclick="liquidar()" style="width:100%">Liquidar todos los empleados</button></div>
      </div>
      <div id="estadoNormativo" style="margin-top:12px;font-size:.9rem"></div>
      <div class="error" id="liqError"></div>
      <div id="resultados"></div>
    </div>

    <div class="tarjeta">
      <div class="cabecera-seccion">
        <h2>Carpeta mensual</h2>
        <button class="chico secundario" onclick="cargarCarpetas()">Actualizar historial</button>
      </div>
      <p style="font-size:.85rem;color:#6b7280">Cada liquidación conserva una versión de sólo lectura. Las correcciones no borran las anteriores.</p>
      <div class="error" id="carpetasError"></div>
      <table id="tablaCarpetas" class="tabla-movil" style="display:none"><thead><tr><th>Mes</th><th>Versión</th><th>Estado</th><th>Creada</th><th>Huella</th></tr></thead><tbody></tbody></table>
      <p id="sinCarpetas" style="margin-top:10px;color:#6b7280;font-size:.9rem">Todavía no hay carpetas generadas para este mes.</p>
    </div>
  </div>
</div>

<script>
const $ = id => document.getElementById(id);
let empleadosCache = {};
let editandoEmpleadoId = null;
let convenios = [];
let obraSocialSugeridaAnterior = '';
let empresaCache = {razon_social:'', cuit:''};
let ultimaLiq = null;
let novedadesCache = {};
let editandoNovedadId = null;

function fmt(n){ return Number(n).toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2}); }
function token(){ return localStorage.getItem('sc_access'); }
function mostrarTab(t){
  $('formIngresar').style.display = t==='ingresar'?'block':'none';
  $('formCrear').style.display   = t==='crear'?'block':'none';
  $('tabIngresar').className = t==='ingresar'?'':'inactivo';
  $('tabCrear').className    = t==='crear'?'':'inactivo';
  ocultar('authError');
}
function mostrarError(id,msg){ const e=$(id); e.textContent=msg; e.style.display='block'; }
function ocultar(id){ $(id).style.display='none'; }

let renovacionEnCurso=null;
async function renovarSesion(){
  const refresh=localStorage.getItem('sc_refresh');
  if(!refresh) return false;
  if(!renovacionEnCurso){
    renovacionEnCurso=(async()=>{
      try{
        const r=await fetch('/auth/refresh',{
          method:'POST',headers:{'Content-Type':'application/json'},
          body:JSON.stringify({refresh_token:refresh})
        });
        if(!r.ok) return false;
        const d=await r.json();
        localStorage.setItem('sc_access',d.access_token);
        localStorage.setItem('sc_refresh',d.refresh_token);
        return true;
      }catch(e){ return false; }
      finally{ renovacionEnCurso=null; }
    })();
  }
  return renovacionEnCurso;
}

async function api(ruta, metodo='GET', body=null, reintento=true){
  const h = {'Content-Type':'application/json'};
  if(token()) h['Authorization'] = 'Bearer ' + token();
  const r = await fetch(ruta,{method:metodo,headers:h,body:body?JSON.stringify(body):null});
  if(r.status===401 && token() && reintento){
    if(await renovarSesion()) return api(ruta,metodo,body,false);
    salir();
    throw new Error('Tu sesión venció. Ingresá de nuevo.');
  }
  const data = await r.json().catch(()=>({detail:'Error inesperado'}));
  if(!r.ok){
    let msg = data.detail;
    if(Array.isArray(msg)) msg = msg.map(x=>{
      if(x.type==='date_from_datetime_parsing'||x.type==='date_type'||/valid date/i.test(x.msg||''))
        return 'Revisá la fecha: escribí los 8 números de día, mes y año';
      return x.msg;
    }).join('. ');
    throw new Error(msg || 'Error ' + r.status);
  }
  return data;
}

function guardarSesion(d){
  localStorage.setItem('sc_access', d.access_token);
  localStorage.setItem('sc_refresh', d.refresh_token);
  entrar();
}
async function crearCuenta(){
  ocultar('authError');
  try{
    const d = await api('/auth/register','POST',{
      razon_social:$('rzRazon').value.trim(), cuit:$('rzCuit').value.replace(/\D/g,''),
      email:$('rzEmail').value.trim(), password:$('rzPass').value });
    guardarSesion(d);
  }catch(e){ mostrarError('authError', e.message); }
}
async function ingresar(){
  ocultar('authError');
  try{
    const d = await api('/auth/login','POST',{email:$('liEmail').value.trim(), password:$('liPass').value});
    guardarSesion(d);
  }catch(e){ mostrarError('authError', e.message); }
}
function salir(){ localStorage.clear(); $('app').style.display='none'; $('auth').style.display='block'; $('quien').textContent=''; }

async function entrar(){
  $('auth').style.display='none'; $('app').style.display='block';
  $('quien').textContent='Sesión iniciada';
  const hoy = new Date();
  $('periodo').value = hoy.toISOString().slice(0,7);
  $('novPeriodo').value = $('periodo').value;
  try{ empresaCache = await api('/empresa'); }catch(e){ /* silencioso */ }
  await cargarConvenios();
  await cargarEmpleados();
  await cargarNovedades();
  await mostrarEstadoNormativo();
  await cargarCarpetas();
}
function toggleAlta(){ const a=$('alta'); a.style.display = a.style.display==='none'?'block':'none'; }

const IDENTIDAD_CONVENIO={
  '414/05':{actividad:'Farmacia',sindicato:'ADEF',obraSocial:'OSADEF - Obra Social de las Asociaciones de Empleados de Farmacia'},
  '122/75':{actividad:'Sanidad',sindicato:'FATSA',obraSocial:'OSPSA - Obra Social del Personal de la Sanidad Argentina'},
  '130/75':{actividad:'Comercio',sindicato:'FAECYS',obraSocial:'OSECAC - Obra Social de Empleados de Comercio'}
};
function actividadConvenio(c){
  const conocida=IDENTIDAD_CONVENIO[c.numero];
  if(conocida) return conocida.actividad;
  const texto=`${c.nombre||''} ${c.sindicato||''}`.toLowerCase();
  if(texto.includes('sanidad')||texto.includes('fatsa')) return 'Sanidad';
  if(texto.includes('farmac')) return 'Farmacia';
  if(texto.includes('comerc')||texto.includes('faecys')) return 'Comercio';
  if(texto.includes('metal')||texto.includes('uom')) return 'Metalúrgicos';
  if(texto.includes('gastron')||texto.includes('hotel')||texto.includes('uthgra')) return 'Gastronomía y hotelería';
  if(texto.includes('camion')||texto.includes('fedcam')) return 'Camioneros';
  if(texto.includes('constru')||texto.includes('uocra')) return 'Construcción';
  return c.nombre||'Otra actividad';
}
function fechaParaPantalla(valor){
  if(!valor) return '';
  const m=String(valor).match(/^(\d{4})-(\d{2})-(\d{2})$/);
  return m?`${m[3]}/${m[2]}/${m[1]}`:String(valor);
}
function formatearFecha(campo){
  const numeros=String(campo.value||'').replace(/\D/g,'').slice(0,8);
  let texto=numeros.slice(0,2);
  if(numeros.length>2) texto+='/'+numeros.slice(2,4);
  if(numeros.length>4) texto+='/'+numeros.slice(4,8);
  campo.value=texto;
}
function fechaIso(valor,nombre){
  const texto=String(valor||'').trim();
  if(!texto) return null;
  let d,m,a,partes=texto.match(/^(\d{1,2})[\/-](\d{1,2})[\/-](\d{4})$/);
  if(partes){d=Number(partes[1]);m=Number(partes[2]);a=Number(partes[3]);}
  else{
    partes=texto.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
    if(!partes) throw new Error(`${nombre}: usá DD/MM/AAAA, por ejemplo 15/08/1974.`);
    a=Number(partes[1]);m=Number(partes[2]);d=Number(partes[3]);
  }
  const prueba=new Date(Date.UTC(a,m-1,d));
  if(prueba.getUTCFullYear()!==a||prueba.getUTCMonth()!==m-1||prueba.getUTCDate()!==d)
    throw new Error(`${nombre}: la fecha no existe.`);
  return `${String(a).padStart(4,'0')}-${String(m).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
}

async function cargarConvenios(){
  try{
    const periodo=$('periodo').value;
    convenios = await api('/convenios'+(periodo?'?periodo='+encodeURIComponent(periodo):''));
    const actividades=[...new Set(convenios.map(actividadConvenio))].sort((a,b)=>a.localeCompare(b,'es'));
    const selActividad=$('eActividad'); selActividad.innerHTML='';
    actividades.forEach(nombre=>{
      const o=document.createElement('option');
      o.value=nombre; o.textContent=nombre; selActividad.appendChild(o);
    });
    const primeroVigente=convenios.find(c=>c.tiene_escala_vigente);
    if(primeroVigente) selActividad.value=actividadConvenio(primeroVigente);
    llenarConvenios(primeroVigente?primeroVigente.numero:null);
  }catch(e){ /* silencioso */ }
}
function llenarConvenios(preseleccion=null){
  const actividad=$('eActividad').value;
  const sel=$('eConvenio'); sel.innerHTML='';
  convenios.filter(c=>actividadConvenio(c)===actividad).forEach(c=>{
    const o=document.createElement('option');
    const identidad=IDENTIDAD_CONVENIO[c.numero];
    const sindicato=identidad?identidad.sindicato:(c.sindicato||'Sin sindicato informado');
    o.value=c.numero; o.textContent=`CCT ${c.numero} — ${sindicato}`;
    if(!c.tiene_escala_vigente) o.textContent+=' — sin escala vigente';
    sel.appendChild(o);
  });
  const elegida=preseleccion||[...sel.options].find(o=>!o.disabled)?.value;
  if(elegida) sel.value=elegida;
  llenarCategorias();
}
function llenarCategorias(){
  const c = convenios.find(x=>x.numero===$('eConvenio').value);
  const sel = $('eCategoria'); sel.innerHTML='';
  (c?c.categorias:[]).forEach(cat=>{
    const o=document.createElement('option'); o.value=cat; o.textContent=cat; sel.appendChild(o);
  });
  const identidad=IDENTIDAD_CONVENIO[$('eConvenio').value];
  $('eSindicato').value=identidad?identidad.sindicato:(c?c.sindicato:'');
  const obraActual=$('eObraSocial').value.trim();
  if(identidad && (!obraActual||obraActual===obraSocialSugeridaAnterior)){
    $('eObraSocial').value=identidad.obraSocial;
    obraSocialSugeridaAnterior=identidad.obraSocial;
  }
}

async function cargarEmpleados(){
  try{
    const lista = await api('/empleados');
    empleadosCache = {};
    const tb = $('tablaEmpleados').querySelector('tbody'); tb.innerHTML='';
    lista.forEach(e=>{
      empleadosCache[e.id] = e;
      const tr=document.createElement('tr');
      tr.innerHTML = `<td data-label="Empleado">${e.apellido}, ${e.nombre}</td><td data-label="CUIL">${e.cuil}</td><td data-label="Convenio">${e.cct_numero}</td><td data-label="Categoría">${e.categoria}</td><td data-label="Ingreso">${e.fecha_ingreso}</td><td class="acciones-celda"><div class="acciones-tabla"><button class="chico secundario" onclick="editarEmpleado('${e.id}')" title="Editar">✏️ Editar</button><button class="chico secundario" onclick="borrarEmpleado('${e.id}','${(e.apellido||'')+', '+(e.nombre||'')}')" title="Eliminar">🗑 Eliminar</button></div></td>`;
      tb.appendChild(tr);
    });
    $('sinEmpleados').style.display = lista.length? 'none':'block';
    $('tablaEmpleados').style.display = lista.length? 'table':'none';
    const novSel = $('novEmpleado');
    novSel.innerHTML = '<option value="">Elegí un empleado…</option>';
    lista.forEach(e=>{
      const o=document.createElement('option');
      o.value=e.id; o.textContent=`${e.apellido}, ${e.nombre}`; novSel.appendChild(o);
    });
  }catch(e){ /* silencioso */ }
}

function numeroNov(id){ return Number($(id).value || 0); }
const checksFarmacia=['novTituloFarmaceutico','novTituloAuxiliar','novTituloSecundario','novCajero','novAdminPerfumeria','novBicicleta','novFallaCaja'];
function actualizarAdicionalesFarmacia(){
  const emp=empleadosCache[$('novEmpleado').value];
  $('novFarmacia').style.display=emp && emp.cct_numero==='414/05'?'block':'none';
}
const checksSanidad=['novElectricistaSanidad','novOperadorSanidad','novLaboratorioSanidad','novRayosSanidad'];
function actualizarAdicionalesSanidad(){
  const emp=empleadosCache[$('novEmpleado').value];
  $('novSanidad').style.display=emp && emp.cct_numero==='122/75'?'block':'none';
}
function actualizarAdicionalesConvenio(){
  actualizarAdicionalesFarmacia();
  actualizarAdicionalesSanidad();
}
function actualizarNocturnidadSanidad(){
  $('novNocturnidadSanidadDatos').style.display=$('novNocturnidadSanidad').checked?'grid':'none';
}
function actualizarNocturnoFarmacia(){
  $('novNocturnoDatos').style.display=$('novNocturnoVoluntario').checked?'grid':'none';
}
function actualizarFallaCaja(){
  $('novFallaCajaDatos').style.display=$('novFallaCaja').checked?'block':'none';
}
function limpiarAdicionalesFarmacia(){
  $('novRolFarmacia').value=''; $('novIdiomas').value='0';
  $('novNocturnoVoluntario').checked=false;
  $('novHorasNocturnas').value='0'; $('novHorasTotales').value='0';
  $('novFaltanteCaja').value='0';
  checksFarmacia.forEach(id=>$(id).checked=false);
  actualizarFallaCaja();
  actualizarNocturnoFarmacia();
  actualizarAdicionalesFarmacia();
}
function limpiarAdicionalesSanidad(){
  $('novSectorSanidad').value='';
  checksSanidad.forEach(id=>$(id).checked=false);
  $('novNocturnidadSanidad').checked=false;
  $('novHorasNocturnasSanidad').value='0';
  $('novHorasTotalesSanidad').value='0';
  actualizarNocturnidadSanidad();
  actualizarAdicionalesSanidad();
}
function datosAdicionalesFarmacia(){
  const emp=empleadosCache[$('novEmpleado').value];
  if(!emp || emp.cct_numero!=='414/05') return {adicionales_convencionales:[],cantidades_adicionales:{}};
  const codigos=[]; const cantidades={};
  const rol=$('novRolFarmacia').value;
  if(rol==='director') codigos.push('DIRECCION_TECNICA','COMPLEMENTO_DIRECCION');
  if(rol==='auxiliar_con') codigos.push('AUXILIAR_CON_BLOQUEO');
  if(rol==='auxiliar_sin') codigos.push('AUXILIAR_SIN_BLOQUEO');
  const opciones={novTituloFarmaceutico:'TITULO_FARMACEUTICO',novTituloAuxiliar:'TITULO_AUXILIAR',novTituloSecundario:'TITULO_SECUNDARIO',novCajero:'ADICIONAL_CAJERO',novAdminPerfumeria:'ADMIN_PERFUMERIA',novBicicleta:'BICICLETA_CICLOMOTOR',novFallaCaja:'FALLA_CAJA'};
  Object.entries(opciones).forEach(([id,codigo])=>{if($(id).checked) codigos.push(codigo);});
  if($('novFallaCaja').checked) cantidades.FALLA_CAJA=numeroNov('novFaltanteCaja');
  const idiomas=numeroNov('novIdiomas');
  if(idiomas>0){codigos.push('IDIOMA'); cantidades.IDIOMA=idiomas;}
  if($('novNocturnoVoluntario').checked){
    codigos.push('NOCTURNO_VOLUNTARIO');
    cantidades.NOCTURNO_VOLUNTARIO=numeroNov('novHorasNocturnas');
    cantidades.HORAS_TOTALES_PERIODO=numeroNov('novHorasTotales');
  }
  return {adicionales_convencionales:codigos,cantidades_adicionales:cantidades};
}
function datosAdicionalesSanidad(){
  const emp=empleadosCache[$('novEmpleado').value];
  if(!emp || emp.cct_numero!=='122/75') return {adicionales_convencionales:[],cantidades_adicionales:{}};
  const codigos=[]; const cantidades={};
  const sector=$('novSectorSanidad').value;
  if(sector) codigos.push(sector);
  const opciones={novElectricistaSanidad:'ELECTRICISTA_TITULO',novOperadorSanidad:'OPERADOR_MAQUINAS_CONTABLES',novLaboratorioSanidad:'LAB_AREA_CERRADA',novRayosSanidad:'RAYOS_LAB_48H'};
  Object.entries(opciones).forEach(([id,codigo])=>{if($(id).checked) codigos.push(codigo);});
  if($('novNocturnidadSanidad').checked){
    codigos.push('NOCTURNIDAD');
    cantidades.NOCTURNIDAD=numeroNov('novHorasNocturnasSanidad');
    cantidades.HORAS_TOTALES_PERIODO=numeroNov('novHorasTotalesSanidad');
  }
  return {adicionales_convencionales:codigos,cantidades_adicionales:cantidades};
}
function datosAdicionalesConvenio(){
  const emp=empleadosCache[$('novEmpleado').value];
  if(emp && emp.cct_numero==='414/05') return datosAdicionalesFarmacia();
  if(emp && emp.cct_numero==='122/75') return datosAdicionalesSanidad();
  return {adicionales_convencionales:[],cantidades_adicionales:{}};
}
function limpiarNovedad(){
  editandoNovedadId=null;
  $('novEmpleado').value=''; $('novEmpleado').disabled=false;
  ['novDias','novFaltasJ','novFaltasI','novLicencias','novVacaciones','novHE50','novHE100','novFeriados','novFeriadosNoTrab','novPremios','novDescuentos'].forEach(id=>$(id).value='0');
  $('novObservaciones').value='';
  $('novTipoPremio').value='pendiente';
  limpiarAdicionalesFarmacia();
  limpiarAdicionalesSanidad();
  $('tituloNovedad').textContent='Nueva novedad';
  $('btnGuardarNovedad').textContent='Guardar novedad';
  ocultar('novFormError');
}
function toggleNovedad(){
  const f=$('formNovedad');
  if(f.style.display==='none'){ limpiarNovedad(); f.style.display='block'; }
  else cancelarNovedad();
}
function cancelarNovedad(){ limpiarNovedad(); $('formNovedad').style.display='none'; }

async function cargarNovedades(){
  ocultar('novError');
  const periodo=$('novPeriodo').value;
  if(!periodo) return;
  try{
    const lista=await api('/novedades?periodo='+encodeURIComponent(periodo));
    novedadesCache={};
    const tb=$('tablaNovedades').querySelector('tbody'); tb.innerHTML='';
    lista.forEach(n=>{
      novedadesCache[n.id]=n;
      const emp=empleadosCache[n.empleado_id] || {apellido:'Empleado',nombre:''};
      const tr=document.createElement('tr');
      const faltas=Number(n.faltas_justificadas)+Number(n.faltas_injustificadas);
      const acciones=n.bloqueada
        ? '<span class="estado-edicion">🔒 Cerrada por liquidación confirmada</span>'
        : `<div class="acciones-tabla"><button class="chico secundario" onclick="editarNovedad('${n.id}')" title="Editar">✏️ Editar</button><button class="chico secundario" onclick="borrarNovedad('${n.id}')" title="Eliminar">🗑 Eliminar</button></div><span class="estado-edicion">Editable: la liquidación está calculada, no confirmada</span>`;
      const adicionales=(n.adicionales_convencionales||[]).length?`<br><small>Convenio: ${(n.adicionales_convencionales||[]).join(', ')}</small>`:'';
      tr.innerHTML=`<td data-label="Empleado">${emp.apellido}, ${emp.nombre}</td><td data-label="Días">${n.dias_trabajados}<br><small>Feriados: ${n.feriados_trabajados||0} trabajados · ${n.feriados_no_trabajados||0} no trabajados</small></td><td data-label="Faltas">${faltas}</td><td data-label="Extras">50%: ${n.horas_extra_50} · 100%: ${n.horas_extra_100}${adicionales}</td><td data-label="Premios / descuentos">$ ${fmt(n.premios)} / $ ${fmt(n.descuentos_adicionales)}</td><td class="acciones-celda">${acciones}</td>`;
      tb.appendChild(tr);
    });
    $('tablaNovedades').style.display=lista.length?'table':'none';
    $('sinNovedades').style.display=lista.length?'none':'block';
  }catch(e){ mostrarError('novError',e.message); }
}

async function mostrarEstadoNormativo(){
  const emp=Object.values(empleadosCache)[0];
  if(!emp || !$('periodo').value){ $('estadoNormativo').innerHTML=''; return; }
  try{
    const e=await api(`/convenios/${encodeURIComponent(emp.cct_numero)}/estado-normativo?periodo=${encodeURIComponent($('periodo').value)}`);
    const color=e.apto_produccion?'#065f46':'#92400e';
    const fondo=e.apto_produccion?'#d1fae5':'#fef3c7';
    const texto=e.apto_produccion?'Convenio verificado para uso real':'Convenio en revisión: usar sólo para pruebas';
    $('estadoNormativo').innerHTML=`<div style="background:${fondo};color:${color};border-radius:8px;padding:10px 14px"><b>${texto}</b> · ${e.resumen.aprobadas}/${e.resumen.total_reglas} reglas aprobadas · ${e.resumen.pendientes} pendientes</div>`;
  }catch(e){ $('estadoNormativo').innerHTML=''; }
}

function fechaHora(valor){
  if(!valor) return '—';
  const d=new Date(valor);
  return Number.isNaN(d.getTime())?valor:new Intl.DateTimeFormat('es-AR',{
    timeZone:'America/Argentina/Buenos_Aires',day:'2-digit',month:'2-digit',year:'numeric',
    hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'
  }).format(d);
}

async function cargarCarpetas(){
  ocultar('carpetasError');
  const periodo=$('periodo').value;
  if(!periodo) return;
  try{
    const lista=await api('/carpetas-mensuales?periodo='+encodeURIComponent(periodo));
    const tb=$('tablaCarpetas').querySelector('tbody'); tb.innerHTML='';
    lista.forEach(c=>{
      const tr=document.createElement('tr');
      const huella=(c.hash_sha256||'').slice(0,12);
      tr.innerHTML=`<td data-label="Mes">${c.periodo}</td><td data-label="Versión">v${c.version}</td><td data-label="Estado"><span class="etiqueta">${c.estado}</span></td><td data-label="Creada (Argentina)">${fechaHora(c.created_at)}</td><td data-label="Huella" title="${c.hash_sha256||''}"><code>${huella}${huella?'…':''}</code></td>`;
      tb.appendChild(tr);
    });
    $('tablaCarpetas').style.display=lista.length?'table':'none';
    $('sinCarpetas').style.display=lista.length?'none':'block';
  }catch(e){ mostrarError('carpetasError',e.message); }
}

function cuerpoNovedad(incluirEmpleado=true){
  const cuerpo={
    periodo:$('novPeriodo').value,
    dias_trabajados:numeroNov('novDias'),
    faltas_justificadas:numeroNov('novFaltasJ'),
    faltas_injustificadas:numeroNov('novFaltasI'),
    horas_extra_50:numeroNov('novHE50'),
    horas_extra_100:numeroNov('novHE100'),
    feriados_trabajados:numeroNov('novFeriados'),
    feriados_no_trabajados:numeroNov('novFeriadosNoTrab'),
    licencias:numeroNov('novLicencias'),
    vacaciones:numeroNov('novVacaciones'),
    premios:numeroNov('novPremios'),
    tipo_premio:$('novTipoPremio').value,
    descuentos_adicionales:numeroNov('novDescuentos'),
    observaciones:$('novObservaciones').value.trim()
  };
  Object.assign(cuerpo,datosAdicionalesConvenio());
  if(incluirEmpleado) cuerpo.empleado_id=$('novEmpleado').value;
  return cuerpo;
}

async function guardarNovedad(){
  ocultar('novFormError'); ocultar('novOk');
  if(!$('novEmpleado').value){ mostrarError('novFormError','Elegí un empleado.'); return; }
  try{
    const eraEdicion=Boolean(editandoNovedadId);
    const ruta=editandoNovedadId?'/novedades/'+editandoNovedadId:'/novedades';
    await api(ruta,editandoNovedadId?'PUT':'POST',cuerpoNovedad(!editandoNovedadId));
    cancelarNovedad();
    $('novOk').textContent=eraEdicion?'Novedad actualizada ✔':'Novedad guardada ✔';
    $('novOk').style.display='block';
    await cargarNovedades();
  }catch(e){ mostrarError('novFormError',e.message); }
}

function editarNovedad(id){
  const n=novedadesCache[id]; if(!n) return;
  editandoNovedadId=id;
  $('novEmpleado').value=n.empleado_id; $('novEmpleado').disabled=true;
  $('novDias').value=n.dias_trabajados; $('novFaltasJ').value=n.faltas_justificadas;
  $('novFaltasI').value=n.faltas_injustificadas; $('novLicencias').value=n.licencias;
  $('novVacaciones').value=n.vacaciones; $('novHE50').value=n.horas_extra_50;
  $('novHE100').value=n.horas_extra_100; $('novFeriados').value=n.feriados_trabajados||0;
  $('novFeriadosNoTrab').value=n.feriados_no_trabajados||0;
  $('novPremios').value=n.premios;
  $('novTipoPremio').value=n.tipo_premio||'pendiente';
  $('novDescuentos').value=n.descuentos_adicionales; $('novObservaciones').value=n.observaciones||'';
  limpiarAdicionalesFarmacia();
  limpiarAdicionalesSanidad();
  const adicionales=new Set(n.adicionales_convencionales||[]);
  if(adicionales.has('DIRECCION_TECNICA')) $('novRolFarmacia').value='director';
  else if(adicionales.has('AUXILIAR_CON_BLOQUEO')) $('novRolFarmacia').value='auxiliar_con';
  else if(adicionales.has('AUXILIAR_SIN_BLOQUEO')) $('novRolFarmacia').value='auxiliar_sin';
  const opciones={novTituloFarmaceutico:'TITULO_FARMACEUTICO',novTituloAuxiliar:'TITULO_AUXILIAR',novTituloSecundario:'TITULO_SECUNDARIO',novCajero:'ADICIONAL_CAJERO',novAdminPerfumeria:'ADMIN_PERFUMERIA',novBicicleta:'BICICLETA_CICLOMOTOR',novFallaCaja:'FALLA_CAJA'};
  Object.entries(opciones).forEach(([id,codigo])=>$(id).checked=adicionales.has(codigo));
  $('novIdiomas').value=(n.cantidades_adicionales||{}).IDIOMA||0;
  $('novNocturnoVoluntario').checked=adicionales.has('NOCTURNO_VOLUNTARIO');
  $('novHorasNocturnas').value=(n.cantidades_adicionales||{}).NOCTURNO_VOLUNTARIO||0;
  $('novHorasTotales').value=(n.cantidades_adicionales||{}).HORAS_TOTALES_PERIODO||0;
  $('novFaltanteCaja').value=(n.cantidades_adicionales||{}).FALLA_CAJA||0;
  const sectoresSanidad=['TERAPIA_8H','MUCAMA_SECTOR_ESPECIAL','MENTAL_ENFERMERIA','MENTAL_TERAPIA','MENTAL_OTRAS_TAREAS'];
  $('novSectorSanidad').value=sectoresSanidad.find(codigo=>adicionales.has(codigo))||'';
  const opcionesSanidad={novElectricistaSanidad:'ELECTRICISTA_TITULO',novOperadorSanidad:'OPERADOR_MAQUINAS_CONTABLES',novLaboratorioSanidad:'LAB_AREA_CERRADA',novRayosSanidad:'RAYOS_LAB_48H'};
  Object.entries(opcionesSanidad).forEach(([id,codigo])=>$(id).checked=adicionales.has(codigo));
  $('novNocturnidadSanidad').checked=adicionales.has('NOCTURNIDAD');
  $('novHorasNocturnasSanidad').value=(n.cantidades_adicionales||{}).NOCTURNIDAD||0;
  $('novHorasTotalesSanidad').value=(n.cantidades_adicionales||{}).HORAS_TOTALES_PERIODO||0;
  actualizarFallaCaja();
  actualizarNocturnoFarmacia();
  actualizarAdicionalesFarmacia();
  actualizarNocturnidadSanidad();
  actualizarAdicionalesSanidad();
  $('tituloNovedad').textContent='Editar novedad'; $('btnGuardarNovedad').textContent='Guardar cambios';
  $('formNovedad').style.display='block'; ocultar('novFormError');
}

async function borrarNovedad(id){
  if(!confirm('¿Eliminar esta novedad mensual?')) return;
  try{
    await api('/novedades/'+id,'DELETE');
    if(editandoNovedadId===id) cancelarNovedad();
    $('novOk').textContent='Novedad eliminada ✔'; $('novOk').style.display='block';
    await cargarNovedades();
  }catch(e){ mostrarError('novError',e.message); }
}

function editarEmpleado(id){
  ocultar('empError'); ocultar('empOk');
  const e = empleadosCache[id];
  if(!e) return;
  editandoEmpleadoId = id;
  $('eNombre').value = e.nombre || '';
  $('eApellido').value = e.apellido || '';
  $('eCuil').value = e.cuil || '';
  $('eFecha').value = fechaParaPantalla(e.fecha_ingreso);
  const convenioEmpleado=convenios.find(c=>c.numero===e.cct_numero);
  if(convenioEmpleado){
    $('eActividad').value=actividadConvenio(convenioEmpleado);
    llenarConvenios(e.cct_numero);
  }else llenarConvenios();
  if(e.categoria) $('eCategoria').value = e.categoria;
  $('eLegajo').value = e.legajo || '';
  $('eNacimiento').value = fechaParaPantalla(e.fecha_nacimiento);
  $('eSexo').value = e.sexo || '';
  $('eEstadoCivil').value = e.estado_civil || '';
  $('eDomicilio').value = e.domicilio || '';
  $('eHijos').value = e.cantidad_hijos || 0;
  $('eConyuge').value = e.conyuge_a_cargo ? 'true' : 'false';
  $('eObraSocial').value = e.obra_social || '';
  obraSocialSugeridaAnterior = '';
  $('eModalidad').value = e.modalidad_contrato || 'Tiempo indeterminado';
  $('eHorasSemanales').value = Number(e.proporcion_jornada || 1) * 48;
  $('eFormaPago').value = e.forma_pago || '';
  $('eCbu').value = e.cbu || '';
  $('eLugar').value = e.lugar_trabajo || '';
  $('eLocalidad').value = e.localidad || '';
  $('eFilial').value = e.filial_sindical || '';
  $('eRemun').value = e.remuneracion_pactada || '';

  $('btnGuardarEmp').textContent = 'Guardar cambios';
  $('btnCancelarEmp').style.display = 'inline-block';
  $('alta').style.display = 'block';
  toggleCbu();
}

function cancelarEdicion(){
  editandoEmpleadoId = null;
  obraSocialSugeridaAnterior = '';
  ['eNombre','eApellido','eCuil','eFecha','eNacimiento','eDomicilio','eLegajo','eObraSocial','eLugar','eCbu','eRemun','eFormaPago','eLocalidad','eFilial','eSindicato'].forEach(i=>$(i).value='');
  $('eHijos').value='0';
  $('eHorasSemanales').value='48';
  $('eConyuge').value='false';
  $('btnGuardarEmp').textContent = 'Guardar empleado';
  $('btnCancelarEmp').style.display = 'none';
  ocultar('empError'); ocultar('empOk');
  toggleCbu();
}

async function borrarEmpleado(id, nombre){
  if(!confirm('¿Eliminar a '+(nombre||'este empleado')+'? Esta acción no se puede deshacer.')) return;
  try{
    await api('/empleados/'+id, 'DELETE');
    if(editandoEmpleadoId === id) cancelarEdicion();
    await cargarEmpleados();
  }catch(e){ alert('No se pudo eliminar: '+e.message); }
}
function toggleCbu(){
  const fp=$('eFormaPago').value;
  $('lblCbu').textContent = fp==='3' ? 'CBU (22 dígitos) — obligatorio' : 'CBU (22 dígitos)';
}

let archivoExcelCargado = null;

async function descargarPlantillaExcel(){
  try{
    const h = {}; if(token()) h['Authorization'] = 'Bearer ' + token();
    const r = await fetch('/empleados/plantilla', {headers: h});
    if(!r.ok) throw new Error('No se pudo descargar la plantilla');
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'plantilla_empleados.xlsx';
    document.body.appendChild(a); a.click(); a.remove();
  }catch(e){ alert(e.message); }
}

async function subirExcelPreview(input){
  if(!input.files || !input.files[0]) return;
  const file = input.files[0];
  archivoExcelCargado = file;
  ocultar('excelError'); ocultar('excelOk');
  
  const formData = new FormData();
  formData.append('archivo', file);
  
  try{
    const h = {}; if(token()) h['Authorization'] = 'Bearer ' + token();
    const r = await fetch('/empleados/preview-import', {method: 'POST', headers: h, body: formData});
    const res = await r.json().catch(()=>({detail: 'Error procesando Excel'}));
    if(!r.ok) throw new Error(res.detail || 'Error en vista previa');
    
    const validos = res.validos || [];
    const errores = res.errores || [];
    const total = res.total_filas || 0;
    
    $('resumenExcel').textContent = `Se leyeron ${total} filas del archivo "${file.name}": ${validos.length} filas válidas para importar, ${errores.length} filas con errores.`;
    $('countValidos').textContent = validos.length;
    $('countErrores').textContent = errores.length;
    
    // Rellenar tabla de válidos
    const tbV = $('tablaValidos').querySelector('tbody'); tbV.innerHTML = '';
    validos.forEach(v=>{
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>Fila ${v.fila || '-'}</td><td>${v.apellido || ''}, ${v.nombre || ''}</td><td>${v.cuil || ''}</td><td>${v.cct_numero || ''}</td><td>${v.categoria || ''}</td><td>${v.fecha_ingreso || ''}</td>`;
      tbV.appendChild(tr);
    });
    $('boxValidos').style.display = validos.length ? 'block' : 'none';
    
    // Rellenar tabla de errores
    const tbE = $('tablaErrores').querySelector('tbody'); tbE.innerHTML = '';
    errores.forEach(e=>{
      const tr = document.createElement('tr');
      const detErr = Array.isArray(e.errores) ? e.errores.join('; ') : (e.errores || '');
      tr.innerHTML = `<td>Fila ${e.fila || '-'}</td><td>${e.cuil || e.nombre || '—'}</td><td>${detErr}</td>`;
      tbE.appendChild(tr);
    });
    $('boxErrores').style.display = errores.length ? 'block' : 'none';
    
    $('btnConfirmarImport').style.display = validos.length ? 'inline-block' : 'none';
    $('btnConfirmarImport').textContent = `Confirmar e importar (${validos.length} filas válidas)`;
    $('vistaPreviaExcel').style.display = 'block';
  }catch(e){
    alert('Error leyendo el archivo Excel: ' + e.message);
  } finally {
    input.value = '';
  }
}

async function confirmarImportacionExcel(){
  if(!archivoExcelCargado) return;
  ocultar('excelError'); ocultar('excelOk');
  
  const formData = new FormData();
  formData.append('archivo', archivoExcelCargado);
  
  try{
    const h = {}; if(token()) h['Authorization'] = 'Bearer ' + token();
    const r = await fetch('/empleados/import', {method: 'POST', headers: h, body: formData});
    const res = await r.json().catch(()=>({detail: 'Error en importación'}));
    if(!r.ok) throw new Error(res.detail || 'Error al importar');
    
    $('excelOk').textContent = `¡Importación completada! Se ingresaron ${res.importados} empleados válidos a la nómina ✔`;
    $('excelOk').style.display = 'block';
    $('btnConfirmarImport').style.display = 'none';
    archivoExcelCargado = null;
    await cargarEmpleados();
  }catch(e){
    mostrarError('excelError', e.message);
  }
}

function cancelarVistaPreviaExcel(){
  archivoExcelCargado = null;
  $('vistaPreviaExcel').style.display = 'none';
  ocultar('excelError'); ocultar('excelOk');
  const input = $('inputExcel'); if(input) input.value = '';
}

async function crearEmpleado(){
  ocultar('empError'); ocultar('empOk');
  const fp=$('eFormaPago').value;
  if(!fp){ mostrarError('empError','Elegí la forma de pago: la exige ARCA para el recibo y el F.931.'); return; }
  if(fp==='3' && $('eCbu').value.replace(/\D/g,'').length!==22){
    mostrarError('empError','Acreditación en cuenta: el CBU es obligatorio y debe tener 22 dígitos.'); return; }
  const horasSemanales=Number($('eHorasSemanales').value);
  if(!(horasSemanales>0 && horasSemanales<=48)){
    mostrarError('empError','Las horas semanales deben ser mayores que 0 y no superar 48.'); return;
  }
  try{
    const cuerpo = {
      nombre:$('eNombre').value.trim(), apellido:$('eApellido').value.trim(),
      cuil:$('eCuil').value.replace(/\D/g,''), fecha_ingreso:fechaIso($('eFecha').value,'Fecha de ingreso'),
      cct_numero:$('eConvenio').value, categoria:$('eCategoria').value,
      legajo:$('eLegajo').value.trim(),
      proporcion_jornada:horasSemanales/48,
      fecha_nacimiento:fechaIso($('eNacimiento').value,'Fecha de nacimiento'),
      sexo:$('eSexo').value || null,
      estado_civil:$('eEstadoCivil').value || null,
      domicilio:$('eDomicilio').value.trim() || null,
      cantidad_hijos:parseInt($('eHijos').value||'0',10),
      conyuge_a_cargo:$('eConyuge').value==='true',
      obra_social:$('eObraSocial').value.trim() || null,
      modalidad_contrato:$('eModalidad').value,
      cbu:$('eCbu').value.trim() || null,
      forma_pago:$('eFormaPago').value,
      lugar_trabajo:$('eLugar').value.trim() || null,
      localidad:$('eLocalidad').value.trim() || null,
      filial_sindical:$('eFilial').value.trim() || null,
      remuneracion_pactada:$('eRemun').value ? $('eRemun').value : null
    };
    const metodo = editandoEmpleadoId ? 'PUT' : 'POST';
    const ruta = editandoEmpleadoId ? '/empleados/' + editandoEmpleadoId : '/empleados';
    await api(ruta, metodo, cuerpo);
    const msgExito = editandoEmpleadoId ? 'Empleado actualizado ✔' : 'Empleado guardado ✔';
    cancelarEdicion();
    $('empOk').textContent = msgExito; $('empOk').style.display = 'block';
    await cargarEmpleados();

  }catch(e){ mostrarError('empError', e.message); }
}

const CS_APORTES = {APORTE_JUBILACION:'Aporte jubilatorio (SIPA 11%)', APORTE_LEY19032:'Aporte INSSJP/PAMI (Ley 19.032, 3%)', APORTE_OBRA_SOCIAL:'Aporte obra social (3%)'};
const CS_CONTRIB = {CONTRIB_JUBILACION:'Contribución jubilatoria', CONTRIB_OBRA_SOCIAL:'Contribución obra social', CONTRIB_INSSJP:'Contribución INSSJP/PAMI', CONTRIB_ASIG_FAM:'Contribución asignaciones familiares'};

function resumenF931(d){
  const ap = {}, co = {}; let remun = 0;
  d.detalles.forEach(det=>{
    remun += Number(det.bruto);
    det.conceptos.forEach(c=>{
      if(CS_APORTES[c.codigo]) ap[c.codigo]=(ap[c.codigo]||0)+Number(c.importe);
      if(CS_CONTRIB[c.codigo]) co[c.codigo]=(co[c.codigo]||0)+Number(c.importe);
    });
  });
  const totAp = Object.values(ap).reduce((a,b)=>a+b,0);
  const totCo = Object.values(co).reduce((a,b)=>a+b,0);
  let fAp = Object.keys(CS_APORTES).filter(k=>ap[k]).map(k=>`<tr><td>${CS_APORTES[k]}</td><td class="num">$ ${fmt(ap[k])}</td></tr>`).join('');
  let fCo = Object.keys(CS_CONTRIB).filter(k=>co[k]).map(k=>`<tr><td>${CS_CONTRIB[k]}</td><td class="num">$ ${fmt(co[k])}</td></tr>`).join('');
  return `<div class="tarjeta" style="border:2px solid var(--verde);margin-top:20px">
    <h2>Resumen de cargas sociales — F.931 (${d.periodo})</h2>
    <p style="font-size:.85rem;color:#6b7280;margin-bottom:8px">Empleados: <b>${d.detalles.length}</b> &nbsp;·&nbsp; Total remuneraciones: <b>$ ${fmt(remun)}</b></p>
    <table><thead><tr><th>Aportes del trabajador (retenidos)</th><th class="num">Importe</th></tr></thead>
      <tbody>${fAp}<tr><td><b>Total aportes</b></td><td class="num"><b>$ ${fmt(totAp)}</b></td></tr></tbody></table>
    <table style="margin-top:12px"><thead><tr><th>Contribuciones del empleador</th><th class="num">Importe</th></tr></thead>
      <tbody>${fCo}<tr><td><b>Total contribuciones</b></td><td class="num"><b>$ ${fmt(totCo)}</b></td></tr></tbody></table>
    <div style="display:flex;justify-content:space-between;margin-top:14px;flex-wrap:wrap;gap:8px">
      <span style="font-size:.8rem;color:#6b7280">La cuota sindical va por boleta aparte (no es carga social de ley). ART y FNE se sumarán al cargar sus parámetros.</span>
      <span class="neto">Total a depositar (F.931): $ ${fmt(totAp+totCo)}</span>
    </div>
  </div>`;
}

function resumenSindical(d){
  const grupos={};
  d.detalles.forEach(det=>{
    det.conceptos.forEach(c=>{
      if(!c.destino_pago || !c.codigo_boleta) return;
      const filial=det.filial_sindical||'';
      const localidad=det.localidad||'';
      const clave=[det.cct_numero||'',c.destino_pago,c.codigo_boleta,filial,localidad].join('|');
      if(!grupos[clave]) grupos[clave]={
        cct:det.cct_numero||'', destino:c.destino_pago, boleta:c.codigo_boleta,
        filial, localidad, importe:0, empleados:new Set(),
        canal:c.canal_pago||'', url:c.url_pago||'',
        vencimiento:c.regla_vencimiento||'', fuente:c.fuente_pago||''
      };
      ['canal_pago','url_pago','regla_vencimiento','fuente_pago'].forEach((campo,i)=>{
        const destinoCampo=['canal','url','vencimiento','fuente'][i];
        if(!grupos[clave][destinoCampo] && c[campo]) grupos[clave][destinoCampo]=c[campo];
      });
      grupos[clave].importe+=Number(c.importe);
      grupos[clave].empleados.add(det.empleado_id);
    });
  });
  const lista=Object.values(grupos);
  if(!lista.length) return `<div class="tarjeta" style="margin-top:20px;border:1px solid #f0c36d">
    <h2>Obligaciones sindicales</h2>
    <p style="color:#6b7280">No hay boletas sindicales configuradas con destino oficial para esta liquidación. No se generó ningún pago por suposición.</p>
  </div>`;
  let items=lista.map(g=>`<div class="detalle" style="margin-top:10px">
    <b>${g.destino}</b> <span class="etiqueta">CCT ${g.cct}</span>
    <div style="margin-top:6px"><b>Boleta:</b> ${g.boleta}</div>
    ${g.filial?`<div><b>Filial:</b> ${g.filial}</div>`:''}
    ${g.localidad?`<div><b>Localidad:</b> ${g.localidad}</div>`:''}
    ${g.canal?`<div><b>Canal oficial:</b> ${g.url?`<a href="${g.url}" target="_blank" rel="noopener">${g.canal}</a>`:g.canal}</div>`:''}
    ${g.vencimiento?`<div><b>Vencimiento:</b> ${g.vencimiento}</div>`:''}
    ${g.fuente?`<div><b>Fuente:</b> ${g.fuente}</div>`:''}
    <div><b>Empleados:</b> ${g.empleados.size}</div>
    <div class="neto" style="margin-top:6px">Importe agrupado: $ ${fmt(g.importe)}</div>
  </div>`).join('');
  return `<div class="tarjeta" style="margin-top:20px;border:2px solid var(--verde)">
    <h2>Obligaciones sindicales agrupadas</h2>
    <p style="font-size:.85rem;color:#6b7280">Control previo. No es una boleta presentable hasta incorporar y verificar el formulario oficial del gremio.</p>
    ${items}
  </div>`;
}

async function liquidar(){
  ocultar('liqError'); $('resultados').innerHTML='<p style="margin-top:12px">Calculando…</p>';
  try{
    const d = await api('/liquidaciones','POST',{periodo:$('periodo').value, tipo:'mensual', novedades:[]});
    ultimaLiq = d;
    if(!d.detalles.length){ $('resultados').innerHTML='<p style="margin-top:12px">No hay empleados para liquidar.</p>'; return; }
    renderLiquidacion();
    await cargarCarpetas();
  }catch(e){ $('resultados').innerHTML=''; mostrarError('liqError', e.message); }
}

function nombreTipoConcepto(tipo){
  return tipo==='deduccion'?'Descuento':tipo==='contribucion'?'Aporte del empleador':tipo==='no_remunerativo'?'No remunerativo':'Remunerativo';
}

function renderLiquidacion(){
    if(!ultimaLiq) return;
    const d=ultimaLiq;
    let html='';
    d.detalles.forEach(det=>{
      const emp = empleadosCache[det.empleado_id] || {apellido:'Empleado',nombre:'',cct_numero:''};
      let filas='';
      det.conceptos.forEach(c=>{
        const tipo = nombreTipoConcepto(c.tipo);
        const amparo = c.articulo_amparo? `<span class="etiqueta amparo">amparo ${c.articulo_amparo}</span>`:'';
        filas += `<tr><td>${c.descripcion} ${amparo}</td><td>${tipo}</td><td class="num">$ ${fmt(c.importe)}</td></tr>`;
      });
      html += `<div class="detalle">
        <b>${emp.apellido}, ${emp.nombre}</b> <span class="etiqueta">CCT ${emp.cct_numero}</span> <span class="etiqueta">${d.periodo}</span>
        <table><thead><tr><th>Concepto</th><th>Tipo</th><th class="num">Importe</th></tr></thead><tbody>${filas}</tbody></table>
        <div style="display:flex;justify-content:space-between;margin-top:10px;flex-wrap:wrap;gap:8px">
          <span>Bruto: <b>$ ${fmt(det.bruto)}</b> &nbsp;·&nbsp; Descuentos: <b>$ ${fmt(det.total_deducciones)}</b></span>
          <span class="neto">Neto a cobrar: $ ${fmt(det.neto)}</span>
        </div>
        <div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap">
          <button class="chico" onclick="abrirAjusteManual('${det.empleado_id}')">✏️ Revisar y ajustar antes de imprimir</button>
          <button class="chico secundario" onclick="descargarReciboPdf('${det.empleado_id}')">📄 Descargar recibo PDF — una hoja A4</button>
        </div>
        <div id="ajuste-${det.empleado_id}"></div>
        </div>`;
    });
    $('resultados').innerHTML = html + resumenF931(d) + resumenSindical(d);
}

function abrirAjusteManual(empId){
  const det=ultimaLiq&&ultimaLiq.detalles.find(x=>x.empleado_id===empId);
  const zona=$('ajuste-'+empId);
  if(!det||!zona) return;
  zona.innerHTML=`<div style="margin-top:12px;padding:12px;border:2px solid var(--verde);border-radius:8px;background:#f8fffd">
    <b>Edición manual del borrador</b>
    <p style="font-size:.84rem;color:#4b5563;margin:5px 0 10px">Podés corregir, eliminar o agregar conceptos. El PDF usará estos valores.</p>
    <div style="overflow:auto"><table><thead><tr><th>Descripción</th><th>Tipo</th><th>Importe</th><th>Cantidad</th><th>Base</th><th></th></tr></thead><tbody id="filas-ajuste-${empId}"></tbody></table></div>
    <button class="chico secundario" style="margin-top:8px" onclick="agregarFilaAjuste('${empId}')">＋ Agregar concepto</button>
    <label style="display:block;margin-top:10px"><b>Motivo del ajuste (obligatorio)</b><textarea id="motivo-ajuste-${empId}" rows="2" placeholder="Ej.: empleada fuera de convenio; se elimina aporte sindical" style="width:100%;margin-top:4px"></textarea></label>
    <div id="total-ajuste-${empId}" class="neto" style="margin-top:8px"></div>
    <div style="display:flex;gap:8px;margin-top:10px"><button class="chico" onclick="guardarAjusteManual('${empId}')">Guardar ajuste</button><button class="chico secundario" onclick="$('ajuste-${empId}').innerHTML=''">Cancelar</button></div>
  </div>`;
  det.conceptos.forEach(c=>agregarFilaAjuste(empId,c));
  recalcularVistaAjuste(empId);
}

function agregarFilaAjuste(empId,c={}){
  const tbody=$('filas-ajuste-'+empId); if(!tbody) return;
  const tr=document.createElement('tr'); tr.className='fila-ajuste';
  const codigo=c.codigo||('MANUAL_'+Date.now());
  tr.dataset.codigo=codigo;
  tr.dataset.regimen=c.regimen||'no_aplica';
  tr.innerHTML=`<td><input class="aj-desc" value="${String(c.descripcion||'Concepto manual').replace(/&/g,'&amp;').replace(/"/g,'&quot;')}" style="min-width:210px"></td>
    <td><select class="aj-tipo"><option value="remunerativo">Remunerativo</option><option value="no_remunerativo">No remunerativo</option><option value="deduccion">Descuento</option><option value="contribucion">Aporte empleador</option></select></td>
    <td><input class="aj-importe" type="number" min="0" step="0.01" value="${Number(c.importe||0).toFixed(2)}" style="width:120px"></td>
    <td><input class="aj-cantidad" type="number" min="0" step="0.01" value="${Number(c.cantidad===undefined?1:c.cantidad)}" style="width:80px"></td>
    <td><input class="aj-base" type="number" min="0" step="0.01" value="${c.base_calculo===null||c.base_calculo===undefined?'':Number(c.base_calculo).toFixed(2)}" style="width:120px"></td>
    <td><button class="chico secundario" title="Eliminar concepto" onclick="this.closest('tr').remove();recalcularVistaAjuste('${empId}')">🗑</button></td>`;
  tr.querySelector('.aj-tipo').value=c.tipo||'remunerativo';
  tr.querySelectorAll('input,select').forEach(x=>x.addEventListener('input',()=>recalcularVistaAjuste(empId)));
  tbody.appendChild(tr);
}

function conceptosDesdeEditor(empId){
  return [...document.querySelectorAll('#filas-ajuste-'+empId+' .fila-ajuste')].map((tr,i)=>({
    codigo:tr.dataset.codigo||('MANUAL_'+(i+1)), descripcion:tr.querySelector('.aj-desc').value.trim(),
    tipo:tr.querySelector('.aj-tipo').value, importe:Number(tr.querySelector('.aj-importe').value||0),
    cantidad:Number(tr.querySelector('.aj-cantidad').value||0),
    base_calculo:tr.querySelector('.aj-base').value===''?null:Number(tr.querySelector('.aj-base').value),
    unidad:'suma fija', regimen:tr.dataset.regimen||'no_aplica'
  }));
}

function recalcularVistaAjuste(empId){
  const conceptos=conceptosDesdeEditor(empId);
  const bruto=conceptos.filter(c=>c.tipo==='remunerativo'||c.tipo==='no_remunerativo').reduce((a,c)=>a+c.importe,0);
  const desc=conceptos.filter(c=>c.tipo==='deduccion').reduce((a,c)=>a+c.importe,0);
  const zona=$('total-ajuste-'+empId);
  if(zona) zona.textContent=`Vista previa — Bruto: $ ${fmt(bruto)} · Descuentos: $ ${fmt(desc)} · Neto: $ ${fmt(bruto-desc)}`;
}

async function guardarAjusteManual(empId){
  const conceptos=conceptosDesdeEditor(empId);
  const motivo=$('motivo-ajuste-'+empId).value.trim();
  if(conceptos.length<1){ alert('El recibo debe conservar al menos un concepto.'); return; }
  if(conceptos.some(c=>!c.descripcion)){ alert('Todos los conceptos necesitan descripción.'); return; }
  if(motivo.length<5){ alert('Escribí el motivo del ajuste (mínimo 5 caracteres).'); return; }
  try{
    const det=await api(`/liquidaciones/${ultimaLiq.id}/empleados/${empId}/ajuste-manual`,'PATCH',{motivo,conceptos});
    const pos=ultimaLiq.detalles.findIndex(x=>x.empleado_id===empId);
    ultimaLiq.detalles[pos]={...ultimaLiq.detalles[pos],...det};
    renderLiquidacion();
    alert('Ajuste guardado. El neto y el PDF ya usan los importes corregidos.');
  }catch(e){ alert(e.message||'No se pudo guardar el ajuste'); }
}

function antigTexto(fIngreso, periodo){
  if(!fIngreso) return '—';
  const ing = new Date(fIngreso+'T00:00:00');
  const p = periodo.split('-').map(Number);
  const ref = new Date(p[0], p[1]-1, 28);
  let a = ref.getFullYear()-ing.getFullYear();
  if(ref.getMonth()<ing.getMonth() || (ref.getMonth()===ing.getMonth() && ref.getDate()<ing.getDate())) a--;
  a=a<0?0:a;
  return a+' '+(a===1?'año':'años');
}
function pieSVG(vals, colors){
  const total = vals.reduce((a,b)=>a+b,0)||1;
  let ang=-90, paths='';
  const cx=90,cy=90,r=85;
  vals.forEach((v,i)=>{
    const frac=v/total, a2=ang+frac*360;
    const x1=cx+r*Math.cos(ang*Math.PI/180), y1=cy+r*Math.sin(ang*Math.PI/180);
    const x2=cx+r*Math.cos(a2*Math.PI/180), y2=cy+r*Math.sin(a2*Math.PI/180);
    const large=frac>0.5?1:0;
    paths+='<path d="M'+cx+','+cy+' L'+x1.toFixed(1)+','+y1.toFixed(1)+' A'+r+','+r+' 0 '+large+' 1 '+x2.toFixed(1)+','+y2.toFixed(1)+' Z" fill="'+colors[i]+'"/>';
    ang=a2;
  });
  return '<svg width="180" height="180" viewBox="0 0 180 180">'+paths+'</svg>';
}
function verRecibo(empId){
  if(!ultimaLiq) return;
  const det = ultimaLiq.detalles.find(x=>x.empleado_id===empId);
  if(!det) return;
  const emp = empleadosCache[empId] || {};
  const per = ultimaLiq.periodo;
  const haberes = det.conceptos.filter(c=>c.tipo==='remunerativo'||c.tipo==='no_remunerativo');
  const deduc = det.conceptos.filter(c=>c.tipo==='deduccion');
  const contrib = det.conceptos.filter(c=>c.tipo==='contribucion');
  const totalContrib = contrib.reduce((a,c)=>a+Number(c.importe),0);
  const neto=Number(det.neto), bruto=Number(det.bruto), totalDed=Number(det.total_deducciones);
  const costo = bruto + totalContrib;
  const filH = haberes.map(c=>'<tr><td>'+c.descripcion+'</td><td class="num">$ '+fmt(c.importe)+'</td><td></td></tr>').join('');
  const filD = deduc.map(c=>'<tr><td>'+c.descripcion+'</td><td></td><td class="num">$ '+fmt(c.importe)+'</td></tr>').join('');
  const filC = contrib.map(c=>'<tr><td>'+c.descripcion+'</td><td class="num">$ '+fmt(c.importe)+'</td></tr>').join('');
  const pie = pieSVG([neto, totalDed, totalContrib], ['#0f766e','#f59e0b','#6366f1']);
  const nom = (emp.apellido||'')+', '+(emp.nombre||'');
  const html = '<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><title>Recibo '+nom+' '+per+'</title>'
   +'<style>*{box-sizing:border-box;font-family:Arial,Helvetica,sans-serif}body{margin:0;background:#eef1f4;color:#111}'
   +'.hoja{background:#fff;max-width:800px;margin:16px auto;padding:24px;border:1px solid #ccc}'
   +'.barra{background:#0f766e;color:#fff;padding:10px 14px;border-radius:6px;display:flex;justify-content:space-between;align-items:center}'
   +'.marca-recibo{display:flex;align-items:center;gap:9px}.marca-recibo svg{width:40px;height:40px;flex:none}'
   +'.barra h1{font-size:1.05rem;margin:0}.barra small{opacity:.9}'
   +'.aviso{background:#fef3c7;border:1px solid #fcd34d;color:#92400e;font-size:.72rem;padding:6px 10px;border-radius:4px;margin:10px 0}'
   +'h2{font-size:.78rem;background:#e6efee;color:#0f766e;padding:5px 8px;margin:14px 0 6px;border-left:4px solid #0f766e;text-transform:uppercase;letter-spacing:.5px}'
   +'.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}.caja{border:1px solid #ddd;border-radius:6px;padding:10px;font-size:.8rem}'
   +'.dato{display:flex;justify-content:space-between;padding:2px 0;border-bottom:1px dotted #eee}'
   +'table{width:100%;border-collapse:collapse;font-size:.8rem}th,td{padding:5px 8px;border-bottom:1px solid #eee;text-align:left}'
   +'th{background:#f7f9f9}.num{text-align:right;font-variant-numeric:tabular-nums}.tot{font-weight:bold;background:#f7f9f9}'
   +'.neto{font-size:1.1rem;font-weight:bold;color:#0f766e}.resumen{display:flex;gap:20px;align-items:center;flex-wrap:wrap}'
   +'.ley{font-size:.8rem}.ley span{display:inline-block;width:12px;height:12px;border-radius:2px;margin-right:6px;vertical-align:middle}'
   +'.firma{margin-top:26px;display:flex;justify-content:space-between;font-size:.78rem;color:#374151}'
   +'.firma div{border-top:1px solid #999;padding-top:4px;width:45%;text-align:center}'
   +'a[x-apple-data-detectors]{color:inherit!important;text-decoration:none!important;font:inherit!important}'
   +'.btn{background:#0f766e;color:#fff;border:0;padding:10px 18px;border-radius:6px;font-size:.9rem;cursor:pointer;margin:12px auto;display:block}'
   +'@page{size:A4 portrait;margin:5mm}@media print{html,body{width:200mm;margin:0!important;padding:0!important;background:#fff;-webkit-print-color-adjust:exact;print-color-adjust:exact}'
   +'.hoja{border:0;margin:0!important;padding:0!important;width:200mm;max-width:200mm;min-height:0}.btn,.aviso{display:none!important}'
   +'.barra{padding:4px 8px;border-radius:3px}.barra h1{font-size:9pt}.barra small{font-size:7pt}.marca-recibo{gap:6px}.marca-recibo svg{width:26px;height:26px}'
   +'h2{font-size:7pt;margin:4px 0 2px;padding:2px 5px;border-left-width:3px}.grid2{gap:5px}.caja{padding:4px;font-size:7pt;border-radius:3px}.dato{padding:0;line-height:1.18}'
   +'table{font-size:7pt;line-height:1.12;page-break-inside:avoid}th,td{font-size:7pt;padding:1.5px 4px}.tot{page-break-inside:avoid}'
   +'.neto{font-size:9pt;margin-top:3px!important}.resumen{display:block;font-size:7pt;page-break-inside:avoid}.resumen svg{display:none}.ley{font-size:7pt;display:grid;grid-template-columns:1fr 1fr;gap:1px 10px}.ley div{margin:0!important}'
   +'.firma{margin-top:10px;font-size:7pt;page-break-inside:avoid}.firma div{padding-top:2px}h2,.barra,.grid2,.neto{page-break-inside:avoid}body{-webkit-text-size-adjust:100%}}</style></head><body>'
   +'<button class="btn" onclick="window.print()">⬇ Descargar / Imprimir PDF</button>'
   +'<div class="hoja">'
   +'<div class="barra"><div class="marca-recibo"><svg viewBox="0 0 64 64" role="img" aria-label="Logo Sueldo Claro"><path d="M12 7h27l10 10v25H12z" fill="none" stroke="#fff" stroke-width="5" stroke-linejoin="round"/><path d="M39 7v11h10M20 24h19M20 33h12" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/><path d="m31 45 8 8 15-18" fill="none" stroke="#fbbf24" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/></svg><div><b>Sueldo Claro</b><h1>RECIBO DE HABERES</h1></div></div><small>Anexo III · Dto. 407/2026 · Período '+per+'</small></div>'
   +'<div class="aviso">Documento de PRUEBA — valores a verificar por contador matriculado.</div>'
   +'<h2>A · Cabecera</h2><div class="grid2">'
   +'<div class="caja"><b>EMPLEADOR</b>'
   +'<div class="dato"><span>Razón social</span><b>'+(empresaCache.razon_social||'—')+'</b></div>'
   +'<div class="dato"><span>CUIT</span><b>'+(empresaCache.cuit||'—')+'</b></div></div>'
   +'<div class="caja"><b>TRABAJADOR</b>'
   +'<div class="dato"><span>Apellido y nombre</span><b>'+nom+'</b></div>'
   +'<div class="dato"><span>CUIL</span><b>'+(emp.cuil||'—')+'</b></div>'
   +'<div class="dato"><span>Legajo</span><b>'+(emp.legajo||'—')+'</b></div>'
   +'<div class="dato"><span>Categoría / CCT</span><b>'+(emp.categoria||'—')+' · '+(emp.cct_numero||'')+'</b></div>'
   +'<div class="dato"><span>Ingreso / Antig.</span><b>'+(emp.fecha_ingreso||'—')+' · '+antigTexto(emp.fecha_ingreso,per)+'</b></div>'
   +'<div class="dato"><span>Modalidad</span><b>'+(emp.modalidad_contrato||'—')+'</b></div></div></div>'
   +'<h2>B · Detalle de contribuciones patronales</h2>'
   +'<table><thead><tr><th>Concepto</th><th class="num">Importe</th></tr></thead><tbody>'+filC
   +'<tr class="tot"><td>Total contribuciones</td><td class="num">$ '+fmt(totalContrib)+'</td></tr></tbody></table>'
   +'<h2>C · Haberes y deducciones del trabajador</h2>'
   +'<table><thead><tr><th>Concepto</th><th class="num">Haberes</th><th class="num">Deducciones</th></tr></thead><tbody>'+filH+filD
   +'<tr class="tot"><td>Totales</td><td class="num">$ '+fmt(bruto)+'</td><td class="num">$ '+fmt(totalDed)+'</td></tr></tbody></table>'
   +'<div style="text-align:right;margin-top:8px" class="neto">NETO A COBRAR: $ '+fmt(neto)+'</div>'
   +'<h2>D · Resumen del costo laboral total</h2><div class="resumen">'+pie
   +'<div class="ley"><div><span style="background:#0f766e"></span>Salario de bolsillo (neto): <b>$ '+fmt(neto)+'</b></div>'
   +'<div><span style="background:#f59e0b"></span>Retenciones al trabajador: <b>$ '+fmt(totalDed)+'</b></div>'
   +'<div><span style="background:#6366f1"></span>Cargas patronales: <b>$ '+fmt(totalContrib)+'</b></div>'
   +'<div style="margin-top:6px;font-weight:bold">Costo laboral total: $ '+fmt(costo)+'</div></div></div>'
   +'<div class="firma"><div>Firma del empleador</div><div>Recibí conforme — Firma del trabajador</div></div>'
   +'</div></body></html>';
  const w = window.open('', '_blank');
  if(!w){ alert('Permití las ventanas emergentes para ver el recibo.'); return; }
  w.document.write(html); w.document.close();
}

async function descargarReciboPdf(empId, reintento=true){
  if(!ultimaLiq) return;
  const det=ultimaLiq.detalles.find(x=>x.empleado_id===empId);
  const emp=empleadosCache[empId]||{};
  if(!det) return;
  const domicilioEmpresa=prompt('Domicilio legal del empleador (obligatorio):',localStorage.getItem('sc_empresa_domicilio')||'');
  if(!domicilioEmpresa) return;
  const fechaPago=prompt('Fecha real de pago del sueldo (AAAA-MM-DD):',new Date().toISOString().slice(0,10));
  if(!fechaPago) return;
  const lugarPago=prompt('Lugar real de pago:',emp.lugar_trabajo||localStorage.getItem('sc_lugar_pago')||'');
  if(!lugarPago) return;
  const formasPago={'1':'Efectivo','2':'Cheque','3':'Acreditación en cuenta','4':'Otra'};
  const formaPago=prompt('Forma real de pago:',formasPago[emp.forma_pago]||localStorage.getItem('sc_forma_pago')||'');
  if(!formaPago) return;
  const fechaCargas=prompt('Fecha de pago de cargas sociales (AAAA-MM-DD):',localStorage.getItem('sc_fecha_cargas')||'');
  if(!fechaCargas) return;
  const lugarCargas=prompt('Lugar/canal de pago de cargas sociales:',localStorage.getItem('sc_lugar_cargas')||'ARCA');
  if(!lugarCargas) return;
  localStorage.setItem('sc_empresa_domicilio',domicilioEmpresa);
  localStorage.setItem('sc_lugar_pago',lugarPago);
  localStorage.setItem('sc_forma_pago',formaPago);
  localStorage.setItem('sc_fecha_cargas',fechaCargas);
  localStorage.setItem('sc_lugar_cargas',lugarCargas);
  const body={
    periodo:ultimaLiq.periodo,
    empresa:{...empresaCache,domicilio:domicilioEmpresa},
    empleado:{...emp,antiguedad:antigTexto(emp.fecha_ingreso,ultimaLiq.periodo)},
    pago:{fecha:fechaPago,lugar:lugarPago,forma:formaPago},
    cargas_sociales:{fecha:fechaCargas,lugar:lugarCargas},
    conceptos:det.conceptos.map(c=>({
      codigo:c.codigo||'',descripcion:c.descripcion,tipo:c.tipo,importe:c.importe,
      base_calculo:c.base_calculo,unidad:c.unidad,cantidad:c.cantidad
    })),
    bruto:det.bruto,total_deducciones:det.total_deducciones,neto:det.neto
  };
  const r=await fetch('/recibos/pdf',{
    method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+token()},
    body:JSON.stringify(body)
  });
  if(r.status===401 && reintento && await renovarSesion()) return descargarReciboPdf(empId,false);
  if(!r.ok){
    const e=await r.json().catch(()=>({detail:'No se pudo generar el PDF'}));
    alert(e.detail||'No se pudo generar el PDF'); return;
  }
  const blob=await r.blob();
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');
  a.href=url; a.download=`recibo-${ultimaLiq.periodo}-${(emp.apellido||'empleado').replace(/\\s+/g,'-')}.pdf`;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),60000);
}

if(token()) entrar();
else if(localStorage.getItem('sc_refresh')){
  renovarSesion().then(ok=>{ if(ok) entrar(); else salir(); });
}
</script>
</body>
</html>
"""
