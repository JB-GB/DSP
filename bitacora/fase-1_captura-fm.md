# Fase 1 — Captura FM + demodulación
Fecha: 2026-09-25

## Objetivo de la fase
Construir la cadena RF → canal FM → demodulación WBFM → audio y archivo, y generar evidencia (espectro RF, MPX con piloto, audio) de forma agnóstica al SDR.

## Qué se implementó
- `python/sdr_config.py`: parámetros de RF centralizados y perfiles de hardware (`rtlsdr` por osmosdr, `soapy12bit` por SoapySDR).
- `python/fm_demod.py`: cadena de referencia NumPy/SciPy (filtro de canal Kaiser, discriminador de cuadratura, de-énfasis 75 µs, LPF de audio 15 kHz, 48 kHz).
- `python/fm_synth.py`: emisora estéreo sintética (MPX con piloto 19 kHz y L−R a 38 kHz, pre-énfasis, vecina a +400 kHz, AWGN 30 dB) para trabajar sin dongle.
- `python/make_fm_flowgraphs.py` → `flowgraphs/fm_rx_sdr.grc` (osmosdr) y `flowgraphs/fm_rx_archivo.grc` (reproduce un `.cfile`); ambos compilan con `grcc` a `.py`.
- `python/fase1_evidencia.py`: figuras, WAV y métricas (acepta `--iq captura.cfile`).
- `python/validar_flowgraph.py`: compara la cadena de bloques de GNU Radio contra la referencia NumPy.

## Teoría cubierta
`theory/01_fm_demod.md`: FM y frecuencia instantánea, regla de Carson, MPX estéreo, pre/de-énfasis, arquitectura RTL2832U, demodulador de cuadratura (derivado), justificación de cada parámetro.

## Decisiones técnicas y justificación
- fs = 1.2 Msps: estable en RTL-SDR y divisible a 240 kHz y 48 kHz con decimaciones enteras (5 y 5).
- Se separa el MPX (240 kHz) del audio para poder ver el piloto de 19 kHz y guardar el MPX crudo.
- Sin dongle: se valida con señal sintética con verdad conocida; la captura real queda pendiente y marcada como tal.
- Corrección conceptual respecto al enunciado: la desviación de 75 kHz no "limita" el audio a 15 kHz; los 15 kHz son una decisión de la norma para que Carson (180 kHz) quepa en 200 kHz (ver teoría §1).

## Evidencia generada
- `results/figures/fase1_sint_01_rf_waterfall.png`: espectro y waterfall de RF (estación en 0 Hz y vecina en +400 kHz).
- `results/figures/fase1_sint_02_mpx.png`: MPX con piloto de 19 kHz y bandas laterales del estéreo.
- `results/figures/fase1_sint_03_audio.png`: espectro del audio demodulado.
- `results/audio_samples/fase1_sint_audio_mono.wav`: audio mono sintético recuperado.
- `results/metrics/fase1_sint_metricas.json`, `fase1_validacion_gnuradio_vs_numpy.json`.

## Resultados / métricas clave
- Piloto medido 0.099 (esperado 0.100).
- Los 7 tonos de (L+R)/2 se recuperan con error ≤ 0.11 dB.
- Residuo del piloto en el audio: −109 dBFS.
- GNU Radio vs NumPy: correlación 0.99998 (desfase de 3 muestras por diferencia de retardo de grupo).

## Problemas encontrados y cómo se resolvieron
- El shell rechazaba heredocs largos con comillas; los archivos se crearon con el editor.
- Primer diseño de pre-énfasis como inverso del RC discreto: tenía un polo en z = −1 (marginalmente estable). Se resolvió aplicándolo analíticamente por tono (ganancia y fase de 1 + jωτ).
- `firdes.WIN_KAISER` no existe en GNU Radio 3.10: se usa `gnuradio.fft.window.WIN_KAISER`.
- `grcc` avisa que el bloque throttle está obsoleto y coexiste con el sink de audio: esperado en el flowgraph de archivo (sin reloj de hardware).
- WSL2 sin GUI: no se usa; solo radioconda en Windows.

## Pendientes / ideas para el reporte final
- **Captura real** (waterfall/FFT de la emisora, piloto real) cuando llegue el SDR: `python python/fase1_evidencia.py --iq captura.cfile`. Hasta entonces la Fase 1 queda validada solo con señal sintética.
- Ejecutar `rtl_test` y registrar el hardware en `results/logs/` (pendiente de la Fase 0).
- Elegir emisora tras un barrido de espectro (candidata: 89.7 XHUNL).
- Probar el flowgraph `fm_rx_archivo.grc` con GUI generando antes `python python/fm_synth.py synth_fm.cfile`.
