# Fase 0 — Setup del repositorio
Fecha: 2026-09-24

## Objetivo de la fase
Dejar la estructura del repositorio y el entorno reproducible listos, y documentar el estado real del hardware/software.

## Qué se implementó
- Estructura de carpetas (`flowgraphs/`, `python/`, `theory/`, `results/{figures,metrics,audio_samples,logs}`, `simulations/`, `bitacora/`) con `.gitkeep`.
- `README.md`, `requirements.txt` (librerías pip) y `environment.md` (GNU Radio, driver WinUSB, verificación).

## Teoría cubierta
Ninguna todavía (arranca en Fase 1: `theory/01_fm_demod.md`).

## Decisiones técnicas y justificación
- GNU Radio se separa de `requirements.txt` porque no se instala con pip; se recomienda Radioconda en Windows.
- Hardware: RTL-SDR (probablemente V3, aún sin verificar). Alternativa <45 USD por evaluar (ver pendientes).

## Evidencia generada
- `environment.md`: procedimiento y estado del entorno.

## Resultados / métricas clave
- Python 3.12.10 disponible.
- `rtl_test` y `gnuradio-companion` NO detectados en PATH. **La verificación del RTL-SDR (chipset, rango de sintonía, tasa de muestreo estable) no se ha realizado**; falta instalar drivers y ejecutar `rtl_test`.

## Problemas encontrados y cómo se resolvieron
- GNU Radio / rtl-sdr ausentes en el equipo: pendiente de instalación por parte del usuario (requiere Zadig con el dongle conectado).

## Pendientes / ideas para el reporte final
- Instalar Radioconda, driver WinUSB y correr `rtl_test`; registrar salida en `results/logs/`.
- Definir estación de FM (no indicada aún).
- Fonocardiograma: sintetizar en Python (Fase 3); opcional mini-fase de investigación de datos reales (PhysioNet / PASCAL).
- Comparar RTL-SDR V3 contra alternativas económicas.
