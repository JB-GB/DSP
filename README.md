# DSP — RTL-SDR + GNU Radio con extensión biomédica/telecom

Proyecto académico-portafolio (Procesamiento Digital de Señales).
Captura de FM comercial, banco de filtros de 3 bandas, reinterpretación como tele-auscultación,
cuantificación de SNR por banda y monitoreo de espectro MICS/ISM (EMC).

> Limitación de hardware: el RTL-SDR es **solo receptor**. Toda "transmisión" biomédica es
> simulada dentro del flowgraph; no hay enlace RF real hacia un paciente.

## Estructura
| Carpeta | Contenido |
|---|---|
| `flowgraphs/` | Flowgraphs `.grc` y `.py` generados |
| `python/` | Scripts de análisis y bloques embebidos |
| `theory/` | Notas teóricas en Markdown por tema |
| `results/` | `figures/`, `metrics/`, `audio_samples/`, `logs/` (evidencia reproducible) |
| `simulations/` | Simulaciones interactivas |
| `bitacora/` | Una entrada por fase (`fase-N_nombre.md`) |

## Fases
0. Setup · 1. Captura FM + demodulación · 2. Banco de filtros (Butterworth) ·
3. Tele-auscultación · 4. SNR por banda · 5. MICS/ISM y EMC · 6. Cierre técnico

## Entorno
Ver [environment.md](environment.md) y [requirements.txt](requirements.txt).

## Convención de commits
`[Acción] [Objeto] [objetivo]`, p. ej. `Add filter bank script for splitting audio into 3 bands`.
