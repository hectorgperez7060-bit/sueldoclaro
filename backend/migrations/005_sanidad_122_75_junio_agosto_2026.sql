-- CCT 122/75: escala y obligaciones verificadas para junio-agosto 2026.
-- Fuente: acuerdo FATSA del 19/06/2026, EX-2026-25687052-APN-DGDTEYSS#MCH.
-- No extrapola la escala de agosto a septiembre: la revisión fue pactada para ese mes.

BEGIN;

INSERT INTO public.cct (
  id, numero, nombre, sindicato, antiguedad_pct_por_anio,
  aplica_presentismo, aplica_cuota_sindical, activo
)
VALUES (
  gen_random_uuid(), '122/75', 'Clínicas, sanatorios, geriátricos y establecimientos con internación',
  'FATSA / sindicato de primer grado', 0.02, false, false, true
)
ON CONFLICT (numero) DO UPDATE SET
  nombre = EXCLUDED.nombre,
  sindicato = EXCLUDED.sindicato,
  antiguedad_pct_por_anio = EXCLUDED.antiguedad_pct_por_anio,
  aplica_presentismo = EXCLUDED.aplica_presentismo,
  aplica_cuota_sindical = EXCLUDED.aplica_cuota_sindical,
  activo = true;

CREATE TEMP TABLE tmp_escala_sanidad (
  categoria text NOT NULL,
  junio numeric(18,2) NOT NULL,
  julio numeric(18,2) NOT NULL,
  agosto numeric(18,2) NOT NULL
) ON COMMIT DROP;

INSERT INTO tmp_escala_sanidad VALUES
('Profesionales Bioquímicos, Nutricionistas, Farmacéuticos y Kinesiólogos',1422958.53,1451417.70,1492490.50),
('Obstétricas e instrumentadoras',1294067.57,1319948.92,1357301.37),
('Cabos/as de cirugía',1294067.57,1319948.92,1357301.37),
('Cabos/as de Piso o Pabellón',1271382.01,1296809.65,1333507.29),
('Enfermeros/as de Cirugía y personal de esterilización',1237354.93,1262102.03,1297817.50),
('Auxiliar Técnico de Rayos X',1237354.93,1262102.03,1297817.50),
('Pedicuros y Masajistas',1237354.93,1262102.03,1297817.50),
('Enfermero/a de Piso o Consultorios Externos',1203321.66,1227388.10,1262121.22),
('Personal Especializado en Terapia Intensiva, Clímax, Unidad Coronaria, Nursery, Foniatría y Riñón artificial',1203321.66,1227388.10,1262121.22),
('Personal destinado a la atención de enfermos mentales y nerviosos',1203321.66,1227388.10,1262121.22),
('Personal Técnico de Hemoterapia, Fisioterapia, Anatomía Patológica y Laboratorio',1150390.66,1173398.47,1206603.77),
('Ayudante de radiología, Fisioterapia, Hemoterapia, Anatomía Patológica y Laboratorio',1150390.66,1173398.47,1206603.77),
('Mucamas de Cirugía o sin atingencia con la atención de enfermos',1069094.28,1090476.16,1121334.89),
('Asistente Geriátrica',1046409.13,1067337.32,1097541.25),
('Asistente de Comedores con atención al público',1040738.82,1061553.60,1091593.87),
('Camilleros y fotógrafos',1040738.82,1061553.60,1091593.87),
('Personal de Lavadero y ropería',1023723.00,1044197.46,1073746.57),
('Mucamas de Piso, Consultorios Externos y Geriátricos',1018054.09,1038415.17,1067800.66),
('Mantenimiento - Oficiales',1170238.26,1193643.02,1227421.21),
('Mantenimiento - Medio oficiales',1102172.07,1124215.52,1156029.02),
('Mantenimiento - Ascensoristas, Porteros y Serenos',1057750.79,1078905.81,1109437.12),
('Mantenimiento - Jardineros',1018054.09,1038415.17,1067800.66),
('Mantenimiento - Peones en general',1040738.82,1061553.60,1091593.87),
('Cocina - Primer cocinero, repostero o fiambrero',1170238.26,1193643.02,1227421.21),
('Cocina - Segundo cocinero, repostero o fiambrero',1105958.12,1128077.28,1160000.06),
('Cocina - Cocinero/a de Establecimientos Geriátricos',1105958.12,1128077.28,1160000.06),
('Cocina - Encargado/a de Office, cafetero o Jefe de despacho',1105958.12,1128077.28,1160000.06),
('Cocina - Ayudante de cocina y cacerolero',1083274.20,1104939.68,1136207.71),
('Cocina - Peones de cocina en general',1018054.09,1038415.17,1067800.66),
('Administrativo de Primera',1139044.11,1161824.99,1194702.78),
('Administrativo de Segunda',1105958.12,1128077.28,1160000.06),
('Administrativo de Tercera',1072875.98,1094333.50,1125301.39),
('Cadete',956604.46,975736.55,1003348.33),
('Geriátricos - Auxiliar de Enfermería',1090832.28,1112648.93,1144135.11);

CREATE TEMP TABLE tmp_periodos_sanidad AS
SELECT categoria, periodo, hasta, basico
FROM tmp_escala_sanidad
CROSS JOIN LATERAL (VALUES
  (DATE '2026-06-01', DATE '2026-06-30', junio),
  (DATE '2026-07-01', DATE '2026-07-31', julio),
  (DATE '2026-08-01', DATE '2026-08-31', agosto)
) p(periodo, hasta, basico);

UPDATE public.escala_salarial e
SET basico = p.basico, valid_to = p.hasta,
    fuente = 'Acuerdo FATSA CCT 122/75 del 19/06/2026 — EX-2026-25687052',
    is_verified = true
FROM tmp_periodos_sanidad p
WHERE e.cct_numero = '122/75' AND e.categoria = p.categoria
  AND e.valid_from = p.periodo;

INSERT INTO public.escala_salarial (
  id, cct_numero, categoria, basico, valid_from, valid_to, fuente, is_verified, version
)
SELECT gen_random_uuid(), '122/75', p.categoria, p.basico, p.periodo, p.hasta,
       'Acuerdo FATSA CCT 122/75 del 19/06/2026 — EX-2026-25687052', true, 1
FROM tmp_periodos_sanidad p
WHERE NOT EXISTS (
  SELECT 1 FROM public.escala_salarial e
  WHERE e.cct_numero = '122/75' AND e.categoria = p.categoria
    AND e.valid_from = p.periodo
);

CREATE TEMP TABLE tmp_param_sanidad (
  codigo text, valor numeric(18,8), unidad text, ambito text,
  desde date, hasta date, incidencias jsonb
) ON COMMIT DROP;

INSERT INTO tmp_param_sanidad VALUES
('SANIDAD_SUMA_NR_JUN_JUL',90000,'ARS','no_rem',DATE '2026-06-01',DATE '2026-07-31',
 '{"integra_antiguedad":false,"integra_presentismo":false,"aporte_jubilacion":false,"aporte_obra_social":false,"aporte_sindicato":true}'::jsonb),
('SANIDAD_SUMA_NR_AGO',80000,'ARS','no_rem',DATE '2026-08-01',DATE '2026-08-31',
 '{"integra_antiguedad":false,"integra_presentismo":false,"aporte_jubilacion":false,"aporte_obra_social":false,"aporte_sindicato":true}'::jsonb),
('SANIDAD_DIA_SANIDAD_122/75',68925.70,'ARS','no_rem',DATE '2026-09-01',DATE '2026-09-30',
 '{"integra_antiguedad":false,"integra_presentismo":false,"aporte_jubilacion":false,"aporte_obra_social":false,"aporte_sindicato":true}'::jsonb),
('APORTE_SOLIDARIO_FATSA_122/75',0.01,'%','ded_todos',DATE '2026-02-01',DATE '2027-01-31',
 '{"base_deduccion":"sindical","destino_pago":"FATSA","codigo_boleta":"FATSA_122_APORTES","canal_pago":"Sistema de Aportes FATSA","url_pago":"https://www.sanidad.org.ar/aportesconvenios/","regla_vencimiento":"Mensual, según boleta emitida por FATSA","fuente_pago":"Acuerdo CCT 122/75 cláusula 11"}'::jsonb),
('CONTRIB_EXTRAORDINARIA_FATSA_122/75',15000,'ARS','contrib_emp',DATE '2026-02-01',DATE '2027-01-31',
 '{"meses_excluidos":[6,12],"destino_pago":"FATSA/OSPSA","codigo_boleta":"FATSA_122_CONTRIB_EXTRA","canal_pago":"Sistema de Aportes FATSA","url_pago":"https://www.sanidad.org.ar/aportesconvenios/","regla_vencimiento":"Día 15 de cada mes o hábil siguiente; no corresponde en junio ni diciembre de 2026","fuente_pago":"Acuerdo CCT 122/75 cláusula 10"}'::jsonb),
('CONTRIB_CAPACITACION_FATSA_122/75',0.01,'%','contrib_emp',DATE '2026-02-01',DATE '2027-01-31',
 '{"base_contribucion":"remunerativa","destino_pago":"FATSA","codigo_boleta":"FATSA_122_CAPACITACION","canal_pago":"Sistema de Aportes FATSA","url_pago":"https://www.sanidad.org.ar/aportesconvenios/","regla_vencimiento":"Mismo vencimiento mensual que los aportes de la Seguridad Social","fuente_pago":"CCT 122/75 — Fondo de Formación y Capacitación"}'::jsonb);

UPDATE public.parametro_legal p
SET valor = t.valor, unidad = t.unidad, ambito = t.ambito,
    valid_to = t.hasta, fuente = 'CCT 122/75 — FATSA, fuente oficial',
    is_verified = true, cct_numero = '122/75', incidencias = t.incidencias
FROM tmp_param_sanidad t
WHERE p.codigo = t.codigo AND p.valid_from = t.desde;

INSERT INTO public.parametro_legal (
  id, codigo, valor, unidad, ambito, valid_from, valid_to,
  fuente, is_verified, version, cct_numero, incidencias
)
SELECT gen_random_uuid(), t.codigo, t.valor, t.unidad, t.ambito, t.desde, t.hasta,
       'CCT 122/75 — FATSA, fuente oficial', true, 1, '122/75', t.incidencias
FROM tmp_param_sanidad t
WHERE NOT EXISTS (
  SELECT 1 FROM public.parametro_legal p
  WHERE p.codigo = t.codigo AND p.valid_from = t.desde
);

COMMIT;
