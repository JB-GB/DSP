# Entorno reproducible

## Python (análisis)
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## GNU Radio + RTL-SDR en Windows
GNU Radio no es instalable vía pip. Opciones (de más a menos recomendada en Windows):

1. **Radioconda** (conda con gnuradio, gr-osmosdr, soapysdr ya empaquetados): https://github.com/ryanvolz/radioconda
2. **Instalador oficial de GNU Radio 3.10** para Windows.
3. **WSL2 + Ubuntu** (`apt install gnuradio gr-osmosdr rtl-sdr`); el paso de USB requiere `usbipd-win`.

## Driver del RTL-SDR (Windows)
El dongle necesita el driver **WinUSB** en la interfaz 0 (no el driver de TV-DVB de Windows). Se instala con **Zadig** (https://zadig.akeo.ie): Options > List All Devices > "Bulk-In, Interface (Interface 0)" > WinUSB.

## Verificación
```bash
rtl_test -t        # detecta el dispositivo y el tuner
rtl_test -s 2400000  # prueba de tasa de muestreo estable (buscar 0 lost samples)
```
La salida se guarda en `results/logs/rtl_test_*.log` y se resume en la bitácora de la Fase 0.

## Estado actual de este equipo (2026-09-24)
- Python 3.12.10 presente.
- `rtl_test` y `gnuradio-companion`: **no encontrados en PATH** (pendiente de instalar).
