"""Genera flowgraphs/fm_rx_sdr.grc y flowgraphs/fm_rx_archivo.grc.

Ambos comparten TODO el procesamiento (canal -> discriminador -> de-énfasis -> audio) y solo
difieren en la fuente, así que se generan desde una plantilla para no duplicar a mano.
Los .grc resultantes se pueden abrir y editar libremente en GNU Radio Companion.
Uso:  python python/make_fm_flowgraphs.py
"""
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "flowgraphs"

HEADER = """options:
  parameters:
    author: ''
    catch_exceptions: 'True'
    category: '[GRC Hier Blocks]'
    cmake_opt: ''
    comment: ''
    copyright: ''
    description: ''
    gen_cmake: 'On'
    gen_linking: dynamic
    generate_options: qt_gui
    hier_block_src_path: '.:'
    id: {fid}
    max_nouts: '0'
    output_language: python
    placement: (0,0)
    qt_qss_theme: ''
    realtime_scheduling: ''
    run: 'True'
    run_command: '{{python}} -u {{filename}}'
    run_options: prompt
    sizing_mode: fixed
    thread_safe_setters: ''
    title: {title}
    window_size: (1200,900)
  states: {{bus_sink: false, bus_source: false, bus_structure: null, coordinate: [8, 8], rotation: 0, state: enabled}}

blocks:
"""


def block(name, bid, params, xy):
    """Serializa un bloque GRC (YAML) con parámetros dados como dict."""
    p = "\n".join(f"    {k}: {v}" for k, v in params.items())
    return (f"- name: {name}\n  id: {bid}\n  parameters:\n{p}\n"
            f"  states: {{coordinate: [{xy[0]}, {xy[1]}], rotation: 0, state: enabled}}\n")


def variables():
    v = ""
    v += block("samp_rate", "variable", {"comment": "'fs de RF; 1.2 Msps es estable en RTL-SDR y divisible a 240k/48k'", "value": "'1200000'"}, (200, 12))
    v += block("mpx_rate", "variable", {"comment": "'fs tras decimar el canal (samp_rate/5)'", "value": "samp_rate//5"}, (320, 12))
    v += block("audio_rate", "variable", {"comment": "''", "value": "'48000'"}, (440, 12))
    v += block("fm_dev", "variable", {"comment": "'desviacion maxima FM comercial (Hz)'", "value": "'75000'"}, (560, 12))
    v += block("import_math", "import", {"alias": "''", "comment": "''", "imports": "import math"}, (680, 12))
    for name, label, lo, hi, step, val in (("center_freq", "Frecuencia central (Hz)", 88e6, 108e6, 1e5, 89.7e6),
                                           ("rf_gain", "Ganancia RF (dB)", 0, 50, 1, 30)):
        v += block(name, "variable_qtgui_range",
                   {"comment": "''", "gui_hint": "''", "label": label, "min_len": "'200'",
                    "orient": "QtCore.Qt.Horizontal", "rangeType": "float", "start": f"'{lo:.0f}'",
                    "step": f"'{step:.0f}'", "stop": f"'{hi:.0f}'", "value": f"'{val:.0f}'",
                    "widget": "counter_slider"}, (800, 12))
    return v


def processing():
    b = ""
    b += block("channel_lpf", "low_pass_filter", {
        "beta": "'6.76'", "comment": "'Aisla el canal FM de 200 kHz: corte 100k, transicion 50k (Kaiser). Decim 5'",
        "cutoff_freq": "'100000'", "decim": "'5'", "gain": "'1'", "interp": "'1'",
        "samp_rate": "samp_rate", "type": "fir_filter_ccf", "width": "'50000'", "win": "window.WIN_KAISER"}, (420, 260))
    b += block("quad_demod", "analog_quadrature_demod_cf", {
        "comment": "'gain = fs/(2*pi*dev): normaliza la desviacion maxima a +-1'",
        "gain": "mpx_rate/(2*math.pi*fm_dev)"}, (640, 260))
    b += block("deemph", "analog_fm_deemph", {
        "comment": "'De-enfasis 75 us (America)'", "samp_rate": "mpx_rate", "tau": "75e-6"}, (860, 260))
    b += block("audio_lpf", "low_pass_filter", {
        "beta": "'6.76'", "comment": "'Audio 15 kHz; transicion 4 kHz rechaza el piloto de 19 kHz. Decim 5 -> 48 kHz'",
        "cutoff_freq": "'15000'", "decim": "'5'", "gain": "'1'", "interp": "'1'",
        "samp_rate": "mpx_rate", "type": "fir_filter_fff", "width": "'4000'", "win": "window.WIN_KAISER"}, (1060, 260))
    b += block("audio_out", "audio_sink", {"comment": "''", "device_name": "''", "num_inputs": "'1'",
                                           "ok_to_block": "'True'", "samp_rate": "audio_rate"}, (1260, 240))
    b += block("audio_file", "blocks_wavfile_sink", {
        "comment": "'Muestra de audio para results/audio_samples'", "file": "audio_mono_48k.wav", "nchan": "'1'",
        "samp_rate": "audio_rate", "type": "float", "format": "FORMAT_WAV", "subformat": "FORMAT_PCM_16",
        "append": "'False'", "bits_per_sample1": "FORMAT_PCM_16"}, (1260, 340))
    b += block("mpx_sink", "blocks_file_sink", {
        "append": "'False'", "comment": "'MPX crudo a 240 kHz (piloto, L-R, RDS) para analisis en Python'",
        "file": "mpx_240k.f32", "type": "float", "unbuffered": "'False'", "vlen": "'1'"}, (860, 380))
    for name, bw, ty, fft, title, cmt, xy in (
            ("rf_spectrum", "samp_rate", "complex", "4096", "Espectro RF", "Espectro de RF antes de demodular", (420, 400)),
            ("mpx_spectrum", "mpx_rate", "float", "4096", "Espectro MPX", "Aqui se ve el piloto de 19 kHz", (860, 520)),
            ("audio_spectrum", "audio_rate", "float", "2048", "Espectro audio", "Audio demodulado (contenido hasta 15 kHz)", (1260, 440))):
        b += block(name, "qtgui_freq_sink_x", {
            "bw": bw, "comment": f"'{cmt}'", "fc": "'0'", "fftsize": f"'{fft}'", "gui_hint": "''",
            "name": f"'\"{title}\"'", "nconnections": "'1'", "showports": "'False'", "type": ty,
            "wintype": "window.WIN_BLACKMAN_hARRIS"}, xy)
    b += block("rf_waterfall", "qtgui_waterfall_sink_x", {
        "bw": "samp_rate", "comment": "'Waterfall de RF'", "fc": "'0'", "fftsize": "'1024'", "gui_hint": "''",
        "name": "'\"Waterfall RF\"'", "nconnections": "'1'", "showports": "'False'", "type": "complex",
        "wintype": "window.WIN_BLACKMAN_hARRIS"}, (420, 520))
    return b


SRC_SDR = block("src", "osmosdr_source", {
    "args": "'\"rtl=0\"'", "comment": "'RTL-SDR. Para otro SDR: Soapy Source o cambiar args (ver environment.md)'",
    "freq0": "center_freq", "gain0": "rf_gain", "if_gain0": "'20'", "bb_gain0": "'20'",
    "sample_rate": "samp_rate", "type": "fc32", "nchan": "'1'", "corr0": "'0'", "dc_offset_mode0": "'0'",
    "iq_balance_mode0": "'0'", "bw0": "'0'", "ant0": "''"}, (180, 200))

SRC_FILE = block("src", "blocks_file_source", {
    "comment": "'Reproduce una captura .cfile (p. ej. la sintetica de fm_synth.py) sin hardware'",
    "file": "synth_fm.cfile", "length": "'0'", "offset": "'0'", "repeat": "'True'", "type": "complex", "vlen": "'1'"}, (180, 200)) \
    + block("throttle", "blocks_throttle", {
        "comment": "'Sin hardware no hay reloj: el throttle impone samp_rate'", "ignoretag": "'True'",
        "samples_per_second": "samp_rate", "type": "complex", "vlen": "'1'"}, (180, 300))

TAIL = [("channel_lpf", "quad_demod"), ("quad_demod", "mpx_sink"), ("quad_demod", "mpx_spectrum"),
        ("quad_demod", "deemph"), ("deemph", "audio_lpf"), ("audio_lpf", "audio_out"),
        ("audio_lpf", "audio_file"), ("audio_lpf", "audio_spectrum")]


def conns(head_src):
    pairs = [("src", "throttle")] if head_src == "throttle" else []
    pairs += [(head_src, d) for d in ("channel_lpf", "rf_spectrum", "rf_waterfall")] + TAIL
    return "\nconnections:\n" + "".join(f"- [{a}, '0', {b}, '0']\n" for a, b in pairs) \
        + "\nmetadata:\n  file_format: 1\n"


def write(fid, title, src_blocks, head_src):
    text = HEADER.format(fid=fid, title=title) + variables() + src_blocks + processing() + conns(head_src)
    (OUT / f"{fid}.grc").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    write("fm_rx_sdr", "FM RX SDR", SRC_SDR, "src")
    write("fm_rx_archivo", "FM RX archivo IQ", SRC_FILE, "throttle")
    print("Generados:", *(p.name for p in OUT.glob("*.grc")))
