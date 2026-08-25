# Fábrica de convenios

Cada convenio se mantiene en un único manifiesto JSON, dividido en:

1. `identidad`: número, nombre y sindicato;
2. `estructura`: categorías, reglas permanentes y zonas;
3. `periodos`: escalas y parámetros con vigencia y fuente;
4. `motor`: bloqueado, vista previa o productivo.

Copiar `PLANTILLA_PAQUETE.json`, completar los datos documentados y compilar:

```powershell
python backend/tools/compilar_paquete_convenio.py CONVENIO.json CONVENIO.sql
```

El compilador no consulta Internet, no estima importes y no arrastra valores de
otro período. Antes de producir SQL rechaza duplicados, categorías inexistentes,
matrices incompletas y valores verificados sin fuente. El estado `PRODUCTIVO`
también exige escalas habilitadas y pruebas de regresión declaradas.

El SQL resultante es transaccional y reejecutable. Al final registra versión,
huella SHA-256 y resumen en `cct_paquete_version`, de modo que una auditoría puede
determinar exactamente qué paquete fue instalado.
