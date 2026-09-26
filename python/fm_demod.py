"""Cadena de recepción FM de difusión en NumPy/SciPy (réplica de la del flowgraph).

Se mantiene equivalente a los bloques de GNU Radio para poder validar el flowgraph
comparando contra esta referencia. Teoría en theory/01_fm_demod.md.
"""
import numpy as np
from scipy import signal

import sdr_config as cfg


def channel_filter(iq, fs=cfg.FS_RF, decim=cfg.CHANNEL_DECIM,
                   cutoff=cfg.CHANNEL_CUTOFF, transition=cfg.CHANNEL_TRANSITION):
    """Pasa-bajos complejo + decimación: aísla el canal FM de 200 kHz.

    Kaiser con atenuación ~60 dB: rechaza estaciones adyacentes (a >=200 kHz) antes de
    demodular; el discriminador es no lineal y un vecino fuerte lo 'captura'.
    """
    numtaps, beta = signal.kaiserord(60.0, transition / (fs / 2))
    numtaps |= 1                                   # impar -> fase lineal tipo I
    taps = signal.firwin(numtaps, cutoff, window=("kaiser", beta), fs=fs)
    # upfirdn = filtrado polifásico: solo calcula las muestras que se conservan.
    return signal.upfirdn(taps, iq, up=1, down=decim)


def quadrature_demod(iq, fs=cfg.FS_MPX, dev=cfg.FM_DEV):
    """Discriminador de cuadratura: m[n] = angle(x[n] * conj(x[n-1])) * fs / (2*pi*dev).

    Si x[n]=exp(j*phi[n]), x[n]*conj(x[n-1]) = exp(j*(phi[n]-phi[n-1])) y el ángulo es el
    incremento de fase = 2*pi*f_inst/fs. Multiplicar por fs/(2*pi*dev) normaliza a +-1
    cuando la desviación es la máxima (igual que analog.quadrature_demod_cf de GNU Radio).
    """
    d = iq[1:] * np.conj(iq[:-1])
    m = np.angle(d) * fs / (2 * np.pi * dev)
    return np.concatenate(([0.0], m))


def deemphasis(x, fs=cfg.FS_MPX, tau=cfg.DEEMPH_TAU):
    """De-énfasis RC de 75 us: H(s)=1/(1+s*tau), discretizado con Tustin (bilineal)."""
    b, a = signal.bilinear([1.0], [tau, 1.0], fs)
    return signal.lfilter(b, a, x)


def audio_lowpass_decimate(x, fs=cfg.FS_MPX, decim=cfg.AUDIO_DECIM, cutoff=cfg.AUDIO_BW):
    """Pasa-bajos de 15 kHz + decimación a 48 kHz.

    Elimina el piloto de 19 kHz, la subportadora estéreo (23-53 kHz) y RDS (57 kHz) del
    MPX. Transición de 4 kHz (15 -> 19 kHz): lo justo para no dejar pasar el piloto.
    """
    numtaps, beta = signal.kaiserord(60.0, 4e3 / (fs / 2))
    numtaps |= 1
    taps = signal.firwin(numtaps, cutoff, window=("kaiser", beta), fs=fs)
    return signal.upfirdn(taps, x, up=1, down=decim)


def receive(iq, fs_rf=cfg.FS_RF):
    """IQ de RF (centrado en la estación) -> (MPX a 240 kHz, audio mono a 48 kHz)."""
    bb = channel_filter(iq, fs_rf)
    mpx = quadrature_demod(bb)
    audio = audio_lowpass_decimate(deemphasis(mpx))
    return mpx, audio


def tone_amplitude(x, f, fs):
    """Amplitud de la componente en f: A = 2*|mean(x[n]*exp(-j*2*pi*f*n/fs))|.

    Proyección sobre una exponencial (un solo coeficiente de la DFT); precisa cuando la
    ventana contiene muchos ciclos del tono.
    """
    n = np.arange(len(x))
    return 2 * np.abs(np.mean(x * np.exp(-2j * np.pi * f * n / fs)))
