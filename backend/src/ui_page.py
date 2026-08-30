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
  .contenedor{max-width:1280px;margin:24px auto;padding:0 16px}
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
  .sesion-activa>header{display:none}
  .app-layout{display:grid;grid-template-columns:240px minmax(0,1fr);gap:22px;align-items:start}
  .boton-menu{display:none;margin:0 0 12px;width:100%}
  .seccion-app{display:none}
  .seccion-app.visible{display:block}
  @media(max-width:900px){
    .boton-menu{display:block}
    .app-layout{grid-template-columns:1fr}
    .lateral{display:none}
    .app-layout.menu-abierto .lateral{display:block}
  }
  .lateral{position:sticky;top:16px;background:#fff;border:1px solid var(--borde);border-radius:14px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,.06)}
  .marca-lateral{display:flex;align-items:center;gap:10px;color:var(--verde);margin-bottom:18px}
  .marca-lateral svg{width:40px;height:40px;flex:none;background:var(--verde);border-radius:10px;padding:6px}
  .marca-lateral strong{font-size:1.08rem}
  .selector-empresa{background:#f0fdfa;border:1px solid #99f6e4;border-radius:10px;padding:10px;margin-bottom:14px}
  .selector-empresa label{margin:0 0 5px;font-weight:600;color:var(--verde)}
  .selector-empresa select{background:#fff;font-weight:600}
  .navegacion{display:grid;gap:5px}
  .navegacion button{display:flex;align-items:center;gap:9px;width:100%;margin:0;padding:9px 11px;text-align:left;background:transparent;color:#374151;border:1px solid transparent}
  .navegacion button:hover,.navegacion button.activo{background:#e0f2f1;color:var(--verde);border-color:#99f6e4}
  .navegacion .icono{width:20px;text-align:center}
  .lateral-pie{border-top:1px solid var(--borde);margin-top:14px;padding-top:12px}
  .lateral-pie button{width:100%;margin:0}
  .contenido-app{min-width:0}
  .contexto-empresa{display:flex;justify-content:space-between;gap:12px;align-items:center;background:#ecfdf5;border:1px solid #a7f3d0;border-radius:10px;padding:10px 14px;margin-bottom:14px;color:#065f46}
  .pasos{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px}
  .paso{flex:1 1 120px;min-width:110px;background:#fff;border:1px solid var(--borde);border-radius:9px;padding:9px;font-size:.82rem;color:#6b7280}
  .paso b{display:inline-grid;place-items:center;width:22px;height:22px;border-radius:50%;background:#e5e7eb;margin-right:5px}
  .paso.activo{border-color:#5eead4;color:var(--verde);font-weight:600}.paso.activo b{background:var(--verde);color:#fff}
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
    .app-layout{grid-template-columns:1fr;gap:12px}
    .lateral{position:static;padding:12px}
    .navegacion{grid-template-columns:1fr 1fr}
    .navegacion button{font-size:.82rem}
    .paso{flex-basis:calc(50% - 6px);font-size:.76rem;padding:7px}
    .contexto-empresa{align-items:flex-start;flex-direction:column}
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
    <div class="app-layout">
      <aside class="lateral" aria-label="Menú principal">
        <div class="marca-lateral">
          <svg viewBox="0 0 64 64" role="img" aria-label="Logo Sueldo Claro">
            <path d="M12 7h27l10 10v25H12z" fill="none" stroke="#fff" stroke-width="5" stroke-linejoin="round"/>
            <path d="M39 7v11h10M20 24h19M20 33h12" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="m31 45 8 8 15-18" fill="none" stroke="#fbbf24" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <div><strong>Sueldo Claro</strong><small style="display:block;color:#6b7280">Gestión laboral</small></div>
        </div>
        <div class="selector-empresa">
          <label for="empresaActiva">Empresa activa</label>
          <select id="empresaActiva" onchange="cambiarEmpresa(this.value)"></select>
          <button class="chico secundario" style="width:100%;margin-top:8px" onclick="mostrarNuevaEmpresa()">+ Nueva empresa</button>
        </div>
        <nav class="navegacion">
          <button class="activo" onclick="irA('seccionInicio',this)"><span class="icono">🏠</span>Inicio</button>
          <button onclick="irA('seccionEmpresas',this)"><span class="icono">🏢</span>Empresas</button>
          <button onclick="irA('seccionConvenios',this);cargarGestorNormativo()"><span class="icono">📚</span>Convenios y escalas</button>
          <button onclick="irA('seccionEstablecimientos',this)"><span class="icono">📍</span>Establecimientos</button>
          <button onclick="irA('seccionEmpleados',this)"><span class="icono">👥</span>Empleados</button>
          <button onclick="irA('seccionNovedades',this)"><span class="icono">🗓</span>Novedades</button>
          <button onclick="irA('seccionLiquidar',this)"><span class="icono">🧮</span>Liquidar</button>
          <button onclick="irA('seccionHistorial',this)"><span class="icono">📁</span>Recibos e historial</button>
        </nav>
        <div class="lateral-pie"><button class="chico secundario" onclick="salir()">Cerrar sesión</button></div>
      </aside>
      <main class="contenido-app">
        <button id="botonMenu" class="boton-menu secundario" onclick="alternarMenu()" aria-expanded="false">☰ Menú</button>
        <div class="contexto-empresa"><span><b id="empresaNombreActiva">Empresa</b><br><small>Los empleados y liquidaciones visibles pertenecen únicamente a esta empresa.</small></span><span id="empresaRol" class="etiqueta"></span></div>
        <div class="pasos" aria-label="Camino de trabajo"><div class="paso activo"><b>1</b>Cliente / grupo</div><div class="paso activo"><b>2</b>Sociedad / CUIT</div><div class="paso"><b>3</b>Establecimiento</div><div class="paso"><b>4</b>Empleado</div><div class="paso"><b>5</b>Novedades</div><div class="paso"><b>6</b>Liquidación</div><div class="paso"><b>7</b>Recibo</div></div>
        <div id="nuevaEmpresa" class="tarjeta" style="display:none">
          <div class="cabecera-seccion"><h2>Nueva empresa o cliente</h2><button class="chico secundario" onclick="mostrarNuevaEmpresa(false)">Cerrar</button></div>
          <p style="font-size:.88rem;color:#6b7280">Se creará un espacio independiente. Sus empleados y liquidaciones nunca se mezclarán con otra empresa.</p>
          <div class="fila"><div><label>Cliente o grupo (opcional)</label><input id="nuevaEmpresaGrupo" placeholder="Ej.: Familia Pérez"></div><div><label>Razón social</label><input id="nuevaEmpresaRazon" placeholder="Empresa cliente S.A."></div><div><label>CUIT</label><input id="nuevaEmpresaCuit" inputmode="numeric" maxlength="13" placeholder="30123456789"></div></div>
          <button onclick="crearEmpresa()">Crear y comenzar a trabajar</button><div id="empresaError" class="error"></div>
        </div>
    <div class="tarjeta seccion-app" id="seccionInicio">
      <div class="cabecera-seccion"><div><h2>Inicio</h2><p style="font-size:.85rem;color:#6b7280;margin:4px 0 0">Resumen de la empresa activa y accesos rápidos.</p></div></div>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-top:14px">
        <div style="border:1px solid var(--borde);border-radius:12px;padding:14px;background:#f8fafc">
          <div style="font-size:.72rem;color:#6b7280;text-transform:uppercase;letter-spacing:.03em">Empresa activa</div>
          <div id="kpiEmpresa" style="font-size:1.05rem;font-weight:700;color:var(--verde);margin-top:4px;line-height:1.15">—</div>
          <div id="kpiEmpresaCuit" style="font-size:.78rem;color:#6b7280;margin-top:3px"></div>
        </div>
        <div style="border:1px solid var(--borde);border-radius:12px;padding:14px;background:#f8fafc">
          <div style="font-size:.72rem;color:#6b7280;text-transform:uppercase;letter-spacing:.03em">Empleados</div>
          <div id="kpiEmpleados" style="font-size:1.7rem;font-weight:800;color:var(--verde);margin-top:2px;line-height:1">0</div>
          <div style="font-size:.78rem;color:#6b7280;margin-top:3px">en esta empresa</div>
        </div>
        <div style="border:1px solid var(--borde);border-radius:12px;padding:14px;background:#f8fafc">
          <div style="font-size:.72rem;color:#6b7280;text-transform:uppercase;letter-spacing:.03em">Establecimientos</div>
          <div id="kpiEstablecimientos" style="font-size:1.7rem;font-weight:800;color:var(--verde);margin-top:2px;line-height:1">0</div>
          <div style="font-size:.78rem;color:#6b7280;margin-top:3px">activos</div>
        </div>
        <div style="border:1px solid var(--borde);border-radius:12px;padding:14px;background:#f8fafc">
          <div style="font-size:.72rem;color:#6b7280;text-transform:uppercase;letter-spacing:.03em">Liquidaciones pendientes</div>
          <div id="kpiPendientes" style="font-size:1.7rem;font-weight:800;color:var(--verde);margin-top:2px;line-height:1">—</div>
          <div id="kpiEstadoLiq" style="font-size:.78rem;color:#6b7280;margin-top:3px"></div>
        </div>
      </div>
      <h3 style="margin:18px 0 8px;font-size:.95rem">Accesos rápidos</h3>
      <div style="display:flex;flex-wrap:wrap;gap:8px">
        <button class="chico" onclick="irA('seccionEmpleados')">👥 Empleados</button>
        <button class="chico secundario" onclick="irA('seccionNovedades')">🗓 Novedades</button>
        <button class="chico secundario" onclick="irA('seccionLiquidar')">🧮 Liquidar</button>
        <button class="chico secundario" onclick="irA('seccionEstablecimientos')">📍 Establecimientos</button>
        <button class="chico secundario" onclick="irA('seccionHistorial')">📁 Recibos e historial</button>
      </div>
    </div>
    <div class="tarjeta seccion-app" id="seccionConvenios">
      <div class="cabecera-seccion"><div><h2>Convenios y escalas</h2><p style="font-size:.85rem;color:#6b7280;margin:4px 0 0">La estructura permanente se conserva; las paritarias se cargan por período sin modificar el historial.</p></div><div style="text-align:right"><button id="btnActualizarGestor" class="chico secundario" onclick="cargarGestorNormativo()">Actualizar estado</button><small id="gestorActualizado" style="display:block;color:#6b7280;margin-top:4px"></small></div></div>
      <div class="fila" style="margin-top:10px"><div><label>Período a revisar</label><input id="periodoGestor" type="month" onchange="cargarGestorNormativo()"></div><div style="display:flex;align-items:end"><p style="font-size:.82rem;color:#6b7280;padding-bottom:9px">🧱 Estructura estable · 📅 Valores del período · 🔒 El historial no se reemplaza</p></div></div>
      <div id="gestorNormativoError" class="error"></div>
      <div id="listaGestorNormativo" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;margin-top:14px"></div>
    </div>
    <div class="tarjeta seccion-app" id="seccionEmpresas">
      <div class="cabecera-seccion"><div><h2>Empresas y clientes</h2><p style="font-size:.85rem;color:#6b7280;margin:4px 0 0">Cada sociedad (CUIT) es un espacio independiente. Elegí la activa o creá una nueva.</p></div><button class="chico secundario" onclick="mostrarNuevaEmpresa()">+ Nueva empresa</button></div>
      <table id="tablaEmpresas" class="tabla-movil" style="display:none;margin-top:12px"><thead><tr><th>Cliente / grupo</th><th>Razón social</th><th>Rol</th><th>Estado</th><th></th></tr></thead><tbody></tbody></table>
      <p id="sinEmpresas" style="margin-top:10px;color:#6b7280;font-size:.9rem">Cargando empresas…</p>
      <div id="perfilLaboralEmpresa" style="border-top:1px solid var(--borde);margin-top:18px;padding-top:16px">
        <h3>Configuración de la empresa para liquidar</h3>
        <p style="font-size:.86rem;color:#6b7280">Cargá datos conocidos de la empresa; Sueldo Claro determina el porcentaje. El convenio continúa eligiéndose por empleado.</p>
        <div class="fila">
          <div><label>Uso de los datos</label><select id="empresaModoLiquidacion"><option value="PRUEBA">Prueba / simulación</option><option value="PRODUCCION">Producción real</option></select></div>
          <div><label>Actividad principal</label><select id="empresaActividadSector"><option value="PENDIENTE">Todavía no informada</option><option value="COMERCIO">Comercio</option><option value="SERVICIOS">Servicios</option><option value="INDUSTRIA">Industria</option><option value="CONSTRUCCION">Construcción</option><option value="AGRO">Agropecuaria</option><option value="MINERIA">Minería</option><option value="OTRO">Otra actividad</option></select></div>
          <div><label>Situación MiPyME</label><select id="empresaCondicionMipyme" onchange="mostrarVigenciaMipyme()"><option value="PENDIENTE">Todavía no comprobada</option><option value="CERTIFICADO_VIGENTE">Tiene Certificado MiPyME vigente</option><option value="SUPERA_LIMITES">Supera los límites MiPyME</option></select></div>
          <div id="campoVigenciaMipyme" style="display:none"><label>Certificado vigente hasta</label><input type="date" id="empresaMipymeHasta"></div>
          <div><label>Respaldo</label><input id="empresaRespaldoPatronal" placeholder="Constancia, enlace o referencia del documento"></div>
        </div>
        <p style="font-size:.8rem;color:#6b7280;margin-top:8px"><a href="https://pyme.produccion.gob.ar/condicionpyme/" target="_blank" rel="noopener">Consultar condición MiPyME por CUIT</a></p>
        <button class="chico" onclick="guardarPerfilLaboral()">Guardar configuración</button>
        <span id="perfilLaboralEstado" style="font-size:.82rem;color:#6b7280;margin-left:8px"></span>
        <div id="perfilLaboralError" class="error"></div>
      </div>
    </div>
    <div class="tarjeta seccion-app" id="seccionEstablecimientos">
      <div class="cabecera-seccion"><div><h2>Establecimientos y domicilios de trabajo</h2><p style="font-size:.85rem;color:#6b7280;margin:4px 0 0">Cada sociedad conserva sus propios lugares. Al cambiar a un empleado queda registrado desde qué fecha trabaja allí.</p></div><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><label style="display:flex;align-items:center;gap:6px;font-size:.82rem;color:#6b7280;margin:0"><input type="checkbox" id="verInactivosEst" onchange="cargarEstablecimientos()" style="width:auto;margin:0"> Ver inactivos</label><button class="chico secundario" onclick="toggleEstablecimiento()">+ Agregar domicilio</button></div></div>
      <div id="formEstablecimiento" style="display:none;border:1px dashed var(--borde);border-radius:10px;padding:14px;margin-top:12px"><div class="fila"><div><label>Nombre del lugar</label><input id="estNombre" placeholder="Casa central / Sucursal 1"></div><div><label>Domicilio</label><input id="estDomicilio" placeholder="Calle y número"></div><div><label>Localidad</label><input id="estLocalidad"></div><div><label>Provincia</label><input id="estProvincia"></div><div><label>Actividad del lugar</label><input id="estActividad" placeholder="Comercio, farmacia, depósito..."></div></div><h3 style="margin-top:14px">Cobertura ART</h3><p style="font-size:.82rem;color:#6b7280">Copiá estos datos del contrato o constancia de afiliación. No se completan automáticamente.</p><div class="fila"><div><label>ART contratada</label><input id="estArtNombre" placeholder="Nombre de la aseguradora"></div><div><label>Alícuota del contrato (%)</label><input id="estArtAlicuota" type="number" min="0" max="100" step="0.0001" placeholder="Ej.: 3,2500"></div><div><label>Suma fija por trabajador ($)</label><input id="estArtSumaFija" type="number" min="0" step="0.01"></div><div><label>Vigente desde</label><input id="estArtDesde" type="date"></div><div><label>Vigente hasta</label><input id="estArtHasta" type="date"></div><div><label>Comprobante / póliza</label><input id="estArtComprobante" placeholder="Número o referencia del contrato"></div></div><input type="hidden" id="estEditId"><button class="chico" id="btnGuardarEst" onclick="guardarEstablecimiento()">Guardar establecimiento</button><button class="chico secundario" id="btnCancelarEst" style="display:none;margin-left:6px" onclick="cancelarEdicionEst()">Cancelar</button><div id="estError" class="error"></div><div id="estOk" class="ok"></div></div>
      <table id="tablaEstablecimientos" class="tabla-movil" style="display:none"><thead><tr><th>Nombre</th><th>Domicilio</th><th>Localidad</th><th>Provincia</th><th>Actividad</th><th>ART</th><th>Estado</th><th></th></tr></thead><tbody></tbody></table><p id="sinEstablecimientos" style="margin-top:10px;color:#6b7280;font-size:.9rem">Todavía no cargaste domicilios de trabajo.</p>
    </div>
    <div class="tarjeta seccion-app" id="seccionEmpleados">
      <div class="cabecera-seccion">
        <h2>Empleados</h2>
        <div style="display:flex;gap:6px;flex-wrap:wrap">
          <button class="chico secundario" onclick="toggleAlta()">+ Agregar manual</button>
          <label class="chico secundario" style="cursor:pointer;display:inline-flex;align-items:center;margin:0">+ Importar Excel (.xlsx)<input type="file" id="inputExcel" accept=".xlsx" style="display:none" onchange="subirExcelPreview(this)"></label>
          <button class="chico secundario" onclick="descargarPlantillaExcel()" title="Descargar plantilla para importar empleados">📥 Plantilla de empleados</button>
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
          <div style="grid-column:1/-1"><label>Tarea principal efectivamente realizada</label>
            <input id="eTareaPrincipal" placeholder="Ej.: atención de mostrador y validación de recetas">
            <small style="color:#6b7280">Se usa para orientar el convenio y la categoría; no alcanza por sí sola.</small></div>
          <div style="grid-column:1/-1">
            <button type="button" class="chico secundario" onclick="analizarEncuadramiento()">Analizar convenio aplicable</button>
            <div id="resultadoEncuadramiento" style="display:none;margin-top:8px;padding:10px;border:1px solid #bfdbfe;background:#eff6ff;border-radius:8px"></div>
          </div>
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
          <div><label>Establecimiento / lugar de trabajo</label><select id="eEstablecimiento" onchange="datosEstablecimientoParaEncuadramiento()"><option value="">Sin establecimiento asignado</option></select></div>
          <div><label>Trabaja allí desde</label><input id="eLugarDesde" type="text" inputmode="numeric" placeholder="DD/MM/AAAA" maxlength="10" oninput="formatearFecha(this)"><small style="color:#6b7280">Solo completalo al asignar o cambiar el lugar.</small></div>
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
      <table id="tablaEmpleados" class="tabla-movil"><thead><tr><th>Apellido y nombre</th><th>CUIL</th><th>Convenio</th><th>Categoría</th><th>Lugar de trabajo</th><th>Ingreso</th><th></th></tr></thead><tbody></tbody></table>
      <p id="sinEmpleados" style="margin-top:10px;color:#6b7280;font-size:.9rem">Todavía no cargaste empleados.</p>
    </div>

    <div class="tarjeta seccion-app" id="seccionNovedades">
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
          <div><label>Tratamiento del premio</label><select id="novTipoPremio"><option value="pendiente">Todavía no definido (no calcular)</option><option value="remunerativo">Remunerativo (integra aportes)</option><option value="no_remunerativo">No remunerativo</option></select></div>
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
          <div id="novUocra" style="display:none;grid-column:1/-1;border:1px solid var(--borde);border-radius:8px;padding:12px">
            <b>Control quincenal — UOCRA CCT 76/75</b>
            <p style="font-size:.82rem;color:#6b7280;margin:5px 0 10px">Informá horas normales y asistencia por separado. No sumes horas extra acá.</p>
            <div class="fila">
              <div><label>Horas normales · 1.ª quincena</label><input id="novHorasQ1" type="number" min="0" max="200" step="0.01" placeholder="Sin informar"></div>
              <div><label>Asistencia perfecta · 1.ª quincena</label><select id="novAsistenciaQ1"><option value="">Sin informar</option><option value="true">Sí</option><option value="false">No</option></select></div>
              <div><label>Feriados no trabajados habilitados · 1.ª</label><input id="novFeriadosHabQ1" type="number" min="0" step="1" value="0"></div>
              <div><label>Horas normales · 2.ª quincena</label><input id="novHorasQ2" type="number" min="0" max="200" step="0.01" placeholder="Sin informar"></div>
              <div><label>Asistencia perfecta · 2.ª quincena</label><select id="novAsistenciaQ2"><option value="">Sin informar</option><option value="true">Sí</option><option value="false">No</option></select></div>
              <div><label>Feriados no trabajados habilitados · 2.ª</label><input id="novFeriadosHabQ2" type="number" min="0" step="1" value="0"></div>
            </div>
            <small style="color:#92400e">“Habilitado” significa que cumple el requisito legal previo; la app no lo presume.</small>
            <div style="margin-top:12px;border-top:1px solid var(--borde);padding-top:10px">
              <div style="display:flex;justify-content:space-between;align-items:center;gap:8px"><b>Detalle de horas extra</b><button type="button" class="chico secundario" onclick="agregarHoraExtraUocra()">+ Agregar tramo</button></div>
              <div id="novHorasExtraUocraLista" style="display:grid;gap:8px;margin-top:8px"></div>
              <div style="margin-top:8px"><label>Horas extra acumuladas en el año, antes de este mes</label><input id="novHorasExtraUocraAnio" type="number" min="0" max="200" step="0.01" value="0"></div>
              <small style="color:#6b7280">La app separa 50%/100% por fecha y hora, divide automáticamente el sábado a las 13 y controla los topes 3/30/200.</small>
            </div>
            <div style="margin-top:12px;border-top:1px solid var(--borde);padding-top:10px">
              <b>Adicionales por tarea verificados</b>
              <div class="fila" style="margin-top:8px">
                <div><label>Horas de colada manual directa de hormigón</label><input id="novHorasHormigonUocra" type="number" min="0" step="0.25" value="0"><small>Art. 56: 15% sobre básico puro. Solo sin medios mecánicos/automáticos.</small></div>
                <div><label>Horas efectivas de trabajo en altura</label><input id="novHorasAlturaUocra" type="number" min="0" step="0.25" value="0"></div>
                <div><label>Altura medida según art. 57 (metros)</label><input id="novAlturaMetrosUocra" type="number" min="0" step="0.01" placeholder="Obligatoria si hay horas"><small>15% / 20% / 25%. Exactamente 26 m requiere criterio profesional.</small></div>
              </div>
              <small style="color:#92400e">Túneles y martillo neumático: visibles como pendientes, sin tarifa independiente verificada; no se calculan.</small>
            </div>
            <div style="margin-top:12px;border-top:1px solid var(--borde);padding-top:10px">
              <div style="display:flex;justify-content:space-between;align-items:center;gap:8px"><b>Detalle de feriados</b><button type="button" class="chico secundario" onclick="agregarFeriadoUocra()">+ Agregar feriado</button></div>
              <div id="novFeriadosUocraLista" style="display:grid;gap:8px;margin-top:8px"></div>
              <small style="color:#6b7280">Cada fecha guarda si fue trabajada, el requisito del art. 168, las horas de la jornada anterior y sus accesorios.</small>
            </div>
            <div style="margin-top:12px;border-top:1px solid var(--borde);padding-top:10px">
              <b>Criterio profesional · mes del primer aniversario</b>
              <div class="fila" style="margin-top:8px">
                <div><label>Criterio Fondo de Cese</label><select id="novFclCriterio"><option value="">No corresponde / sin definir</option><option value="MES_COMPLETO_12">Mes completo al 12%</option><option value="MES_COMPLETO_8">Mes completo al 8%</option><option value="PRORRATEO_DIAS">Prorrateo por bases separadas</option></select></div>
                <div><label>Profesional que lo aprueba</label><input id="novFclAprobado" maxlength="200" placeholder="Nombre y matrícula"></div>
                <div style="grid-column:1/-1"><label>Fundamento</label><textarea id="novFclFundamento" rows="2" placeholder="Criterio profesional documentado"></textarea></div>
                <div style="grid-column:1/-1"><label>Base remunerativa UOCRA del plantel del mes anterior ($)</label><input id="novBaseUocraAnterior" type="number" min="0" step="0.01" placeholder="Obligatoria para calcular la contribución empresaria del 2%"><small style="color:#6b7280">Copiar de la liquidación cerrada del mes anterior. Queda guardada para auditoría.</small></div>
              </div>
            </div>
          </div>
          <div id="novCamioneros" style="display:none;grid-column:1/-1;border:1px solid var(--borde);border-radius:8px;padding:12px">
            <b>Variables de viaje y rama — Camioneros CCT 40/89</b>
            <p style="font-size:.82rem;color:#6b7280;margin:5px 0 10px">Cargá solo hechos del período. Los ceros no generan conceptos y la app controla mínimos de 350 km por día y 700 km por viaje cordillerano.</p>
            <div class="fila">
              <div><label>Rama de actividad</label><select id="camRama"><option value="general">General</option><option value="larga_distancia">Larga distancia</option><option value="transporte_automoviles">Transporte de automóviles</option><option value="logistica">Logística</option><option value="combustibles">Combustibles</option><option value="sustancias_peligrosas">Sustancias peligrosas</option><option value="pozos_petroliferos">Pozos petrolíferos</option><option value="materia_prima_lactea">Materia prima láctea</option><option value="auxilio">Auxilio mecánico</option><option value="residuos">Residuos</option><option value="taller">Taller</option><option value="caudales">Caudales</option><option value="diarios_revistas">Diarios y revistas</option><option value="clearing">Clearing</option><option value="expreso_mudanza">Expreso y mudanza</option><option value="aguas_gaseosas">Aguas gaseosas</option></select></div>
              <div><label>Zona salarial</label><select id="camZona"><option value="BASE">Base</option><option value="COEF_1_20">Coeficiente 1,20</option><option value="COEF_1_40">Coeficiente 1,40</option></select></div>
              <div><label>Grupo de taller</label><select id="camGrupoTaller"><option value="">No corresponde</option><option value="I">Grupo I</option><option value="II">Grupo II</option><option value="III">Grupo III</option></select><small style="color:#6b7280">Completalo para personal de taller.</small></div>
              <label><input type="checkbox" id="camCuencaPetrolifera"> Trabajo en cuenca petrolífera</label>
              <label><input type="checkbox" id="camLaPampaMendoza"> Servicio petrolero en La Pampa o Mendoza</label>
              <label><input id="camFrio" type="checkbox"> Trabajo habitual en cámara de frío</label>
            </div>
            <div class="fila" style="margin-top:10px">
              <div><label>Días con comida</label><input id="camDiasComida" type="number" min="0" step="1" value="0"></div>
              <div><label>Días viático especial</label><input id="camDiasViatico" type="number" min="0" step="1" value="0"></div>
              <div><label>Pernoctadas</label><input id="camPernoctadas" type="number" min="0" step="1" value="0"></div>
              <div><label>Kilómetros extra</label><input id="camKmExtra" type="number" min="0" step="0.01" value="0"></div>
              <div><label>Kilómetros viático</label><input id="camKmViatico" type="number" min="0" step="0.01" value="0"></div>
              <div><label>Días en viaje</label><input id="camDiasViaje" type="number" min="0" step="1" value="0"></div>
              <div><label>Viajes cordilleranos</label><input id="camCordillera" type="number" min="0" step="1" value="0"></div>
              <div><label>Permanencias</label><input id="camPermanencias" type="number" min="0" step="1" value="0"></div>
              <div><label>Simples presencias</label><input id="camPresencias" type="number" min="0" step="1" value="0"></div>
              <div><label>Permanencias sur</label><input id="camPermanenciasSur" type="number" min="0" step="1" value="0"></div>
              <div><label>Simples presencias sur</label><input id="camPresenciasSur" type="number" min="0" step="1" value="0"></div>
              <div><label>Cruces de frontera</label><input id="camFrontera" type="number" min="0" step="1" value="0"></div>
              <div><label>Ingresos/egresos T. del Fuego</label><input id="camTdf" type="number" min="0" step="1" value="0"></div>
              <div><label>Días plus vacacional</label><input id="camVacaciones" type="number" min="0" step="1" value="0"></div>
              <div><label>Traslados de unidad para descarga</label><input id="camTrasladosDescarga" type="number" min="0" step="1" value="0"><small style="color:#6b7280">Larga distancia · un jornal por traslado (ítem 4.2.6).</small></div>
              <div><label>Viajes transportando automóviles</label><input id="camViajesAutomoviles" type="number" min="0" step="1" value="0"><small style="color:#6b7280">Un jornal por viaje (ítem 4.2.9).</small></div>
              <div><label>Unidades bitrenes</label><input id="camBitrenes" type="number" min="0" step="1" value="0"></div>
            </div>
            <small style="color:#92400e">La carga queda auditada. El recibo se habilita únicamente cuando las bases e incidencias de cada rama estén verificadas; la app no presume ni prorratea reglas faltantes.</small>
          </div>
          <div id="novUom" style="display:none;grid-column:1/-1;border:1px solid var(--borde);border-radius:8px;padding:12px">
            <b>Novedades metalúrgicas — UOM CCT 260/75</b>
            <p style="font-size:.82rem;color:#6b7280;margin:5px 0 10px">La categoría ya identifica rama y modalidad. Informá horas solamente si es jornalizada; para mensualizados dejalas vacías.</p>
            <div class="fila">
              <div><label>Horas normales del período</label><input id="uomHorasNormales" type="number" min="0" max="300" step="0.01" placeholder="Solo personal jornalizado"></div>
              <div><label>Ingresos computables para IMGR ($)</label><input id="uomIngresosImgr" type="number" min="0" step="0.01" placeholder="Sin incluir horas extra"></div>
              <div><label>Días trabajados entre 01/04 y 31/07</label><input id="uomDiasAbrJul" type="number" min="0" max="122" step="1" placeholder="Incluye licencias pagas"></div>
              <label><input id="uomContratoJulio" type="checkbox"> Contrato vigente al 31/07/2026</label>
              <div><label>Pagos a cuenta absorbibles ($)</label><input id="uomPagosCuenta" type="number" min="0" step="0.01" value="0"></div>
            </div>
            <small style="color:#92400e">El IMGR es una garantía, no un básico. Los adicionales se habilitan únicamente con su hecho generador y nunca se marcan solos.</small>
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

    <div class="tarjeta seccion-app" id="seccionLiquidar">
      <h2>Liquidar sueldos</h2>
      <div class="fila">
        <div><label>Mes a liquidar</label><input id="periodo" type="month" onchange="cargarConvenios();cargarCarpetas();mostrarEstadoNormativo()"></div>
        <div style="display:flex;align-items:end"><button onclick="liquidar()" style="width:100%">Liquidar todos los empleados</button></div>
      </div>
      <div id="estadoNormativo" style="margin-top:12px;font-size:.9rem"></div>
      <div class="error" id="liqError"></div>
      <div id="resultados"></div>
    </div>

    <div class="tarjeta seccion-app" id="seccionHistorial">
      <div class="cabecera-seccion">
        <h2>Carpeta mensual</h2>
        <button class="chico secundario" onclick="cargarCarpetas()">Actualizar historial</button>
      </div>
      <p style="font-size:.85rem;color:#6b7280">Cada liquidación conserva una versión de sólo lectura. Las correcciones no borran las anteriores.</p>
      <div class="error" id="carpetasError"></div>
      <table id="tablaCarpetas" class="tabla-movil" style="display:none"><thead><tr><th>Mes</th><th>Versión</th><th>Estado</th><th>Creada</th><th>Huella</th><th></th></tr></thead><tbody></tbody></table>
      <p id="sinCarpetas" style="margin-top:10px;color:#6b7280;font-size:.9rem">Todavía no hay carpetas generadas para este mes.</p>
      <div id="panelVersion" style="display:none;margin-top:18px;border-top:1px solid #d1d5db;padding-top:16px">
        <div class="cabecera-seccion"><h3 id="panelVersionTitulo">Versión</h3><button class="chico secundario" onclick="cerrarPanelVersion()">Cerrar</button></div>
        <p id="panelVersionMeta" style="font-size:.85rem;color:#4b5563"></p>
        <div class="aviso" id="panelVersionFaltantes" style="display:none"></div>
        <div style="margin:10px 0"><button class="chico" onclick="descargarRecibosDeVersion()">Descargar todos los recibos</button></div>
        <table id="tablaVersionDetalle" class="tabla-movil"><thead><tr><th>Empleado</th><th class="num">Bruto</th><th class="num">Descuentos</th><th class="num">Neto</th><th>Conceptos</th><th></th></tr></thead><tbody></tbody></table>
      </div>
      <div id="panelCierre" style="display:none;margin-top:18px;border-top:1px solid #d1d5db;padding-top:16px">
        <div class="cabecera-seccion"><h3>Cierre profesional del período</h3><button class="chico secundario" onclick="cerrarPanelCierre()">Cerrar</button></div>
        <p id="cierreResumen" style="font-size:.9rem;color:#4b5563"></p>
        <div class="error" id="cierreError"></div><div class="ok" id="cierreOk"></div>
        <div id="cierreFaltantes" style="margin:10px 0"></div>
        <table id="tablaObligaciones" class="tabla-movil"><thead><tr><th>Salida / boleta</th><th>Destino</th><th>Importe</th><th>Estado</th><th>Comprobante</th><th>Acción</th></tr></thead><tbody></tbody></table>
        <div style="margin-top:14px"><label>Observaciones del contador</label><textarea id="cierreObservaciones" rows="2" placeholder="Control realizado, salvedades o referencia del papel de trabajo"></textarea></div>
        <button class="chico" style="margin-top:10px" onclick="aprobarCierre()">Aprobar y firmar revisión profesional</button>
        <div id="cierreRevisiones" style="margin-top:12px;font-size:.85rem"></div>
      </div>
    </div>
      </main>
    </div>
  </div>
</div>

<script>
const $ = id => document.getElementById(id);
function esc(t){ return String(t==null?'':t).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
let empleadosCache = {};
let establecimientosCache = {};
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
        if(d.tenant_id) localStorage.setItem('sc_tenant',d.tenant_id);
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
  const r = await fetch(ruta,{method:metodo,headers:h,body:body?JSON.stringify(body):null,cache:metodo==='GET'?'no-store':'default'});
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
    if(msg && typeof msg==='object') msg=(msg.mensaje||'No se pudo completar')+(msg.faltantes?' · '+msg.faltantes.join(' · '):'');
    throw new Error(msg || 'Error ' + r.status);
  }
  return data;
}

function guardarCredenciales(d){
  localStorage.setItem('sc_access', d.access_token);
  localStorage.setItem('sc_refresh', d.refresh_token);
  if(d.tenant_id) localStorage.setItem('sc_tenant',d.tenant_id);
}
function guardarSesion(d){
  guardarCredenciales(d);
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
function salir(){
  localStorage.clear(); document.body.classList.remove('sesion-activa');
  $('app').style.display='none'; $('auth').style.display='block'; $('quien').textContent='';
}

// Navegación real: una sección visible por vez, con hash propio. No se
// desmonta nada, así que los formularios y los datos ya cargados sobreviven
// al cambio de sección.
const SECCIONES = [
  ['inicio','seccionInicio'],
  ['empresas','seccionEmpresas'],
  ['convenios','seccionConvenios'],
  ['establecimientos','seccionEstablecimientos'],
  ['empleados','seccionEmpleados'],
  ['novedades','seccionNovedades'],
  ['liquidar','seccionLiquidar'],
  ['historial','seccionHistorial'],
];
const SECCION_POR_HASH = Object.fromEntries(SECCIONES);
const HASH_POR_SECCION = Object.fromEntries(SECCIONES.map(([h,id])=>[id,h]));
// Al entrar por primera vez a una sección se carga lo suyo. No se recalcula
// nada: sólo se piden datos que ya existen en el servidor.
const CARGA_SECCION = {
  seccionConvenios: ()=>cargarGestorNormativo(),
  seccionHistorial: ()=>cargarCarpetas(),
};
let seccionActual = 'seccionInicio';

function irA(id,boton,actualizarHash=true){
  if(!HASH_POR_SECCION[id]) id='seccionInicio';
  seccionActual=id;
  SECCIONES.forEach(([,secId])=>{
    const el=$(secId);
    if(el) el.classList.toggle('visible', secId===id);
  });
  document.querySelectorAll('.navegacion button').forEach(b=>b.classList.remove('activo'));
  if(!boton){ boton=[...document.querySelectorAll('.navegacion button')].find(b=>(b.getAttribute('onclick')||'').includes("irA('"+id+"'")); }
  if(boton) boton.classList.add('activo');
  if(actualizarHash){
    const hash='#'+HASH_POR_SECCION[id];
    if(location.hash!==hash) history.replaceState(null,'',hash);
  }
  cerrarMenu();
  window.scrollTo({top:0,behavior:'auto'});
  const carga=CARGA_SECCION[id];
  if(carga){ try{ carga(); }catch(e){} }
}

function seccionDelHash(){
  const clave=(location.hash||'').replace('#','').trim().toLowerCase();
  return SECCION_POR_HASH[clave] || 'seccionInicio';
}

function aplicarHash(){
  // Si no hay hash, se deja el de Inicio: la URL siempre identifica la sección.
  irA(seccionDelHash(), null, !location.hash);
}

function alternarMenu(){
  const layout=document.querySelector('.app-layout');
  if(!layout) return;
  const abierto=layout.classList.toggle('menu-abierto');
  const boton=$('botonMenu');
  if(boton) boton.setAttribute('aria-expanded', abierto?'true':'false');
}

function cerrarMenu(){
  const layout=document.querySelector('.app-layout');
  if(layout) layout.classList.remove('menu-abierto');
  const boton=$('botonMenu');
  if(boton) boton.setAttribute('aria-expanded','false');
}

window.addEventListener('hashchange', ()=>{
  const destino=seccionDelHash();
  if(destino!==seccionActual) irA(destino, null, false);
});
function mostrarNuevaEmpresa(forzar=true){
  const panel=$('nuevaEmpresa');
  panel.style.display=forzar===false?'none':(panel.style.display==='none'?'block':'none');
  ocultar('empresaError');
  if(panel.style.display==='block') $('nuevaEmpresaRazon').focus();
}
async function cargarEmpresas(){
  const empresas=await api('/auth/empresas');
  const activa=localStorage.getItem('sc_tenant');
  const sel=$('empresaActiva'); sel.innerHTML='';
  empresas.forEach(e=>{
    const o=document.createElement('option');
    o.value=e.id; o.textContent=(e.grupo_cliente?e.grupo_cliente+' — ':'')+e.razon_social;
    if(e.activa||e.id===activa) o.selected=true;
    sel.appendChild(o);
  });
  const elegida=empresas.find(e=>e.id===sel.value)||empresas.find(e=>e.activa)||empresas[0];
  if(elegida){
    $('empresaNombreActiva').textContent=elegida.razon_social;
    $('empresaRol').textContent=elegida.rol==='admin'?'Administrador':elegida.rol;
  }
}
async function cambiarEmpresa(tenantId){
  if(!tenantId||tenantId===localStorage.getItem('sc_tenant')) return;
  try{
    const d=await api('/auth/seleccionar-empresa','POST',{tenant_id:tenantId});
    guardarCredenciales(d);
    cancelarEdicion(); cancelarNovedad(); ultimaLiq=null;
    $('resultados').innerHTML='';
    await recargarEmpresaActiva();
  }catch(e){
    window.alert('No se pudo cambiar de empresa: '+e.message);
    await cargarEmpresas();
  }
}
async function crearEmpresa(){
  ocultar('empresaError');
  const razon=$('nuevaEmpresaRazon').value.trim();
  const cuit=$('nuevaEmpresaCuit').value.replace(/\D/g,'');
  if(razon.length<2){mostrarError('empresaError','Escribí la razón social.');return;}
  if(cuit.length!==11){mostrarError('empresaError','El CUIT debe tener 11 dígitos.');return;}
  try{
    const d=await api('/auth/empresas','POST',{razon_social:razon,cuit:cuit,grupo_cliente:$('nuevaEmpresaGrupo').value.trim()});
    guardarCredenciales(d);
    $('nuevaEmpresaGrupo').value=''; $('nuevaEmpresaRazon').value=''; $('nuevaEmpresaCuit').value='';
    mostrarNuevaEmpresa(false);
    await recargarEmpresaActiva();
  }catch(e){mostrarError('empresaError',e.message);}
}

async function recargarEmpresaActiva(){
  await cargarEmpresas();
  empresaCache=await api('/empresa');
  await cargarConvenios();
  await cargarEstablecimientos();
  await cargarEmpleados();
  await cargarNovedades();
  await mostrarEstadoNormativo();
  await cargarCarpetas();
  await cargarEmpresasSeccion();
  await cargarInicio();
  await cargarGestorNormativo();
}

async function entrar(){
  document.body.classList.add('sesion-activa');
  $('auth').style.display='none'; $('app').style.display='block';
  $('quien').textContent='Sesión iniciada';
  const hoy = new Date();
  $('periodo').value = hoy.toISOString().slice(0,7);
  $('periodoGestor').value = $('periodo').value;
  $('novPeriodo').value = $('periodo').value;
  try{ await recargarEmpresaActiva(); }
  catch(e){ salir(); mostrarError('authError',e.message); return; }
  // Al entrar (o al recargar la página) se abre la sección que indica el hash.
  aplicarHash();
}
function toggleAlta(){ const a=$('alta'); a.style.display = a.style.display==='none'?'block':'none'; }
function toggleEstablecimiento(){ const a=$('formEstablecimiento'); a.style.display=a.style.display==='none'?'block':'none'; }
async function cargarEstablecimientos(){
  const verInactivos=$('verInactivosEst') && $('verInactivosEst').checked;
  const lista=await api('/establecimientos?incluir_inactivos=true'); establecimientosCache={};
  const tb=$('tablaEstablecimientos').querySelector('tbody'); tb.innerHTML='';
  const sel=$('eEstablecimiento'); const elegido=sel.value;
  sel.innerHTML='<option value="">Sin establecimiento asignado</option>';
  let visibles=0;
  lista.forEach(e=>{
    establecimientosCache[e.id]=e;
    if(verInactivos || e.activo){
      visibles++;
      const tr=document.createElement('tr'); if(!e.activo) tr.style.opacity='.55';
      const estado=e.activo?'<span class="etiqueta">Activo</span>':'<span style="display:inline-block;background:#fee2e2;color:#991b1b;border-radius:999px;padding:2px 10px;font-size:.75rem">Inactivo</span>';
      const acciones=`<div class="acciones-tabla"><button class="chico secundario" onclick="editarEstablecimiento('${e.id}')" title="Editar">✏️ Editar</button><button class="chico secundario" onclick="cambiarActivoEstablecimiento('${e.id}')" title="${e.activo?'Desactivar':'Activar'}">${e.activo?'🚫 Desactivar':'✅ Activar'}</button></div>`;
      const art=e.art_nombre?`${esc(e.art_nombre)} · ${fmt(Number(e.art_alicuota_pct||0))}%`:'Pendiente';
      tr.innerHTML=`<td data-label="Nombre">${esc(e.nombre)}</td><td data-label="Domicilio">${esc(e.domicilio)}</td><td data-label="Localidad">${esc(e.localidad||'')}</td><td data-label="Provincia">${esc(e.provincia||'')}</td><td data-label="Actividad">${esc(e.actividad||'')}</td><td data-label="ART">${art}</td><td data-label="Estado">${estado}</td><td class="acciones-celda">${acciones}</td>`;
      tb.appendChild(tr);
    }
    { const o=document.createElement('option'); o.value=e.id; o.textContent=`${e.nombre} — ${e.domicilio}${e.localidad?', '+e.localidad:''}`+(e.activo?'':' (Inactivo)'); if(!e.activo) o.disabled=true; sel.appendChild(o); }
  });
  if([...sel.options].some(o=>o.value===elegido)) sel.value=elegido;
  $('tablaEstablecimientos').style.display=visibles?'table':'none'; $('sinEstablecimientos').style.display=visibles?'none':'block';
}
function limpiarFormEst(){
  ['estNombre','estDomicilio','estLocalidad','estProvincia','estActividad','estArtNombre','estArtAlicuota','estArtSumaFija','estArtDesde','estArtHasta','estArtComprobante','estEditId'].forEach(id=>$(id).value='');
  $('btnGuardarEst').textContent='Guardar establecimiento';
  $('btnCancelarEst').style.display='none';
}
function cancelarEdicionEst(){ limpiarFormEst(); ocultar('estError'); ocultar('estOk'); $('formEstablecimiento').style.display='none'; }
function editarEstablecimiento(id){
  const e=establecimientosCache[id]; if(!e) return;
  ocultar('estError'); ocultar('estOk');
  $('estEditId').value=e.id; $('estNombre').value=e.nombre||''; $('estDomicilio').value=e.domicilio||'';
  $('estLocalidad').value=e.localidad||''; $('estProvincia').value=e.provincia||''; $('estActividad').value=e.actividad||'';
  $('estArtNombre').value=e.art_nombre||''; $('estArtAlicuota').value=e.art_alicuota_pct??''; $('estArtSumaFija').value=e.art_suma_fija??'';
  $('estArtDesde').value=e.art_vigencia_desde||''; $('estArtHasta').value=e.art_vigencia_hasta||''; $('estArtComprobante').value=e.art_comprobante_ref||'';
  $('btnGuardarEst').textContent='Guardar cambios'; $('btnCancelarEst').style.display='inline-block';
  $('formEstablecimiento').style.display='block'; $('estNombre').focus();
}
async function guardarEstablecimiento(){
  ocultar('estError'); ocultar('estOk');
  const id=$('estEditId').value;
  const datos={nombre:$('estNombre').value.trim(),domicilio:$('estDomicilio').value.trim(),localidad:$('estLocalidad').value.trim(),provincia:$('estProvincia').value.trim(),actividad:$('estActividad').value.trim(),art_nombre:$('estArtNombre').value.trim(),art_alicuota_pct:$('estArtAlicuota').value||null,art_suma_fija:$('estArtSumaFija').value||null,art_vigencia_desde:$('estArtDesde').value||null,art_vigencia_hasta:$('estArtHasta').value||null,art_comprobante_ref:$('estArtComprobante').value.trim(),activo:true};
  try{
    if(id){ const prev=establecimientosCache[id]; datos.activo=prev?prev.activo:true; await api('/establecimientos/'+id,'PUT',datos); }
    else{ await api('/establecimientos','POST',datos); }
    limpiarFormEst(); $('estOk').textContent=id?'Establecimiento actualizado ✔':'Establecimiento guardado ✔'; $('estOk').style.display='block';
    await cargarEstablecimientos(); await cargarInicio();
  }catch(e){mostrarError('estError',e.message);}
}
async function cambiarActivoEstablecimiento(id){
  const e=establecimientosCache[id]; if(!e) return;
  if(e.activo && !window.confirm(`¿Desactivar el establecimiento "${e.nombre}"? No se podrá asignar a nuevos empleados.`)) return;
  ocultar('estError'); ocultar('estOk');
  try{
    await api('/establecimientos/'+id,'PUT',{nombre:e.nombre,domicilio:e.domicilio,localidad:e.localidad||'',provincia:e.provincia||'',actividad:e.actividad||'',art_nombre:e.art_nombre||'',art_alicuota_pct:e.art_alicuota_pct??null,art_suma_fija:e.art_suma_fija??null,art_vigencia_desde:e.art_vigencia_desde||null,art_vigencia_hasta:e.art_vigencia_hasta||null,art_comprobante_ref:e.art_comprobante_ref||'',activo:!e.activo});
    await cargarEstablecimientos(); await cargarInicio();
  }catch(err){mostrarError('estError',err.message);}
}
async function cargarEmpresasSeccion(){
  try{
    const empresas=await api('/auth/empresas');
    const activa=localStorage.getItem('sc_tenant');
    const tb=$('tablaEmpresas').querySelector('tbody'); tb.innerHTML='';
    empresas.forEach(e=>{
      const esActiva=(e.activa||e.id===activa);
      const rol=e.rol==='admin'?'Administrador':(e.rol||'');
      const estado=esActiva?'<span class="etiqueta">Activa</span>':'';
      const accion=esActiva?'<span style="color:#6b7280;font-size:.8rem">En uso</span>':`<button class="chico secundario" onclick="cambiarEmpresa('${e.id}')">Usar esta</button>`;
      const tr=document.createElement('tr');
      tr.innerHTML=`<td data-label="Cliente / grupo">${esc(e.grupo_cliente||'—')}</td><td data-label="Razón social">${esc(e.razon_social||'')}</td><td data-label="Rol">${esc(rol)}</td><td data-label="Estado">${estado}</td><td class="acciones-celda">${accion}</td>`;
      tb.appendChild(tr);
    });
    $('tablaEmpresas').style.display=empresas.length?'table':'none';
    $('sinEmpresas').style.display=empresas.length?'none':'block';
    if(!empresas.length) $('sinEmpresas').textContent='Todavía no tenés empresas cargadas.';
    const actual=empresas.find(e=>e.activa||e.id===activa);
    if(actual){
      $('empresaModoLiquidacion').value=actual.modo_liquidacion||'PRUEBA';
      $('empresaActividadSector').value=actual.actividad_sector||'PENDIENTE';
      $('empresaCondicionMipyme').value=actual.condicion_mipyme||'PENDIENTE';
      $('empresaMipymeHasta').value=actual.certificado_mipyme_vigente_hasta||'';
      $('empresaRespaldoPatronal').value=actual.respaldo_regimen_patronal||'';
      mostrarVigenciaMipyme();
      const tasa=actual.regimen_contribucion_patronal==='PRIVADO_18'?'18%':(actual.regimen_contribucion_patronal==='SERVICIOS_COMERCIO_204'?'20,40%':'pendiente');
      $('perfilLaboralEstado').textContent=(actual.modo_liquidacion==='PRUEBA'?'Simulación':'Producción')+' · resultado '+tasa;
    }
  }catch(e){ /* silencioso */ }
}
function mostrarVigenciaMipyme(){
  $('campoVigenciaMipyme').style.display=$('empresaCondicionMipyme').value==='CERTIFICADO_VIGENTE'?'block':'none';
}
async function guardarPerfilLaboral(){
  ocultar('perfilLaboralError');
  const modo=$('empresaModoLiquidacion').value;
  const actividad=$('empresaActividadSector').value;
  const condicion=$('empresaCondicionMipyme').value;
  const vigenteHasta=$('empresaMipymeHasta').value||null;
  const respaldo=$('empresaRespaldoPatronal').value.trim();
  if(condicion==='CERTIFICADO_VIGENTE'&&!vigenteHasta){
    mostrarError('perfilLaboralError','Informá hasta cuándo está vigente el certificado.'); return;
  }
  if(modo==='PRODUCCION'&&!respaldo){
    mostrarError('perfilLaboralError','Producción requiere una constancia o referencia.'); return;
  }
  try{
    const actualizada=await api('/auth/empresas/activa/perfil-laboral','PUT',{
      modo_liquidacion:modo,
      actividad_sector:actividad,
      condicion_mipyme:condicion,
      certificado_mipyme_vigente_hasta:vigenteHasta,
      respaldo_regimen_patronal:respaldo
    });
    const tasa=actualizada.regimen_contribucion_patronal==='PRIVADO_18'?'18%':(actualizada.regimen_contribucion_patronal==='SERVICIOS_COMERCIO_204'?'20,40%':'pendiente');
    $('perfilLaboralEstado').textContent='Guardado · resultado '+tasa;
    await cargarEmpresasSeccion();
  }catch(e){mostrarError('perfilLaboralError',e.message);}
}

async function cargarGestorNormativo(){
  const periodo=$('periodoGestor').value||$('periodo').value||new Date().toISOString().slice(0,7);
  $('periodoGestor').value=periodo; ocultar('gestorNormativoError');
  const boton=$('btnActualizarGestor'); if(boton){boton.disabled=true;boton.textContent='Actualizando…';}
  try{
    const lista=await api('/convenios/gestor-normativo?periodo='+encodeURIComponent(periodo));
    const colores={completo:['#d1fae5','#065f46','Completo'],parcial:['#fef3c7','#92400e','Parcial'],pendiente:['#fee2e2','#991b1b','Pendiente']};
    $('listaGestorNormativo').innerHTML=lista.map(c=>{
      const est=colores[c.estado]||colores.pendiente;
      return `<div style="border:1px solid var(--borde);border-radius:12px;padding:14px;background:#fff">
        <div style="display:flex;justify-content:space-between;gap:8px;align-items:start"><div><b>${esc(c.nombre)}</b><div style="font-size:.78rem;color:#6b7280">CCT ${esc(c.numero)} · ${esc(c.sindicato||'Sin sindicato informado')}</div></div><span style="background:${est[0]};color:${est[1]};border-radius:999px;padding:3px 9px;font-size:.72rem;font-weight:700">${est[2]}</span></div>
        <div style="margin-top:12px;font-size:.83rem;display:grid;gap:6px"><div>🧱 Estructura: <b>${c.estructura.categorias_verificadas}/${c.estructura.categorias}</b> categorías · <b>${c.estructura.reglas}</b> reglas</div><div>📅 ${esc(periodo)}: <b>${c.periodo_actual.escalas_verificadas}/${c.periodo_actual.escalas_esperadas||c.estructura.categorias}</b> escalas · <b>${c.periodo_actual.parametros}</b> parámetros</div>${c.periodo_actual.motor_habilitado?'':c.periodo_actual.vista_previa_habilitada?`<div style="color:#075985">🧪 ${esc(c.periodo_actual.mensaje_motor||'Motor conectado en vista previa · validación real pendiente')}</div>`:'<div style="color:#92400e">🔒 Datos cargados; motor pendiente para esta modalidad</div>'}</div>
      </div>`;
    }).join('')||'<p style="color:#6b7280">Todavía no hay convenios activos.</p>';
    $('gestorActualizado').textContent='Actualizado '+new Date().toLocaleTimeString('es-AR',{hour:'2-digit',minute:'2-digit',second:'2-digit'});
  }catch(e){ mostrarError('gestorNormativoError',e.message); }
  finally{if(boton){boton.disabled=false;boton.textContent='Actualizar estado';}}
}
async function cargarInicio(){
  let emp=empresaCache; if(!emp||!emp.razon_social){ try{ emp=await api('/empresa'); }catch(e){ emp={razon_social:'',cuit:''}; } }
  $('kpiEmpresa').textContent=emp.razon_social||'—';
  $('kpiEmpresaCuit').textContent=emp.cuit?('CUIT '+emp.cuit):'';
  const nEmp=Object.keys(empleadosCache||{}).length;
  $('kpiEmpleados').textContent=nEmp;
  const activos=Object.values(establecimientosCache||{}).filter(e=>e.activo).length;
  $('kpiEstablecimientos').textContent=activos;
  const periodo=new Date().toISOString().slice(0,7);
  let estado='Sin generar', pend=nEmp;
  try{
    const carpetas=await api('/carpetas-mensuales?periodo='+periodo);
    if(carpetas && carpetas.length){
      const estados=carpetas.map(c=>c.estado);
      if(estados.some(x=>['presentada','aceptada','pagada'].includes(x))){ estado='Presentada'; pend=0; }
      else if(estados.some(x=>['borrador','calculada','revisada'].includes(x))){ estado='En preparación'; pend=nEmp; }
    }
  }catch(e){ /* período sin carpetas: queda Sin generar */ }
  $('kpiPendientes').textContent = nEmp ? pend : '—';
  $('kpiEstadoLiq').textContent = nEmp ? ('Mes '+periodo+' · '+estado) : 'Cargá empleados para liquidar';
}

const IDENTIDAD_CONVENIO={
  '414/05':{actividad:'Farmacia comercial / comunitaria',sindicato:'ADEF',obraSocial:'OSADEF - Obra Social de las Asociaciones de Empleados de Farmacia'},
  '659/13':{actividad:'Farmacia comercial / comunitaria',sindicato:'FATFA',obraSocial:''},
  '122/75':{actividad:'Clínica, sanatorio o geriátrico con internación',sindicato:'FATSA',obraSocial:'OSPSA - Obra Social del Personal de la Sanidad Argentina'},
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

function datosEstablecimientoParaEncuadramiento(){
  const est=establecimientosCache[$('eEstablecimiento').value];
  if(!est) return;
  if(!$('eLocalidad').value.trim()) $('eLocalidad').value=est.localidad||'';
}

function aplicarPropuestaEncuadramiento(numero){
  const c=convenios.find(x=>x.numero===numero);
  if(!c) return;
  $('eActividad').value=actividadConvenio(c);
  llenarConvenios(numero);
  $('resultadoEncuadramiento').insertAdjacentHTML('beforeend','<div class="ok" style="display:block;margin-top:6px">Propuesta aplicada. Ahora elegí la categoría que describe la tarea real.</div>');
}

async function analizarEncuadramiento(){
  const box=$('resultadoEncuadramiento');
  box.style.display='block'; box.textContent='Analizando actividad, localidad y tarea…';
  const est=establecimientosCache[$('eEstablecimiento').value]||{};
  const actividad=(est.actividad||$('eActividad').value||'').trim();
  const localidad=(est.localidad||$('eLocalidad').value||'').trim();
  try{
    const r=await api('/convenios/asistente-encuadramiento','POST',{
      actividad, localidad, provincia:est.provincia||'', tarea:$('eTareaPrincipal').value.trim()
    });
    let html=`<b>Criterio:</b> ${esc(r.criterio)}<br><small>Actividad: ${esc(actividad||'sin informar')} · Localidad: ${esc(localidad||'sin informar')}</small>`;
    if(r.faltantes.length) html+=`<div style="margin-top:7px;color:#92400e"><b>Falta revisar:</b> ${r.faltantes.map(esc).join(' · ')}</div>`;
    (r.candidatos||[]).forEach(c=>{
      html+=`<div style="margin-top:9px;padding-top:8px;border-top:1px solid #bfdbfe"><b>CCT ${esc(c.cct_numero)} — ${esc(c.nombre)}</b> <span class="etiqueta">Confianza ${esc(c.confianza)}</span><br><small>${c.motivos.map(esc).join(' · ')}</small>${c.advertencias.length?`<div style="color:#92400e;font-size:.8rem">${c.advertencias.map(esc).join(' · ')}</div>`:''}<button type="button" class="chico" style="margin-top:6px" onclick="aplicarPropuestaEncuadramiento('${esc(c.cct_numero)}')">Usar esta propuesta</button></div>`;
    });
    if(!(r.candidatos||[]).length) html+='<div style="margin-top:8px">No se eligió ningún convenio automáticamente. Completá los datos faltantes.</div>';
    box.innerHTML=html;
  }catch(e){box.innerHTML=`<span class="error" style="display:block">${esc(e.message)}</span>`;}
}

async function cargarEmpleados(){
  try{
    const lista = await api('/empleados');
    empleadosCache = {};
    const tb = $('tablaEmpleados').querySelector('tbody'); tb.innerHTML='';
    lista.forEach(e=>{
      empleadosCache[e.id] = e;
      const tr=document.createElement('tr');
      tr.innerHTML = `<td data-label="Empleado">${e.apellido}, ${e.nombre}</td><td data-label="CUIL">${e.cuil}</td><td data-label="Convenio">${e.cct_numero}</td><td data-label="Categoría">${e.categoria}</td><td data-label="Lugar">${e.lugar_trabajo||'Sin asignar'}</td><td data-label="Ingreso">${e.fecha_ingreso}</td><td class="acciones-celda"><div class="acciones-tabla"><button class="chico secundario" onclick="editarEmpleado('${e.id}')" title="Editar">✏️ Editar</button><button class="chico secundario" onclick="borrarEmpleado('${e.id}','${(e.apellido||'')+', '+(e.nombre||'')}')" title="Eliminar">🗑 Eliminar</button></div></td>`;
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
function numeroNovOpcional(id){ return $(id).value===''?null:Number($(id).value); }
function booleanoNovOpcional(id){ return $(id).value===''?null:$(id).value==='true'; }
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
  const emp=empleadosCache[$('novEmpleado').value];
  $('novUocra').style.display=emp && emp.cct_numero==='76/75'?'block':'none';
  $('novCamioneros').style.display=emp && emp.cct_numero==='40/89'?'block':'none';
  $('novUom').style.display=emp && emp.cct_numero==='260/75'?'block':'none';
}
const camposCamioneros={dias_comida:'camDiasComida',dias_viatico_especial:'camDiasViatico',pernoctadas:'camPernoctadas',kilometros_extra:'camKmExtra',kilometros_viatico:'camKmViatico',dias_en_viaje:'camDiasViaje',viajes_cordilleranos:'camCordillera',permanencias:'camPermanencias',simples_presencias:'camPresencias',permanencias_sur:'camPermanenciasSur',simples_presencias_sur:'camPresenciasSur',cruces_frontera:'camFrontera',ingresos_egresos_tdf:'camTdf',dias_plus_vacacional:'camVacaciones',traslados_unidad_descarga:'camTrasladosDescarga',viajes_transporte_automoviles:'camViajesAutomoviles',unidades_bitrenes:'camBitrenes'};
function datosCamioneros(){
  const emp=empleadosCache[$('novEmpleado').value];
  if(!emp || emp.cct_numero!=='40/89') return {};
  const datos={rama:$('camRama').value,zona:$('camZona').value,grupo_taller:$('camGrupoTaller').value,camara_frio:$('camFrio').checked,cuenca_petrolifera:$('camCuencaPetrolifera').checked,la_pampa_mendoza:$('camLaPampaMendoza').checked};
  Object.entries(camposCamioneros).forEach(([campo,id])=>datos[campo]=numeroNov(id));
  return datos;
}
function limpiarCamioneros(){
  $('camRama').value='general'; $('camZona').value='BASE'; $('camGrupoTaller').value=''; $('camFrio').checked=false; $('camCuencaPetrolifera').checked=false; $('camLaPampaMendoza').checked=false;
  Object.values(camposCamioneros).forEach(id=>$(id).value='0');
}
function cargarCamioneros(datos={}){
  limpiarCamioneros(); $('camRama').value=datos.rama||'general'; $('camZona').value=datos.zona||'BASE'; $('camGrupoTaller').value=datos.grupo_taller||''; $('camFrio').checked=Boolean(datos.camara_frio); $('camCuencaPetrolifera').checked=Boolean(datos.cuenca_petrolifera); $('camLaPampaMendoza').checked=Boolean(datos.la_pampa_mendoza);
  Object.entries(camposCamioneros).forEach(([campo,id])=>$(id).value=datos[campo]??0);
}
function datosUom(){
  const emp=empleadosCache[$('novEmpleado').value];
  if(!emp || emp.cct_numero!=='260/75') return {};
  return {horas_normales:numeroNovOpcional('uomHorasNormales'),ingresos_computables_imgr:numeroNovOpcional('uomIngresosImgr'),dias_trabajados_abril_julio:numeroNovOpcional('uomDiasAbrJul'),contrato_vigente_31_07:$('uomContratoJulio').checked,pagos_a_cuenta_absorbibles:numeroNovOpcional('uomPagosCuenta'),adicionales:{}};
}
function limpiarUom(){ $('uomHorasNormales').value=''; $('uomIngresosImgr').value=''; $('uomDiasAbrJul').value=''; $('uomContratoJulio').checked=false; $('uomPagosCuenta').value='0'; }
function cargarUom(datos={}){ limpiarUom(); $('uomHorasNormales').value=datos.horas_normales??''; $('uomIngresosImgr').value=datos.ingresos_computables_imgr??''; $('uomDiasAbrJul').value=datos.dias_trabajados_abril_julio??''; $('uomContratoJulio').checked=Boolean(datos.contrato_vigente_31_07); $('uomPagosCuenta').value=datos.pagos_a_cuenta_absorbibles??0; }
function agregarFeriadoUocra(datos={}){
  const fila=document.createElement('div'); fila.className='feriado-uocra-fila fila';
  fila.style.cssText='border:1px solid var(--borde);border-radius:8px;padding:8px';
  fila.innerHTML='<div><label>Fecha</label><input class="fu-fecha" type="date"></div><label><input class="fu-trabajado" type="checkbox"> Trabajado</label><label><input class="fu-requisito" type="checkbox"> Cumple art. 168</label><div><label>Horas jornada anterior</label><input class="fu-horas" type="number" min="0.01" max="9" step="0.01"></div><div><label>Accesorios jornada ($)</label><input class="fu-accesorios" type="number" min="0" step="0.01" value="0"></div><div style="display:flex;align-items:end"><button type="button" class="chico secundario fu-quitar">Quitar</button></div>';
  fila.querySelector('.fu-fecha').value=datos.fecha||'';
  fila.querySelector('.fu-trabajado').checked=Boolean(datos.trabajado);
  fila.querySelector('.fu-requisito').checked=Boolean(datos.cumple_requisito_art168);
  fila.querySelector('.fu-horas').value=datos.horas_jornada_anterior??'';
  fila.querySelector('.fu-accesorios').value=datos.remuneraciones_accesorias??0;
  fila.querySelectorAll('input').forEach(i=>i.addEventListener('change',sincronizarFeriadosUocra));
  fila.querySelector('.fu-quitar').onclick=()=>{fila.remove();sincronizarFeriadosUocra();};
  $('novFeriadosUocraLista').appendChild(fila);
  sincronizarFeriadosUocra();
}
function detalleFeriadosUocra(){
  return [...document.querySelectorAll('.feriado-uocra-fila')].map(f=>({
    fecha:f.querySelector('.fu-fecha').value,
    trabajado:f.querySelector('.fu-trabajado').checked,
    cumple_requisito_art168:f.querySelector('.fu-requisito').checked,
    horas_jornada_anterior:Number(f.querySelector('.fu-horas').value||0),
    remuneraciones_accesorias:Number(f.querySelector('.fu-accesorios').value||0)
  }));
}
function sincronizarFeriadosUocra(){
  const detalles=detalleFeriadosUocra();
  $('novFeriados').value=detalles.filter(d=>d.trabajado).length;
  $('novFeriadosNoTrab').value=detalles.filter(d=>!d.trabajado).length;
  $('novFeriadosHabQ1').value=detalles.filter(d=>!d.trabajado&&d.cumple_requisito_art168&&Number((d.fecha||'').slice(8,10))<=15).length;
  $('novFeriadosHabQ2').value=detalles.filter(d=>!d.trabajado&&d.cumple_requisito_art168&&Number((d.fecha||'').slice(8,10))>15).length;
}
function agregarHoraExtraUocra(datos={}){
  const fila=document.createElement('div'); fila.className='hora-extra-uocra-fila fila';
  fila.style.cssText='border:1px solid var(--borde);border-radius:8px;padding:8px';
  fila.innerHTML='<div><label>Fecha</label><input class="heu-fecha" type="date"></div><div><label>Hora de inicio</label><input class="heu-inicio" type="number" min="0" max="23.99" step="0.25" placeholder="Ej. 14"></div><div><label>Cantidad de horas</label><input class="heu-horas" type="number" min="0.01" max="3" step="0.25"></div><label><input class="heu-feriado" type="checkbox"> Es feriado</label><div style="display:flex;align-items:end"><button type="button" class="chico secundario heu-quitar">Quitar</button></div>';
  fila.querySelector('.heu-fecha').value=datos.fecha||'';
  fila.querySelector('.heu-inicio').value=datos.hora_inicio??'';
  fila.querySelector('.heu-horas').value=datos.horas??'';
  fila.querySelector('.heu-feriado').checked=Boolean(datos.es_feriado);
  fila.querySelectorAll('input').forEach(i=>i.addEventListener('change',sincronizarHorasExtraUocra));
  fila.querySelector('.heu-quitar').onclick=()=>{fila.remove();sincronizarHorasExtraUocra();};
  $('novHorasExtraUocraLista').appendChild(fila); sincronizarHorasExtraUocra();
}
function detalleHorasExtraUocra(){
  return [...document.querySelectorAll('.hora-extra-uocra-fila')].map(f=>({
    fecha:f.querySelector('.heu-fecha').value,
    hora_inicio:Number(f.querySelector('.heu-inicio').value||0),
    horas:Number(f.querySelector('.heu-horas').value||0),
    es_feriado:f.querySelector('.heu-feriado').checked
  }));
}
function sincronizarHorasExtraUocra(){
  let h50=0,h100=0;
  detalleHorasExtraUocra().forEach(d=>{
    const dia=d.fecha?new Date(d.fecha+'T12:00:00').getDay():-1;
    if(d.es_feriado||dia===0) h100+=d.horas;
    else if(dia===6){const antes=Math.max(0,Math.min(d.hora_inicio+d.horas,13)-d.hora_inicio);h50+=antes;h100+=d.horas-antes;}
    else h50+=d.horas;
  });
  $('novHE50').value=h50.toFixed(2); $('novHE100').value=h100.toFixed(2);
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
  ['novHorasQ1','novHorasQ2'].forEach(id=>$(id).value='');
  ['novAsistenciaQ1','novAsistenciaQ2'].forEach(id=>$(id).value='');
  ['novFeriadosHabQ1','novFeriadosHabQ2'].forEach(id=>$(id).value='0');
  $('novFeriadosUocraLista').innerHTML='';
  $('novHorasExtraUocraLista').innerHTML=''; $('novHorasExtraUocraAnio').value='0';
  $('novBaseUocraAnterior').value='';
  $('novHorasHormigonUocra').value='0'; $('novHorasAlturaUocra').value='0'; $('novAlturaMetrosUocra').value='';
  $('novFclCriterio').value=''; $('novFclAprobado').value=''; $('novFclFundamento').value='';
  $('novObservaciones').value='';
  $('novTipoPremio').value='pendiente';
  limpiarAdicionalesFarmacia();
  limpiarAdicionalesSanidad();
  limpiarCamioneros();
  limpiarUom();
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
      const quincenas=emp.cct_numero==='76/75'?`<br><small>Q1: ${n.horas_normales_q1??'—'} h · Q2: ${n.horas_normales_q2??'—'} h</small>`:'';
      tr.innerHTML=`<td data-label="Empleado">${emp.apellido}, ${emp.nombre}</td><td data-label="Días">${n.dias_trabajados}<br><small>Feriados: ${n.feriados_trabajados||0} trabajados · ${n.feriados_no_trabajados||0} no trabajados</small>${quincenas}</td><td data-label="Faltas">${faltas}</td><td data-label="Extras">50%: ${n.horas_extra_50} · 100%: ${n.horas_extra_100}${adicionales}</td><td data-label="Premios / descuentos">$ ${fmt(n.premios)} / $ ${fmt(n.descuentos_adicionales)}</td><td class="acciones-celda">${acciones}</td>`;
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

let carpetasCache = {};
let versionAbierta = null;

async function cargarCarpetas(){
  ocultar('carpetasError');
  const periodo=$('periodo').value;
  if(!periodo) return;
  try{
    const lista=await api('/carpetas-mensuales?periodo='+encodeURIComponent(periodo));
    carpetasCache={};
    // La versión más alta del período es la vigente; el resto son históricas y
    // se conservan tal cual fueron calculadas.
    const ultima=lista.reduce((max,c)=>Math.max(max,Number(c.version)||0),0);
    const tb=$('tablaCarpetas').querySelector('tbody'); tb.innerHTML='';
    lista.forEach(c=>{
      carpetasCache[c.id]=c;
      const tr=document.createElement('tr');
      const huella=(c.hash_sha256||'').slice(0,12);
      const vigente=Number(c.version)===ultima;
      tr.innerHTML=`<td data-label="Mes">${esc(c.periodo)}</td>`
        +`<td data-label="Versión">v${c.version}${vigente?' <span class="etiqueta">más reciente</span>':''}</td>`
        +`<td data-label="Estado"><span class="etiqueta">${esc(c.estado)}</span></td>`
        +`<td data-label="Creada (Argentina)">${fechaHora(c.created_at)}</td>`
        +`<td data-label="Huella" title="${esc(c.hash_sha256||'')}"><code>${huella}${huella?'…':''}</code></td>`
        +`<td data-label="Acción"><button class="chico secundario" onclick="verVersion('${c.id}')">Ver liquidación</button> `
        +`<button class="chico secundario" onclick="abrirCierre('${c.id}')">Revisar cierre</button></td>`;
      tb.appendChild(tr);
    });
    $('tablaCarpetas').style.display=lista.length?'table':'none';
    $('sinCarpetas').style.display=lista.length?'none':'block';
    if(versionAbierta && !carpetasCache[versionAbierta]) cerrarPanelVersion();
  }catch(e){ mostrarError('carpetasError',e.message); }
}

// ----- Lectura de una versión histórica -----
// Todo sale de carpeta.contenido: no se vuelve a liquidar ni se consulta la
// ficha actual del empleado, que pudo cambiar después del cierre.
function nombreDesdeCarpeta(carpeta, empleadoId){
  const doc=datosDocumentales(carpeta, empleadoId);
  if(doc.nombre || doc.apellido) return `${doc.nombre||''} ${doc.apellido||''}`.trim();
  const emp=empleadosCache[empleadoId];
  if(emp) return `${emp.nombre||''} ${emp.apellido||''}`.trim()+' (ficha actual)';
  return 'Empleado '+String(empleadoId).slice(0,8);
}

function datosDocumentales(carpeta, empleadoId){
  const snap=(carpeta.contenido&&carpeta.contenido.snapshot_parametros)||{};
  const emp=(snap.empleados&&snap.empleados[empleadoId])||{};
  return emp.documental||{};
}

function faltantesDeCarpeta(carpeta){
  const snap=(carpeta.contenido&&carpeta.contenido.snapshot_parametros)||{};
  const empresa=snap.empresa||{};
  const faltan=[];
  if(!empresa.razon_social) faltan.push('razón social del empleador');
  if(!empresa.cuit) faltan.push('CUIT del empleador');
  faltan.push('domicilio legal del empleador');
  const detalles=(carpeta.contenido&&carpeta.contenido.detalles)||[];
  const sinDocumental=detalles.filter(d=>!Object.keys(datosDocumentales(carpeta,d.empleado_id)).length);
  if(sinDocumental.length) faltan.push(`datos personales de ${sinDocumental.length} empleado(s): nombre, CUIL, ingreso, categoría`);
  faltan.push('fecha, forma y lugar de pago');
  return faltan;
}

async function verVersion(id){
  const carpeta=carpetasCache[id]||await api('/carpetas-mensuales/'+id);
  carpetasCache[id]=carpeta; versionAbierta=id;
  const detalles=(carpeta.contenido&&carpeta.contenido.detalles)||[];
  $('panelVersionTitulo').textContent=`Liquidación conservada — ${carpeta.periodo} v${carpeta.version}`;
  $('panelVersionMeta').innerHTML=`Estado: <b>${esc(carpeta.estado)}</b> · Creada: ${fechaHora(carpeta.created_at)} · `
    +`Empleados: <b>${detalles.length}</b><br>Huella SHA-256: <code style="font-size:.72rem">${esc(carpeta.hash_sha256||'—')}</code>`;
  const faltan=faltantesDeCarpeta(carpeta);
  const aviso=$('panelVersionFaltantes');
  if(faltan.length){
    aviso.style.display='block';
    aviso.innerHTML='<b>Para imprimir el recibo de esta carpeta falta información documental:</b><br>'
      +faltan.map(f=>'• '+esc(f)).join('<br>')
      +'<br><small>Se pide al descargar cada recibo. Los importes y conceptos no se tocan.</small>';
  } else { aviso.style.display='none'; }
  const tb=$('tablaVersionDetalle').querySelector('tbody'); tb.innerHTML='';
  detalles.forEach(d=>{
    const tr=document.createElement('tr');
    const conceptos=(d.conceptos||[]).length;
    tr.innerHTML=`<td data-label="Empleado">${esc(nombreDesdeCarpeta(carpeta,d.empleado_id))}</td>`
      +`<td data-label="Bruto" class="num">$ ${fmt(Number(d.bruto))}</td>`
      +`<td data-label="Descuentos" class="num">$ ${fmt(Number(d.total_deducciones))}</td>`
      +`<td data-label="Neto" class="num">$ ${fmt(Number(d.neto))}</td>`
      +`<td data-label="Conceptos"><button class="chico secundario" onclick="verConceptosVersion('${d.empleado_id}')">${conceptos} conceptos</button></td>`
      +`<td data-label="Recibo"><button class="chico secundario" onclick="descargarReciboHistorico('${d.empleado_id}')">PDF</button></td>`;
    tb.appendChild(tr);
  });
  $('panelVersion').style.display='block';
}

function cerrarPanelVersion(){ $('panelVersion').style.display='none'; versionAbierta=null; }

function verConceptosVersion(empleadoId){
  const carpeta=carpetasCache[versionAbierta]; if(!carpeta) return;
  const detalle=((carpeta.contenido||{}).detalles||[]).find(d=>d.empleado_id===empleadoId);
  if(!detalle) return;
  const filas=(detalle.conceptos||[]).map(c=>`<tr><td>${esc(c.descripcion)}</td><td>${esc(c.tipo)}</td>`
    +`<td class="num">$ ${fmt(Number(c.base_calculo||0))}</td><td>${esc(c.unidad||'')}</td>`
    +`<td class="num">$ ${fmt(Number(c.importe))}</td></tr>`).join('');
  const w=window.open('','_blank');
  if(!w){ alert('Permití las ventanas emergentes para ver el detalle.'); return; }
  w.document.write(`<!doctype html><meta charset="utf-8"><title>Conceptos conservados</title>`
    +`<style>body{font-family:system-ui;padding:18px}table{border-collapse:collapse;width:100%;font-size:.9rem}`
    +`th,td{border-bottom:1px solid #ddd;padding:6px 8px;text-align:left}td.num{text-align:right}</style>`
    +`<h2>${esc(nombreDesdeCarpeta(carpeta,empleadoId))}</h2>`
    +`<p>${esc(carpeta.periodo)} · versión ${carpeta.version} · conceptos tal como fueron calculados</p>`
    +`<table><thead><tr><th>Concepto</th><th>Tipo</th><th>Base</th><th>Unidad</th><th>Importe</th></tr></thead><tbody>${filas}</tbody></table>`);
  w.document.close();
}

// ----- Recibo histórico: se arma sólo con el snapshot de la carpeta -----
let metadatosRecibo = null;
const metadatosEmpleadoHistorico = {};

function pedirMetadatosRecibo(carpeta){
  if(metadatosRecibo && metadatosRecibo.carpeta===carpeta.id) return metadatosRecibo;
  const snap=(carpeta.contenido&&carpeta.contenido.snapshot_parametros)||{};
  const empresa=snap.empresa||{};
  const razon=empresa.razon_social||prompt('Razón social del empleador (no figura en esta carpeta):',empresaCache.razon_social||'');
  if(!razon) return null;
  const cuit=empresa.cuit||prompt('CUIT del empleador (no figura en esta carpeta):',empresaCache.cuit||'');
  if(!cuit) return null;
  const domicilio=prompt('Domicilio legal del empleador:',localStorage.getItem('sc_empresa_domicilio')||'');
  if(!domicilio) return null;
  const fechaPago=prompt('Fecha real de pago de este período (AAAA-MM-DD):',localStorage.getItem('sc_fecha_pago_hist')||'');
  if(!fechaPago) return null;
  const lugarPago=prompt('Lugar de pago:',localStorage.getItem('sc_lugar_pago')||'');
  if(!lugarPago) return null;
  const formaPago=prompt('Forma de pago:',localStorage.getItem('sc_forma_pago')||'');
  if(!formaPago) return null;
  localStorage.setItem('sc_empresa_domicilio',domicilio);
  localStorage.setItem('sc_fecha_pago_hist',fechaPago);
  metadatosRecibo={carpeta:carpeta.id,razon,cuit,domicilio,fechaPago,lugarPago,formaPago};
  return metadatosRecibo;
}

function pedirDatosEmpleadoHistorico(carpeta, detalle){
  const doc=datosDocumentales(carpeta, detalle.empleado_id);
  const completos=['nombre','apellido','cuil','fecha_ingreso','categoria'].every(k=>String(doc[k]||'').trim());
  if(completos) return doc;
  const clave=carpeta.id+':'+detalle.empleado_id;
  if(metadatosEmpleadoHistorico[clave]) return metadatosEmpleadoHistorico[clave];
  const snap=(carpeta.contenido&&carpeta.contenido.snapshot_parametros)||{};
  const empSnap=(snap.empleados&&snap.empleados[detalle.empleado_id])||{};
  const actual=empleadosCache[detalle.empleado_id]||{};
  const pedir=(rotulo,valor)=>prompt(rotulo+' (confirmá el dato histórico):',valor||'');
  const confirmado={
    nombre:pedir('Nombre',actual.nombre), apellido:pedir('Apellido',actual.apellido),
    cuil:pedir('CUIL',actual.cuil), legajo:pedir('Legajo',actual.legajo),
    fecha_ingreso:pedir('Fecha de ingreso (AAAA-MM-DD)',actual.fecha_ingreso),
    categoria:pedir('Categoría',empSnap.categoria||detalle.categoria||actual.categoria),
    cct_numero:pedir('Convenio',empSnap.cct||detalle.cct_numero||actual.cct_numero),
    modalidad_contrato:pedir('Modalidad de contrato',actual.modalidad_contrato),
    lugar_trabajo:pedir('Lugar de trabajo',actual.lugar_trabajo),
  };
  if(!confirmado.nombre || !confirmado.apellido || !confirmado.cuil
      || !confirmado.fecha_ingreso || !confirmado.categoria) return null;
  metadatosEmpleadoHistorico[clave]=confirmado;
  return confirmado;
}

function cuerpoReciboHistorico(carpeta, detalle, meta, doc){
  const snap=(carpeta.contenido&&carpeta.contenido.snapshot_parametros)||{};
  const empSnap=(snap.empleados&&snap.empleados[detalle.empleado_id])||{};
  const empleado={
    nombre: doc.nombre||'', apellido: doc.apellido||'', cuil: doc.cuil||'',
    legajo: doc.legajo||'', fecha_ingreso: doc.fecha_ingreso||'',
    categoria: doc.categoria||empSnap.categoria||'',
    cct_numero: doc.cct_numero||empSnap.cct||detalle.cct_numero||'',
    modalidad_contrato: doc.modalidad_contrato||'',
    antiguedad: antigTexto(doc.fecha_ingreso,carpeta.periodo),
  };
  return {
    periodo: carpeta.periodo,
    empresa:{razon_social:meta.razon,cuit:meta.cuit,domicilio:meta.domicilio},
    empleado,
    pago:{fecha:meta.fechaPago,lugar:meta.lugarPago,forma:meta.formaPago,
          establecimiento:doc.lugar_trabajo||'',domicilio_trabajo:''},
    cargas_sociales:{},
    conceptos:(detalle.conceptos||[]).map(c=>({
      codigo:c.codigo||'',descripcion:c.descripcion,tipo:c.tipo,importe:c.importe,
      base_calculo:c.base_calculo,unidad:c.unidad,cantidad:c.cantidad,
      destino_pago:c.destino_pago||null,codigo_boleta:c.codigo_boleta||null
    })),
    bruto:detalle.bruto,total_deducciones:detalle.total_deducciones,neto:detalle.neto,
  };
}

async function pedirPdf(body, nombreArchivo, reintento=true){
  const r=await fetch('/recibos/pdf',{
    method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+token()},
    body:JSON.stringify(body)
  });
  if(r.status===401 && reintento && await renovarSesion()) return pedirPdf(body,nombreArchivo,false);
  if(!r.ok){
    const e=await r.json().catch(()=>({detail:'No se pudo generar el PDF'}));
    throw new Error(e.detail||'No se pudo generar el PDF');
  }
  const blob=await r.blob(); const url=URL.createObjectURL(blob);
  const a=document.createElement('a'); a.href=url; a.download=nombreArchivo;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),60000);
}

async function descargarReciboHistorico(empleadoId){
  const carpeta=carpetasCache[versionAbierta]; if(!carpeta) return;
  const detalle=((carpeta.contenido||{}).detalles||[]).find(d=>d.empleado_id===empleadoId);
  if(!detalle){ alert('Esta carpeta no conserva el detalle de ese empleado.'); return; }
  const meta=pedirMetadatosRecibo(carpeta); if(!meta) return;
  const doc=pedirDatosEmpleadoHistorico(carpeta,detalle); if(!doc) return;
  try{
    const body=cuerpoReciboHistorico(carpeta,detalle,meta,doc);
    const apellido=(body.empleado.apellido||'empleado').replace(/\s+/g,'-');
    await pedirPdf(body,`recibo-${carpeta.periodo}-v${carpeta.version}-${apellido}.pdf`);
  }catch(e){ alert(e.message); }
}

async function descargarRecibosDeVersion(){
  const carpeta=carpetasCache[versionAbierta]; if(!carpeta) return;
  const detalles=((carpeta.contenido||{}).detalles||[]);
  if(!detalles.length){ alert('Esta carpeta no conserva detalles.'); return; }
  const meta=pedirMetadatosRecibo(carpeta); if(!meta) return;
  let errores=0;
  for(const detalle of detalles){
    try{
      const doc=pedirDatosEmpleadoHistorico(carpeta,detalle);
      if(!doc){ errores++; continue; }
      const body=cuerpoReciboHistorico(carpeta,detalle,meta,doc);
      const apellido=(body.empleado.apellido||'empleado').replace(/\s+/g,'-');
      await pedirPdf(body,`recibo-${carpeta.periodo}-v${carpeta.version}-${apellido}.pdf`);
    }catch(e){ errores++; }
  }
  if(errores) alert(`No se pudieron generar ${errores} recibo(s). Revisá los datos documentales faltantes.`);
}

let cierreActualId=null;
const siguienteEstadoObligacion={pendiente:'generada',generada:'pagada',pagada:'verificada'};
const textoAccionObligacion={pendiente:'Confirmar importe',generada:'Registrar pago',pagada:'Verificar comprobante'};

function cerrarPanelCierre(){ $('panelCierre').style.display='none'; cierreActualId=null; }
function dineroCierre(v){ return v==null?'A completar':new Intl.NumberFormat('es-AR',{style:'currency',currency:'ARS'}).format(Number(v)); }

async function abrirCierre(id){
  cierreActualId=id; ocultar('cierreError'); ocultar('cierreOk');
  $('panelCierre').style.display='block';
  $('cierreResumen').textContent='Cargando el detalle del cierre…';
  $('cierreFaltantes').innerHTML='';
  $('tablaObligaciones').querySelector('tbody').innerHTML='';
  $('cierreRevisiones').innerHTML='';
  $('panelCierre').scrollIntoView({behavior:'smooth',block:'start'});
  try{
    const d=await api('/carpetas-mensuales/'+id+'/cierre');
    $('cierreResumen').textContent=`${d.carpeta.periodo} · versión ${d.carpeta.version} · estado ${d.carpeta.estado} · huella ${(d.carpeta.hash_sha256||'').slice(0,12)}…`;
    $('cierreFaltantes').innerHTML=d.faltantes.length
      ? `<div style="background:#fef3c7;color:#92400e;padding:10px;border-radius:8px"><b>Falta para aprobar:</b> ${d.faltantes.map(esc).join(' · ')}</div>`
      : '<div style="background:#d1fae5;color:#065f46;padding:10px;border-radius:8px"><b>Controles completos.</b> Ya puede firmar un contador habilitado.</div>';
    const tb=$('tablaObligaciones').querySelector('tbody'); tb.innerHTML='';
    d.obligaciones.forEach(o=>{
      const siguiente=siguienteEstadoObligacion[o.estado];
      const tr=document.createElement('tr');
      tr.innerHTML=`<td data-label="Salida / boleta"><b>${esc(o.codigo_boleta)}</b><br><small>${esc(o.tipo)}${o.cct_numero?' · CCT '+esc(o.cct_numero):''}</small></td>
        <td data-label="Destino">${esc(o.destino_pago)}${o.url_pago?`<br><a href="${esc(o.url_pago)}" target="_blank" rel="noopener">Abrir sitio de pago</a>`:''}</td>
        <td data-label="Importe"><input id="imp-${o.id}" type="number" min="0" step="0.01" value="${o.importe==null?'':esc(o.importe)}" placeholder="Importe real" ${o.estado!=='pendiente'?'disabled':''}><small>${dineroCierre(o.importe)}</small></td>
        <td data-label="Estado"><span class="etiqueta">${esc(o.estado)}</span></td>
        <td data-label="Comprobante"><input id="comp-${o.id}" value="${esc(o.comprobante||'')}" placeholder="Nº, enlace o referencia" ${o.estado==='verificada'?'disabled':''}></td>
        <td data-label="Acción">${siguiente?`<button class="chico" onclick="avanzarObligacion('${o.id}','${siguiente}')">${textoAccionObligacion[o.estado]}</button>`:'✅ Cerrada'}</td>`;
      tb.appendChild(tr);
    });
    $('cierreRevisiones').innerHTML=d.revisiones.length
      ? '<b>Revisiones firmadas:</b> '+d.revisiones.map(r=>`${esc(r.nombre_apellido)} · matrícula ${esc(r.matricula)} · ${fechaHora(r.firmado_at)}`).join('<br>')
      : '<span style="color:#6b7280">Aún no hay revisión profesional firmada.</span>';
  }catch(e){
    $('cierreResumen').textContent='No se pudo cargar el detalle del cierre.';
    mostrarError('cierreError',e.message);
  }
}

async function avanzarObligacion(id,estado){
  ocultar('cierreError'); ocultar('cierreOk');
  const valor=$('imp-'+id).value;
  try{
    await api(`/carpetas-mensuales/${cierreActualId}/obligaciones/${id}`,'PATCH',{
      estado, comprobante:$('comp-'+id).value.trim(), importe:valor===''?null:Number(valor)
    });
    await abrirCierre(cierreActualId);
    $('cierreOk').textContent='Estado registrado con trazabilidad.'; $('cierreOk').style.display='block';
  }catch(e){ mostrarError('cierreError',e.message); }
}

async function aprobarCierre(){
  ocultar('cierreError'); ocultar('cierreOk');
  if(!cierreActualId) return;
  try{
    const d=await api(`/carpetas-mensuales/${cierreActualId}/aprobar`,'POST',{
      observaciones:$('cierreObservaciones').value.trim()
    });
    await abrirCierre(cierreActualId); await cargarCarpetas();
    $('cierreOk').textContent=`Revisión firmada por ${d.contador} · matrícula ${d.matricula}.`;
    $('cierreOk').style.display='block';
  }catch(e){ mostrarError('cierreError',e.message); }
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
  Object.assign(cuerpo,{
    horas_normales_q1:numeroNovOpcional('novHorasQ1'),
    horas_normales_q2:numeroNovOpcional('novHorasQ2'),
    asistencia_perfecta_q1:booleanoNovOpcional('novAsistenciaQ1'),
    asistencia_perfecta_q2:booleanoNovOpcional('novAsistenciaQ2'),
    feriados_habilitados_q1:numeroNov('novFeriadosHabQ1'),
    feriados_habilitados_q2:numeroNov('novFeriadosHabQ2')
  });
  Object.assign(cuerpo,{
    feriados_uocra_detalle:detalleFeriadosUocra(),
    fcl_criterio_aniversario:$('novFclCriterio').value||null,
    fcl_aprobado_por:$('novFclAprobado').value.trim()||null,
    fcl_fundamento:$('novFclFundamento').value.trim()||null
    ,base_contribucion_uocra_mes_anterior:numeroNovOpcional('novBaseUocraAnterior')
    ,horas_extra_uocra_detalle:detalleHorasExtraUocra()
    ,horas_extra_uocra_acumuladas_anio:numeroNov('novHorasExtraUocraAnio')
    ,horas_hormigon_manual_uocra:numeroNov('novHorasHormigonUocra')
    ,horas_altura_uocra:numeroNov('novHorasAlturaUocra')
    ,altura_metros_uocra:numeroNovOpcional('novAlturaMetrosUocra')
    ,camioneros_detalle:datosCamioneros()
    ,uom_detalle:datosUom()
  });
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
  $('novHorasQ1').value=n.horas_normales_q1??''; $('novHorasQ2').value=n.horas_normales_q2??'';
  $('novAsistenciaQ1').value=n.asistencia_perfecta_q1===null?'':String(n.asistencia_perfecta_q1);
  $('novAsistenciaQ2').value=n.asistencia_perfecta_q2===null?'':String(n.asistencia_perfecta_q2);
  $('novFeriadosHabQ1').value=n.feriados_habilitados_q1||0;
  $('novFeriadosHabQ2').value=n.feriados_habilitados_q2||0;
  $('novFeriadosUocraLista').innerHTML='';
  (n.feriados_uocra_detalle||[]).forEach(agregarFeriadoUocra);
  $('novFclCriterio').value=n.fcl_criterio_aniversario||'';
  $('novFclAprobado').value=n.fcl_aprobado_por||'';
  $('novFclFundamento').value=n.fcl_fundamento||'';
  $('novBaseUocraAnterior').value=n.base_contribucion_uocra_mes_anterior??'';
  $('novHorasExtraUocraLista').innerHTML='';
  (n.horas_extra_uocra_detalle||[]).forEach(agregarHoraExtraUocra);
  $('novHorasExtraUocraAnio').value=n.horas_extra_uocra_acumuladas_anio||0;
  $('novHorasHormigonUocra').value=n.horas_hormigon_manual_uocra||0;
  $('novHorasAlturaUocra').value=n.horas_altura_uocra||0;
  $('novAlturaMetrosUocra').value=n.altura_metros_uocra??'';
  cargarCamioneros(n.camioneros_detalle||{});
  cargarUom(n.uom_detalle||{});
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
  actualizarAdicionalesConvenio();
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
  $('eEstablecimiento').value = e.establecimiento_id || '';
  $('eLugarDesde').value = '';
  $('eLocalidad').value = e.localidad || '';
  $('eFilial').value = e.filial_sindical || '';
  $('eRemun').value = e.remuneracion_pactada || '';
  $('eTareaPrincipal').value = '';
  $('resultadoEncuadramiento').style.display='none';

  $('btnGuardarEmp').textContent = 'Guardar cambios';
  $('btnCancelarEmp').style.display = 'inline-block';
  $('alta').style.display = 'block';
  toggleCbu();
}

function cancelarEdicion(){
  editandoEmpleadoId = null;
  obraSocialSugeridaAnterior = '';
  ['eNombre','eApellido','eCuil','eFecha','eNacimiento','eDomicilio','eLegajo','eObraSocial','eLugarDesde','eCbu','eRemun','eFormaPago','eLocalidad','eFilial','eSindicato','eTareaPrincipal'].forEach(i=>$(i).value='');
  $('resultadoEncuadramiento').style.display='none';
  $('eEstablecimiento').value='';
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
  const lugarElegido=$('eEstablecimiento').value || null;
  const lugarAnterior=editandoEmpleadoId ? (empleadosCache[editandoEmpleadoId].establecimiento_id||null) : null;
  if(editandoEmpleadoId && lugarElegido!==lugarAnterior && !$('eLugarDesde').value.trim()){
    mostrarError('empError','Indicá desde qué fecha cambia el lugar de trabajo.'); return;
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
      lugar_trabajo:null,
      establecimiento_id:$('eEstablecimiento').value || null,
      lugar_trabajo_desde:fechaIso($('eLugarDesde').value,'Fecha del cambio de lugar'),
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
      <span style="font-size:.8rem;color:#6b7280">La cuota sindical va por boleta aparte. Este subtotal todavía no incluye ART ni otros datos contractuales pendientes.</span>
      <span class="neto" style="color:#b45309">Subtotal calculado — falta ART: $ ${fmt(totAp+totCo)}</span>
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

async function liquidar(confirmarProvisorios=false){
  ocultar('liqError'); $('resultados').innerHTML='<p style="margin-top:12px">Calculando…</p>';
  try{
    const d = await api('/liquidaciones','POST',{
      periodo:$('periodo').value, tipo:'mensual', novedades:[],
      confirmar_provisorios:confirmarProvisorios
    });
    ultimaLiq = d;
    if(!d.detalles.length){
      const motivos=(d.bloqueos||[]).map(b=>`<li>${esc(b.categoria||'Empleado')}: ${esc(b.motivo)}</li>`).join('');
      const confirmables=(d.bloqueos||[]).filter(b=>b.requiere_confirmacion);
      const confirmar=confirmables.length?`<div style="margin-top:10px;padding:10px;border:1px solid #f59e0b;background:#fffbeb;border-radius:8px"><b>Hay una escala anterior disponible como valor provisorio.</b><br><small>La liquidación y su historial quedarán identificados como provisorios. No equivale a una escala nueva ni a una aprobación profesional.</small><br><button class="chico" style="margin-top:8px" onclick="liquidar(true)">Confirmar y calcular provisoriamente</button></div>`:'';
      $('resultados').innerHTML=motivos?`<div class="error" style="display:block"><b>No se pudo calcular:</b><ul>${motivos}</ul></div>${confirmar}`:'<p style="margin-top:12px">No hay empleados para liquidar.</p>';
      return;
    }
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
        <b>${emp.apellido}, ${emp.nombre}</b> <span class="etiqueta">CCT ${emp.cct_numero}</span> <span class="etiqueta">${d.periodo}</span> ${det.escala_provisoria?'<span class="etiqueta" style="background:#fffbeb;color:#92400e">ESCALA PROVISORIA CONFIRMADA</span>':''} ${det.pendiente_aprobacion_contador?'<span class="etiqueta" style="background:#fff3cd;color:#7c5700">NÚMEROS REALES · PENDIENTE APROBACIÓN CONTADOR</span>':det.vista_previa?'<span class="etiqueta" style="background:#fff3cd;color:#7c5700">VISTA PREVIA</span>':''}
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
    const bloqueos=(d.bloqueos||[]).map(b=>`<li>${esc(b.categoria||'Empleado')}: ${esc(b.motivo)}</li>`).join('');
    $('resultados').innerHTML = (bloqueos?`<div class="error" style="display:block"><b>Empleados bloqueados:</b><ul>${bloqueos}</ul></div>`:'') + html + resumenF931(d) + resumenSindical(d);
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
   +'.hoja{border:0;margin:0!important;padding:0!important;width:200mm;max-width:200mm;min-height:0}.btn{display:none!important}'
   +'.barra{padding:4px 8px;border-radius:3px}.barra h1{font-size:9pt}.barra small{font-size:7pt}.marca-recibo{gap:6px}.marca-recibo svg{width:26px;height:26px}'
   +'h2{font-size:7pt;margin:4px 0 2px;padding:2px 5px;border-left-width:3px}.grid2{gap:5px}.caja{padding:4px;font-size:7pt;border-radius:3px}.dato{padding:0;line-height:1.18}'
   +'table{font-size:7pt;line-height:1.12;page-break-inside:avoid}th,td{font-size:7pt;padding:1.5px 4px}.tot{page-break-inside:avoid}'
   +'.neto{font-size:9pt;margin-top:3px!important}.resumen{display:block;font-size:7pt;page-break-inside:avoid}.resumen svg{display:none}.ley{font-size:7pt;display:grid;grid-template-columns:1fr 1fr;gap:1px 10px}.ley div{margin:0!important}'
   +'.firma{margin-top:10px;font-size:7pt;page-break-inside:avoid}.firma div{padding-top:2px}h2,.barra,.grid2,.neto{page-break-inside:avoid}body{-webkit-text-size-adjust:100%}}</style></head><body>'
   +'<button class="btn" onclick="window.print()">⬇ Descargar / Imprimir PDF</button>'
   +'<div class="hoja">'
   +'<div class="barra"><div class="marca-recibo"><svg viewBox="0 0 64 64" role="img" aria-label="Logo Sueldo Claro"><path d="M12 7h27l10 10v25H12z" fill="none" stroke="#fff" stroke-width="5" stroke-linejoin="round"/><path d="M39 7v11h10M20 24h19M20 33h12" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/><path d="m31 45 8 8 15-18" fill="none" stroke="#fbbf24" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/></svg><div><b>Sueldo Claro</b><h1>RECIBO DE HABERES</h1></div></div><small>Anexo III · Dto. 407/2026 · Período '+per+'</small></div>'
   +'<div class="aviso">'+(det.pendiente_aprobacion_contador?'NÚMEROS REALES DE FUENTES OFICIALES — PENDIENTE DE REVISIÓN Y APROBACIÓN POR CONTADOR PÚBLICO.':'Documento de prueba — valores a verificar por contador matriculado.')+'</div>'
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
    bruto:det.bruto,total_deducciones:det.total_deducciones,neto:det.neto,
    pendiente_aprobacion_contador:Boolean(det.pendiente_aprobacion_contador)
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
