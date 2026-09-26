"""Fase 1: genera la evidencia (espectros, waterfall, audio, métricas) de la cadena FM.

Uso:
  python python/fase1_evidencia.py                      # señal sintética (sin dongle)
  python python/fase1_evidencia.py --iq cap.cfile       # captura real (complex64, fs=FS_RF)
Los archivos salen con prefijo 'fase1_sint_' o 'fase1_cap_' para no mezclar origen.
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from scipy.io import wavfile

import fm_demod
import fm_synth
import sdr_config as cfg

ROOT = Path(__file__).resolve().parents[1]
FIG, MET, AUD = (ROOT / "results" / d for d in ("figures", "metrics", "audio_samples"))


def psd_db(x, fs, nperseg, complex_input):
    """PSD de Welch en dB (ventana Hann: lóbulos laterales bajos para ver el piso real)."""
    f, p = signal.welch(x, fs, window="hann", nperseg=nperseg, return_onesided=not complex_input,
                        detrend=False)
    if complex_input:
        f, p = np.fft.fftshift(f), np.fft.fftshift(p)
    return f, 10 * np.log10(p + 1e-20)


def occupied_bw(f, p_lin, frac=0.99):
    """Ancho de banda que contiene 'frac' de la potencia (criterio de ocupación ITU)."""
    c = np.cumsum(p_lin) / p_lin.sum()
    lo, hi = f[np.searchsorted(c, (1 - frac) / 2)], f[np.searchsorted(c, 1 - (1 - frac) / 2)]
    return hi - lo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iq", help="archivo .cfile (complex64) capturado a FS_RF")
    args = ap.parse_args()
    tag = "cap" if args.iq else "sint"
    for d in (FIG, MET, AUD):
        d.mkdir(parents=True, exist_ok=True)

    iq = (np.fromfile(args.iq, dtype=np.complex64) if args.iq else fm_synth.synth_iq())
    print(f"[{tag}] {iq.size} muestras IQ, {iq.size / cfg.FS_RF:.1f} s a {cfg.FS_RF / 1e6} Msps")

    # ---- 1) Espectro de RF y waterfall (antes de demodular) ----
    f, p = psd_db(iq, cfg.FS_RF, 4096, True)
    fig, ax = plt.subplots(2, 1, figsize=(9, 8))
    ax[0].plot(f / 1e3, p)
    ax[0].axvspan(-100, 100, color="tab:green", alpha=0.15, label="canal FM (+-100 kHz)")
    ax[0].set(title="Espectro de RF (banda base, centrado en la estación)",
              xlabel="Frecuencia relativa (kHz)", ylabel="PSD (dB/Hz)")
    ax[0].legend(); ax[0].grid(alpha=0.3)
    fw, tw, sw = signal.spectrogram(iq[:int(cfg.FS_RF * 2)], cfg.FS_RF, nperseg=2048,
                                    return_onesided=False, mode="psd")
    ax[1].pcolormesh(np.fft.fftshift(fw) / 1e3, tw, 10 * np.log10(np.fft.fftshift(sw, axes=0).T + 1e-20),
                     shading="auto")
    ax[1].set(title="Waterfall de RF (2 s)", xlabel="Frecuencia relativa (kHz)", ylabel="Tiempo (s)")
    fig.tight_layout(); fig.savefig(FIG / f"fase1_{tag}_01_rf_waterfall.png", dpi=130); plt.close(fig)

    # ---- 2) Demodulación ----
    mpx, audio = fm_demod.receive(iq)
    skip = int(0.1 * cfg.FS_MPX)                       # descarta el transitorio de los filtros
    mpx_s, aud_s = mpx[skip:], audio[int(0.1 * cfg.FS_AUDIO):]

    # ---- 3) Espectro del MPX: piloto 19 kHz y subportadora estéreo ----
    f, p = psd_db(mpx_s, cfg.FS_MPX, 8192, False)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(f / 1e3, p)
    for x, lab in ((19, "piloto 19 kHz"), (38, "38 kHz (L-R)"), (57, "RDS 57 kHz")):
        ax.axvline(x, color="tab:red", ls="--", alpha=0.6); ax.text(x + 0.5, p.max() - 10, lab, rotation=90, va="top")
    ax.set(title="Espectro de la señal compuesta (MPX) tras el discriminador",
           xlabel="Frecuencia (kHz)", ylabel="PSD (dB/Hz)", xlim=(0, 100))
    ax.grid(alpha=0.3); fig.tight_layout(); fig.savefig(FIG / f"fase1_{tag}_02_mpx.png", dpi=130); plt.close(fig)

    # ---- 4) Espectro del audio demodulado ----
    f, p = psd_db(aud_s, cfg.FS_AUDIO, 8192, False)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(f / 1e3, p); ax.axvline(15, color="tab:red", ls="--", label="15 kHz")
    ax.set(title="Espectro del audio demodulado (48 kHz)", xlabel="Frecuencia (kHz)",
           ylabel="PSD (dB/Hz)"); ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(FIG / f"fase1_{tag}_03_audio.png", dpi=130); plt.close(fig)

    # ---- 5) Audio de muestra (16 bits, normalizado a -1 dBFS) ----
    a = aud_s / (np.abs(aud_s).max() + 1e-12) * 0.89
    wavfile.write(AUD / f"fase1_{tag}_audio_mono.wav", int(cfg.FS_AUDIO), (a * 32767).astype(np.int16))

    # ---- 6) Métricas ----
    fr, pr = signal.welch(iq, cfg.FS_RF, nperseg=4096, return_onesided=False)
    inband = np.abs(fr) <= cfg.CHANNEL_CUTOFF
    metrics = {"origen": tag, "fs_rf_hz": cfg.FS_RF, "fs_audio_hz": cfg.FS_AUDIO,
               "ancho_banda_ocupado_99pct_canal_kHz":
                   round(occupied_bw(np.sort(fr[inband]), pr[inband][np.argsort(fr[inband])]) / 1e3, 1),
               "desviacion_pico_medida_kHz": round(float(np.percentile(np.abs(mpx_s), 99.9)) * cfg.FM_DEV / 1e3, 1),
               "piloto_19k_nivel_relativo": round(float(fm_demod.tone_amplitude(mpx_s, 19e3, cfg.FS_MPX)), 4)}
    if tag == "sint":
        exp = fm_synth.expected_mono_amplitudes()
        # Recuperado = (L+R)/2 x 0.9 (el MPX lleva 0.45*(L+R)); se re-normaliza por 1/0.9.
        rec = {f: float(fm_demod.tone_amplitude(aud_s, f, cfg.FS_AUDIO)) / 0.9 for f in exp}
        metrics["piloto_esperado"] = fm_synth.PILOT_LEVEL
        metrics["tonos_hz_esperado_medido_error_dB"] = {
            str(f): [round(exp[f], 4), round(rec[f], 4), round(20 * np.log10(rec[f] / exp[f]), 2)]
            for f in exp}
        # Residuo de piloto en el audio (debe estar muy por debajo del programa).
        # (19 kHz < Nyquist de 24 kHz, así que si el LPF fallara aparecería aquí.)
        metrics["piloto_residual_en_audio_dBFS"] = round(
            20 * np.log10(fm_demod.tone_amplitude(aud_s, 19e3, cfg.FS_AUDIO) + 1e-12), 1)
    (MET / f"fase1_{tag}_metricas.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False),
                                                     encoding="utf-8")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
