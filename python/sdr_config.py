"""Configuración central del proyecto (única fuente de verdad para parámetros de RF).

Todo lo que depende del hardware vive aquí. Para cambiar de SDR (RTL-SDR -> SDR de 12 bits
10 kHz-2 GHz) solo se edita el perfil activo; scripts y flowgraphs leen estos valores.
"""

# --- Perfiles de hardware -------------------------------------------------------------
# block: familia de bloque de GNU Radio (gr-osmosdr para RTL-SDR, SoapySDR para el resto).
SDR_PROFILES = {
    # RTL-SDR (RTL2832U + R820T2): ADC de 8 bits, 24-1766 MHz, <=2.4 Msps estables.
    "rtlsdr": {"block": "osmosdr", "args": "rtl=0", "adc_bits": 8,
               "fs_max": 2.4e6, "gain_db": 30.0},
    # SDR genérico vía SoapySDR (p. ej. 12 bits, 10 kHz-2 GHz). Ajustar 'args' con
    # SoapySDRUtil --find una vez que se tenga el equipo.
    "soapy12bit": {"block": "soapy", "args": "driver=", "adc_bits": 12,
                   "fs_max": 10e6, "gain_db": 30.0},
}
ACTIVE_PROFILE = "rtlsdr"

# --- Parámetros de recepción FM (independientes del hardware) ---------------------------
# 1.2 Msps: divisible entre 240 kHz (decim 5) y entre 48 kHz (decim total 25), y dentro
# del rango estable del RTL-SDR (evita pérdida de muestras que aparece cerca de 2.56 Msps).
FS_RF = 1.2e6
CHANNEL_DECIM = 5                     # 1.2 Msps -> 240 kHz (banda base del canal FM)
FS_MPX = FS_RF / CHANNEL_DECIM        # 240 kHz: fs de la señal compuesta estéreo (MPX)
AUDIO_DECIM = 5                       # 240 kHz -> 48 kHz
FS_AUDIO = FS_MPX / AUDIO_DECIM       # 48 kHz: estándar de audio
FM_DEV = 75e3                         # desviación máxima FM comercial (Hz)
AUDIO_BW = 15e3                       # ancho de banda de audio FM (Hz)
DEEMPH_TAU = 75e-6                    # de-énfasis: 75 us en América (50 us en Europa)
CHANNEL_CUTOFF = 100e3                # canal FM de 200 kHz -> +-100 kHz
CHANNEL_TRANSITION = 50e3

# Frecuencia a sintonizar (Hz). Aún no definida: elegir tras medir el espectro real.
FM_STATION_HZ = 89.7e6                # candidata: XHUNL Radio UANL (cambiar libremente)
