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
          <div><label>Fecha de nacimiento</label><input id="eNacimiento" type="date"></div>
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
          <div><label>Fecha de ingreso</label><input id="eFecha" type="date"></div>
          <div><label>Legajo</label><input id="eLegajo" placeholder="0001"></div>
          <div><label>Convenio / Sindicato</label>
            <select id="eConvenio" onchange="llenarCategorias()"></select></div>
          <div><label>Categoría</label>
            <select id="eCategoria"></select></div>
          <div><label>Modalidad de contrato</label>
            <select id="eModalidad"><option>Tiempo indeterminado</option><option>Plazo fijo</option><option>Eventual</option><option>Temporada</option><option>Período de prueba</option></select></div>
          <div><label>Jornada</label>
            <select id="eJornada"><option value="1">Completa</option><option value="0.5">Media jornada</option></select></div>
          <div><label>Obra social</label><input id="eObraSocial" placeholder="OSECAC, OSPACA..."></div>
          <div><label>Lugar de trabajo / sucursal</label><input id="eLugar" placeholder="Casa central"></div>
          <div><label>Remuneración pactada (si supera el básico)</label><input id="eRemun" type="number" min="0" placeholder="opcional"></div>
        </div>

        <h3 style="font-size:.9rem;color:var(--verde);margin:14px 0 6px">Datos de pago</h3>
        <div class="fila">
          <div><label>Forma de pago * (la exige ARCA)</label>
            <select id="eFormaPago" onchange="toggleCbu()"><option value="">Elegí una opción…</option><option value="1">Efectivo</option><option value="2">Cheque</option><option value="3">Acreditación en cuenta (CBU)</option><option value="4">Otra</option></select></div>
          <div><label id="lblCbu">CBU (22 dígitos)</label><input id="eCbu" maxlength="22" placeholder="opcional"></div>
        </div>

        <h3 style="font-size:.9rem;color:var(--verde);margin:14px 0 6px">Datos sindicales (para cuota de afiliado — Art. 101)</h3>
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
      <table id="tablaEmpleados"><thead><tr><th>Apellido y nombre</th><th>CUIL</th><th>Convenio</th><th>Categoría</th><th>Ingreso</th><th></th></tr></thead><tbody></tbody></table>
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
          <div style="grid-column:1/-1"><label>Empleado</label><select id="novEmpleado"></select></div>
          <div><label>Días trabajados</label><input id="novDias" type="number" min="0" value="0"></div>
          <div><label>Faltas justificadas</label><input id="novFaltasJ" type="number" min="0" value="0"></div>
          <div><label>Faltas injustificadas</label><input id="novFaltasI" type="number" min="0" value="0"></div>
          <div><label>Licencias (días)</label><input id="novLicencias" type="number" min="0" value="0"></div>
          <div><label>Vacaciones (días)</label><input id="novVacaciones" type="number" min="0" value="0"></div>
          <div><label>Horas extra al 50%</label><input id="novHE50" type="number" min="0" step="0.01" value="0"></div>
          <div><label>Horas extra al 100%</label><input id="novHE100" type="number" min="0" step="0.01" value="0"></div>
          <div><label>Premios ($)</label><input id="novPremios" type="number" min="0" step="0.01" value="0"></div>
          <div><label>Tratamiento del premio</label><select id="novTipoPremio"><option value="pendiente">Pendiente de definir (no calcular)</option><option value="remunerativo">Remunerativo (integra aportes)</option><option value="no_remunerativo">No remunerativo</option></select></div>
          <div><label>Descuentos adicionales ($)</label><input id="novDescuentos" type="number" min="0" step="0.01" value="0"></div>
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
      <table id="tablaNovedades" style="display:none"><thead><tr><th>Empleado</th><th>Días</th><th>Faltas</th><th>Extras</th><th>Premios / descuentos</th><th></th></tr></thead><tbody></tbody></table>
      <p id="sinNovedades" style="margin-top:10px;color:#6b7280;font-size:.9rem">No hay novedades cargadas para este mes.</p>
    </div>

    <div class="tarjeta">
      <h2>Liquidar sueldos</h2>
      <div class="fila">
        <div><label>Mes a liquidar</label><input id="periodo" type="month" onchange="cargarCarpetas();mostrarEstadoNormativo()"></div>
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
      <table id="tablaCarpetas" style="display:none"><thead><tr><th>Mes</th><th>Versión</th><th>Estado</th><th>Creada</th><th>Huella</th></tr></thead><tbody></tbody></table>
      <p id="sinCarpetas" style="margin-top:10px;color:#6b7280;font-size:.9rem">Todavía no hay carpetas generadas para este mes.</p>
    </div>
  </div>
</div>

<script>
const $ = id => document.getElementById(id);
let empleadosCache = {};
let editandoEmpleadoId = null;
let convenios = [];
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

async function api(ruta, metodo='GET', body=null){
  const h = {'Content-Type':'application/json'};
  if(token()) h['Authorization'] = 'Bearer ' + token();
  const r = await fetch(ruta,{method:metodo,headers:h,body:body?JSON.stringify(body):null});
  if(r.status===401 && token()){ salir(); throw new Error('Tu sesión venció. Ingresá de nuevo.'); }
  const data = await r.json().catch(()=>({detail:'Error inesperado'}));
  if(!r.ok){
    let msg = data.detail;
    if(Array.isArray(msg)) msg = msg.map(x=>x.msg).join('. ');
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

async function cargarConvenios(){
  try{
    convenios = await api('/convenios');
    const sel = $('eConvenio'); sel.innerHTML='';
    convenios.forEach(c=>{
      const o=document.createElement('option');
      o.value=c.numero; o.textContent=`${c.nombre} (${c.sindicato}) — CCT ${c.numero}`;
      sel.appendChild(o);
    });
    llenarCategorias();
  }catch(e){ /* silencioso */ }
}
function llenarCategorias(){
  const c = convenios.find(x=>x.numero===$('eConvenio').value);
  const sel = $('eCategoria'); sel.innerHTML='';
  (c?c.categorias:[]).forEach(cat=>{
    const o=document.createElement('option'); o.value=cat; o.textContent=cat; sel.appendChild(o);
  });
}

async function cargarEmpleados(){
  try{
    const lista = await api('/empleados');
    empleadosCache = {};
    const tb = $('tablaEmpleados').querySelector('tbody'); tb.innerHTML='';
    lista.forEach(e=>{
      empleadosCache[e.id] = e;
      const tr=document.createElement('tr');
      tr.innerHTML = `<td>${e.apellido}, ${e.nombre}</td><td>${e.cuil}</td><td>${e.cct_numero}</td><td>${e.categoria}</td><td>${e.fecha_ingreso}</td><td><button class="chico secundario" onclick="editarEmpleado('${e.id}')" title="Editar">✏️</button> <button class="chico secundario" onclick="borrarEmpleado('${e.id}','${(e.apellido||'')+', '+(e.nombre||'')}')" title="Eliminar">🗑</button></td>`;
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
function limpiarNovedad(){
  editandoNovedadId=null;
  $('novEmpleado').value=''; $('novEmpleado').disabled=false;
  ['novDias','novFaltasJ','novFaltasI','novLicencias','novVacaciones','novHE50','novHE100','novPremios','novDescuentos'].forEach(id=>$(id).value='0');
  $('novObservaciones').value='';
  $('novTipoPremio').value='pendiente';
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
      tr.innerHTML=`<td>${emp.apellido}, ${emp.nombre}</td><td>${n.dias_trabajados}</td><td>${faltas}</td><td>50%: ${n.horas_extra_50} · 100%: ${n.horas_extra_100}</td><td>$ ${fmt(n.premios)} / $ ${fmt(n.descuentos_adicionales)}</td><td><button class="chico secundario" onclick="editarNovedad('${n.id}')" title="Editar">✏️</button> <button class="chico secundario" onclick="borrarNovedad('${n.id}')" title="Eliminar">🗑</button></td>`;
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
  return Number.isNaN(d.getTime())?valor:d.toLocaleString('es-AR');
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
      tr.innerHTML=`<td>${c.periodo}</td><td>v${c.version}</td><td><span class="etiqueta">${c.estado}</span></td><td>${fechaHora(c.created_at)}</td><td title="${c.hash_sha256||''}"><code>${huella}${huella?'…':''}</code></td>`;
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
    licencias:numeroNov('novLicencias'),
    vacaciones:numeroNov('novVacaciones'),
    premios:numeroNov('novPremios'),
    tipo_premio:$('novTipoPremio').value,
    descuentos_adicionales:numeroNov('novDescuentos'),
    observaciones:$('novObservaciones').value.trim()
  };
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
  $('novHE100').value=n.horas_extra_100; $('novPremios').value=n.premios;
  $('novTipoPremio').value=n.tipo_premio||'pendiente';
  $('novDescuentos').value=n.descuentos_adicionales; $('novObservaciones').value=n.observaciones||'';
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
  $('eFecha').value = e.fecha_ingreso || '';
  if(e.cct_numero) $('eConvenio').value = e.cct_numero;
  llenarCategorias();
  if(e.categoria) $('eCategoria').value = e.categoria;
  $('eLegajo').value = e.legajo || '';
  $('eNacimiento').value = e.fecha_nacimiento || '';
  $('eSexo').value = e.sexo || '';
  $('eEstadoCivil').value = e.estado_civil || '';
  $('eDomicilio').value = e.domicilio || '';
  $('eHijos').value = e.cantidad_hijos || 0;
  $('eConyuge').value = e.conyuge_a_cargo ? 'true' : 'false';
  $('eObraSocial').value = e.obra_social || '';
  $('eModalidad').value = e.modalidad_contrato || 'Tiempo indeterminado';
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
  ['eNombre','eApellido','eCuil','eFecha','eNacimiento','eDomicilio','eLegajo','eObraSocial','eLugar','eCbu','eRemun','eFormaPago','eLocalidad','eFilial'].forEach(i=>$(i).value='');
  $('eHijos').value='0';
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
  try{
    const cuerpo = {
      nombre:$('eNombre').value.trim(), apellido:$('eApellido').value.trim(),
      cuil:$('eCuil').value.replace(/\D/g,''), fecha_ingreso:$('eFecha').value,
      cct_numero:$('eConvenio').value, categoria:$('eCategoria').value,
      legajo:$('eLegajo').value.trim(),
      proporcion_jornada:$('eJornada').value,
      fecha_nacimiento:$('eNacimiento').value || null,
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

async function liquidar(){
  ocultar('liqError'); $('resultados').innerHTML='<p style="margin-top:12px">Calculando…</p>';
  try{
    const d = await api('/liquidaciones','POST',{periodo:$('periodo').value, tipo:'mensual', novedades:[]});
    ultimaLiq = d;
    if(!d.detalles.length){ $('resultados').innerHTML='<p style="margin-top:12px">No hay empleados para liquidar.</p>'; return; }
    let html='';
    d.detalles.forEach(det=>{
      const emp = empleadosCache[det.empleado_id] || {apellido:'Empleado',nombre:'',cct_numero:''};
      let filas='';
      det.conceptos.forEach(c=>{
        const tipo = c.tipo==='deduccion'?'Descuento': c.tipo==='contribucion'?'Aporte del empleador':'Haber';
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
        <div style="margin-top:10px"><button class="chico secundario" onclick="verRecibo('${det.empleado_id}')">📄 Ver recibo oficial (Anexo III) — descargar PDF</button></div>
        </div>`;
    });
    $('resultados').innerHTML = html + resumenF931(d);
    await cargarCarpetas();
  }catch(e){ $('resultados').innerHTML=''; mostrarError('liqError', e.message); }
}

function antigTexto(fIngreso, periodo){
  if(!fIngreso) return '—';
  const ing = new Date(fIngreso+'T00:00:00');
  const p = periodo.split('-').map(Number);
  const ref = new Date(p[0], p[1]-1, 28);
  let a = ref.getFullYear()-ing.getFullYear();
  if(ref.getMonth()<ing.getMonth() || (ref.getMonth()===ing.getMonth() && ref.getDate()<ing.getDate())) a--;
  return (a<0?0:a)+' años';
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
   +'.btn{background:#0f766e;color:#fff;border:0;padding:10px 18px;border-radius:6px;font-size:.9rem;cursor:pointer;margin:12px auto;display:block}'
   +'@media print{body{background:#fff}.hoja{border:0;margin:0;max-width:100%}.btn,.aviso{display:none}}</style></head><body>'
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

if(token()) entrar();
</script>
</body>
</html>
"""
