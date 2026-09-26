"""Sintetizador de una transmisión FM de difusión estéreo (sustituye al SDR sin dongle).

Produce IQ a FS_RF con la estructura real del estándar: MPX = (L+R) + piloto 19 kHz +
(L-R) DSB-SC en 38 kHz, pre-énfasis 75 us, desviación pico 75 kHz. La señal es SINTÉTICA:
sirve para validar la cadena con verdad de referencia conocida; no reemplaza una captura.
"""
import numpy as np

import sdr_config as cfg

# Tonos (Hz -> amplitud) por canal; cubren 100 Hz-12 kHz y L != R para que L-R exista
# (el receptor mono debe recuperar (L+R)/2).
TONES_L = {100: 0.25, 440: 0.20, 1000: 0.15, 5000: 0.04, 10000: 0.02}
TONES_R = {440: 0.20, 2000: 0.15, 5000: 0.04, 12000: 0.02}
PILOT_LEVEL = 0.10                     # 10 % de la desviación (7.5 kHz), norma FCC/ITU


def _tones_preemph(spec, t, tau=cfg.DEEMPH_TAU):
    """Suma de tonos con pre-énfasis exacto: H(jw)=1+jw*tau (ganancia y fase por tono).

    Al ser sinusoides puras se aplica analíticamente; evita el filtro inverso del RC
    discreto, que tendría un polo en z=-1 (marginalmente estable).
    """
    x = np.zeros_like(t)
    for f, a in spec.items():
        h = 1 + 1j * 2 * np.pi * f * tau
        x += a * np.abs(h) * np.sin(2 * np.pi * f * t + np.angle(h))
    return x


def expected_mono_amplitudes():
    """Amplitud esperada en el audio mono recibido, (L+R)/2 por tono."""
    freqs = sorted(set(TONES_L) | set(TONES_R))
    return {f: (TONES_L.get(f, 0) + TONES_R.get(f, 0)) / 2 for f in freqs}


def synth_iq(duration=4.0, snr_db=30.0, neighbor_hz=400e3, seed=0):
    """IQ complejo a FS_RF: estación objetivo en 0 Hz (banda base) + vecina en +400 kHz."""
    rng = np.random.default_rng(seed)
    fs = cfg.FS_RF
    t = np.arange(int(duration * fs)) / fs

    L = _tones_preemph(TONES_L, t)
    R = _tones_preemph(TONES_R, t)
    assert max(abs(L).max(), abs(R).max()) < 1.0, "el pre-énfasis satura: bajar amplitudes"

    mpx = (0.45 * (L + R)
           + 0.45 * (L - R) * np.cos(2 * np.pi * 38e3 * t)
           + PILOT_LEVEL * np.cos(2 * np.pi * 19e3 * t))
    # Fase = 2*pi*dev * integral(mpx dt)  ->  f_inst = dev * mpx(t).
    st1 = np.exp(1j * 2 * np.pi * cfg.FM_DEV * np.cumsum(mpx) / fs)

    # Vecina mono con otro programa y misma potencia: caso exigente para el filtro de canal.
    m2 = 0.9 * _tones_preemph({300: 0.3, 3000: 0.3}, t)
    st2 = np.exp(1j * (2 * np.pi * cfg.FM_DEV * np.cumsum(m2) / fs
                       + 2 * np.pi * neighbor_hz * t))

    # AWGN complejo: SNR referida a la potencia de UNA estación (=1) sobre todo fs.
    sigma = np.sqrt(10 ** (-snr_db / 10) / 2)
    noise = sigma * (rng.standard_normal(t.size) + 1j * rng.standard_normal(t.size))
    return (st1 + st2 + noise).astype(np.complex64)


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "synth_fm.cfile"
    synth_iq().tofile(out)          # .cfile: complex64 intercalado I/Q (formato GNU Radio)
    print(f"IQ sintético guardado en {out} (fs={cfg.FS_RF:.0f} Hz, complex64)")
