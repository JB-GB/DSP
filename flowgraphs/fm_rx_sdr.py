#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: FM RX SDR
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from gnuradio import analog
import math
from gnuradio import audio
from gnuradio import blocks
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import osmosdr
import time
import sip
import threading



class fm_rx_sdr(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "FM RX SDR", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("FM RX SDR")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "fm_rx_sdr")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 1200000
        self.rf_gain = rf_gain = 30
        self.mpx_rate = mpx_rate = samp_rate//5
        self.fm_dev = fm_dev = 75000
        self.center_freq = center_freq = 89700000
        self.audio_rate = audio_rate = 48000

        ##################################################
        # Blocks
        ##################################################

        self._rf_gain_range = qtgui.Range(0, 50, 1, 30, 200)
        self._rf_gain_win = qtgui.RangeWidget(self._rf_gain_range, self.set_rf_gain, "Ganancia RF (dB)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._rf_gain_win)
        self._center_freq_range = qtgui.Range(88000000, 108000000, 100000, 89700000, 200)
        self._center_freq_win = qtgui.RangeWidget(self._center_freq_range, self.set_center_freq, "Frecuencia central (Hz)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._center_freq_win)
        self.src = osmosdr.source(
            args="numchan=" + str(1) + " " + "rtl=0"
        )
        self.src.set_time_unknown_pps(osmosdr.time_spec_t())
        self.src.set_sample_rate(samp_rate)
        self.src.set_center_freq(center_freq, 0)
        self.src.set_freq_corr(0, 0)
        self.src.set_dc_offset_mode(0, 0)
        self.src.set_iq_balance_mode(0, 0)
        self.src.set_gain_mode(False, 0)
        self.src.set_gain(rf_gain, 0)
        self.src.set_if_gain(20, 0)
        self.src.set_bb_gain(20, 0)
        self.src.set_antenna('', 0)
        self.src.set_bandwidth(0, 0)
        self.rf_waterfall = qtgui.waterfall_sink_c(
            1024, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate, #bw
            "Waterfall RF", #name
            1, #number of inputs
            None # parent
        )
        self.rf_waterfall.set_update_time(0.10)
        self.rf_waterfall.enable_grid(False)
        self.rf_waterfall.enable_axis_labels(True)



        labels = ['', '', '', '', '',
                  '', '', '', '', '']
        colors = [0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.rf_waterfall.set_line_label(i, "Data {0}".format(i))
            else:
                self.rf_waterfall.set_line_label(i, labels[i])
            self.rf_waterfall.set_color_map(i, colors[i])
            self.rf_waterfall.set_line_alpha(i, alphas[i])

        self.rf_waterfall.set_intensity_range(-140, 10)

        self._rf_waterfall_win = sip.wrapinstance(self.rf_waterfall.qwidget(), Qt.QWidget)

        self.top_layout.addWidget(self._rf_waterfall_win)
        self.rf_spectrum = qtgui.freq_sink_c(
            4096, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate, #bw
            "Espectro RF", #name
            1,
            None # parent
        )
        self.rf_spectrum.set_update_time(0.10)
        self.rf_spectrum.set_y_axis((-140), 10)
        self.rf_spectrum.set_y_label('Relative Gain', 'dB')
        self.rf_spectrum.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.rf_spectrum.enable_autoscale(False)
        self.rf_spectrum.enable_grid(False)
        self.rf_spectrum.set_fft_average(1.0)
        self.rf_spectrum.enable_axis_labels(True)
        self.rf_spectrum.enable_control_panel(False)
        self.rf_spectrum.set_fft_window_normalized(False)



        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.rf_spectrum.set_line_label(i, "Data {0}".format(i))
            else:
                self.rf_spectrum.set_line_label(i, labels[i])
            self.rf_spectrum.set_line_width(i, widths[i])
            self.rf_spectrum.set_line_color(i, colors[i])
            self.rf_spectrum.set_line_alpha(i, alphas[i])

        self._rf_spectrum_win = sip.wrapinstance(self.rf_spectrum.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._rf_spectrum_win)
        self.quad_demod = analog.quadrature_demod_cf((mpx_rate/(2*math.pi*fm_dev)))
        self.mpx_spectrum = qtgui.freq_sink_f(
            4096, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            mpx_rate, #bw
            "Espectro MPX", #name
            1,
            None # parent
        )
        self.mpx_spectrum.set_update_time(0.10)
        self.mpx_spectrum.set_y_axis((-140), 10)
        self.mpx_spectrum.set_y_label('Relative Gain', 'dB')
        self.mpx_spectrum.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.mpx_spectrum.enable_autoscale(False)
        self.mpx_spectrum.enable_grid(False)
        self.mpx_spectrum.set_fft_average(1.0)
        self.mpx_spectrum.enable_axis_labels(True)
        self.mpx_spectrum.enable_control_panel(False)
        self.mpx_spectrum.set_fft_window_normalized(False)


        self.mpx_spectrum.set_plot_pos_half(not True)

        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.mpx_spectrum.set_line_label(i, "Data {0}".format(i))
            else:
                self.mpx_spectrum.set_line_label(i, labels[i])
            self.mpx_spectrum.set_line_width(i, widths[i])
            self.mpx_spectrum.set_line_color(i, colors[i])
            self.mpx_spectrum.set_line_alpha(i, alphas[i])

        self._mpx_spectrum_win = sip.wrapinstance(self.mpx_spectrum.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._mpx_spectrum_win)
        self.mpx_sink = blocks.file_sink(gr.sizeof_float*1, 'mpx_240k.f32', False)
        self.mpx_sink.set_unbuffered(False)
        self.deemph = analog.fm_deemph(fs=mpx_rate, tau=(75e-6))
        self.channel_lpf = filter.fir_filter_ccf(
            5,
            firdes.low_pass(
                1,
                samp_rate,
                100000,
                50000,
                window.WIN_KAISER,
                6.76))
        self.audio_spectrum = qtgui.freq_sink_f(
            2048, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            audio_rate, #bw
            "Espectro audio", #name
            1,
            None # parent
        )
        self.audio_spectrum.set_update_time(0.10)
        self.audio_spectrum.set_y_axis((-140), 10)
        self.audio_spectrum.set_y_label('Relative Gain', 'dB')
        self.audio_spectrum.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.audio_spectrum.enable_autoscale(False)
        self.audio_spectrum.enable_grid(False)
        self.audio_spectrum.set_fft_average(1.0)
        self.audio_spectrum.enable_axis_labels(True)
        self.audio_spectrum.enable_control_panel(False)
        self.audio_spectrum.set_fft_window_normalized(False)


        self.audio_spectrum.set_plot_pos_half(not True)

        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.audio_spectrum.set_line_label(i, "Data {0}".format(i))
            else:
                self.audio_spectrum.set_line_label(i, labels[i])
            self.audio_spectrum.set_line_width(i, widths[i])
            self.audio_spectrum.set_line_color(i, colors[i])
            self.audio_spectrum.set_line_alpha(i, alphas[i])

        self._audio_spectrum_win = sip.wrapinstance(self.audio_spectrum.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._audio_spectrum_win)
        self.audio_out = audio.sink(audio_rate, '', True)
        self.audio_lpf = filter.fir_filter_fff(
            5,
            firdes.low_pass(
                1,
                mpx_rate,
                15000,
                4000,
                window.WIN_KAISER,
                6.76))
        self.audio_file = blocks.wavfile_sink(
            'audio_mono_48k.wav',
            1,
            audio_rate,
            blocks.FORMAT_WAV,
            blocks.FORMAT_PCM_16,
            False
            )


        ##################################################
        # Connections
        ##################################################
        self.connect((self.audio_lpf, 0), (self.audio_file, 0))
        self.connect((self.audio_lpf, 0), (self.audio_out, 0))
        self.connect((self.audio_lpf, 0), (self.audio_spectrum, 0))
        self.connect((self.channel_lpf, 0), (self.quad_demod, 0))
        self.connect((self.deemph, 0), (self.audio_lpf, 0))
        self.connect((self.quad_demod, 0), (self.deemph, 0))
        self.connect((self.quad_demod, 0), (self.mpx_sink, 0))
        self.connect((self.quad_demod, 0), (self.mpx_spectrum, 0))
        self.connect((self.src, 0), (self.channel_lpf, 0))
        self.connect((self.src, 0), (self.rf_spectrum, 0))
        self.connect((self.src, 0), (self.rf_waterfall, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "fm_rx_sdr")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_mpx_rate(self.samp_rate//5)
        self.src.set_sample_rate(self.samp_rate)
        self.channel_lpf.set_taps(firdes.low_pass(1, self.samp_rate, 100000, 50000, window.WIN_KAISER, 6.76))
        self.rf_spectrum.set_frequency_range(0, self.samp_rate)
        self.rf_waterfall.set_frequency_range(0, self.samp_rate)

    def get_rf_gain(self):
        return self.rf_gain

    def set_rf_gain(self, rf_gain):
        self.rf_gain = rf_gain
        self.src.set_gain(self.rf_gain, 0)

    def get_mpx_rate(self):
        return self.mpx_rate

    def set_mpx_rate(self, mpx_rate):
        self.mpx_rate = mpx_rate
        self.quad_demod.set_gain((self.mpx_rate/(2*math.pi*self.fm_dev)))
        self.audio_lpf.set_taps(firdes.low_pass(1, self.mpx_rate, 15000, 4000, window.WIN_KAISER, 6.76))
        self.mpx_spectrum.set_frequency_range(0, self.mpx_rate)

    def get_fm_dev(self):
        return self.fm_dev

    def set_fm_dev(self, fm_dev):
        self.fm_dev = fm_dev
        self.quad_demod.set_gain((self.mpx_rate/(2*math.pi*self.fm_dev)))

    def get_center_freq(self):
        return self.center_freq

    def set_center_freq(self, center_freq):
        self.center_freq = center_freq
        self.src.set_center_freq(self.center_freq, 0)

    def get_audio_rate(self):
        return self.audio_rate

    def set_audio_rate(self, audio_rate):
        self.audio_rate = audio_rate
        self.audio_spectrum.set_frequency_range(0, self.audio_rate)




def main(top_block_cls=fm_rx_sdr, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()
    tb.flowgraph_started.set()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
