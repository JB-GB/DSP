"""Valida que la cadena de bloques de GNU Radio == la referencia NumPy (fm_demod.py).

Arma sin GUI la misma cadena del flowgraph (file source -> LPF canal -> quad demod ->
de-énfasis -> LPF audio) sobre la señal sintética y compara el audio resultante contra
fm_demod.receive(). Se compara por amplitud de tonos y correlación (los retardos de grupo de
los FIR pueden diferir unas muestras, por eso no se compara muestra a muestra).
Uso (con el Python de radioconda):  python python/validar_flowgraph.py
"""
import json
import math
import tempfile
from pathlib import Path

import numpy as np
from gnuradio import analog, blocks, filter, gr
from gnuradio.fft import window
from gnuradio.filter import firdes
from scipy import signal

import fm_demod
import fm_synth
import sdr_config as cfg

ROOT = Path(__file__).resolve().parents[1]


class FMChain(gr.top_block):
    """Mismos parámetros que flowgraphs/fm_rx_*.grc (generados por make_fm_flowgraphs.py)."""

    def __init__(self, path):
        super().__init__()
        fs, mpx = cfg.FS_RF, cfg.FS_MPX
        src = blocks.file_source(gr.sizeof_gr_complex, path, False)
        chan = filter.fir_filter_ccf(cfg.CHANNEL_DECIM, firdes.low_pass(
            1, fs, cfg.CHANNEL_CUTOFF, cfg.CHANNEL_TRANSITION, window.WIN_KAISER, 6.76))
        demod = analog.quadrature_demod_cf(mpx / (2 * math.pi * cfg.FM_DEV))
        deemph = analog.fm_deemph(mpx, cfg.DEEMPH_TAU)
        alpf = filter.fir_filter_fff(cfg.AUDIO_DECIM, firdes.low_pass(
            1, mpx, cfg.AUDIO_BW, 4e3, window.WIN_KAISER, 6.76))
        self.sink = blocks.vector_sink_f()
        self.connect(src, chan, demod, deemph, alpf, self.sink)


def main():
    iq = fm_synth.synth_iq()
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        p = str(Path(d) / "synth.cfile")
        iq.tofile(p)
        tb = FMChain(p)
        tb.run()                                    # termina solo al agotarse el archivo
        gr_audio = np.array(tb.sink.data())
    _, ref_audio = fm_demod.receive(iq)

    s = int(0.2 * cfg.FS_AUDIO)                      # descarta transitorios
    g, r = gr_audio[s:], ref_audio[s:]
    n = min(len(g), len(r))
    g, r = g[:n], r[:n]
    lag = np.argmax(signal.correlate(g[:20000], r[:20000], mode="full")) - 19999
    rho = np.corrcoef(g[max(lag, 0):n - max(-lag, 0)], r[max(-lag, 0):n - max(lag, 0)])[0, 1]
    exp = fm_synth.expected_mono_amplitudes()
    res = {"retardo_relativo_muestras": int(lag), "correlacion_gnuradio_vs_numpy": round(float(rho), 6),
           "tonos_hz_esperado_gnuradio_numpy": {
               str(f): [round(exp[f], 4),
                        round(fm_demod.tone_amplitude(g, f, cfg.FS_AUDIO) / 0.9, 4),
                        round(fm_demod.tone_amplitude(r, f, cfg.FS_AUDIO) / 0.9, 4)] for f in exp}}
    out = ROOT / "results" / "metrics" / "fase1_validacion_gnuradio_vs_numpy.json"
    out.write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
