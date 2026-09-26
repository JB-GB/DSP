# 01 — FM de difusión: modulación, receptor SDR y demodulación

Código asociado: `python/fm_demod.py`, `python/fm_synth.py`, `python/sdr_config.py`, `flowgraphs/fm_rx_*.grc`.

## 1. Modulación FM

Sea $m(t)$ el mensaje normalizado ($|m|\le 1$). La señal FM es

$$s(t)=A\cos\!\big(2\pi f_c t+\phi(t)\big),\qquad \phi(t)=2\pi\,\Delta f\int_0^t m(\tau)\,d\tau$$

La frecuencia instantánea es la derivada de la fase total dividida entre $2\pi$:

$$f_i(t)=\frac{1}{2\pi}\frac{d}{dt}\big(2\pi f_c t+\phi(t)\big)=f_c+\Delta f\,m(t)$$

Por eso $\Delta f$ es la **desviación máxima**: cuando $m=\pm1$, la portadora se desplaza $\pm\Delta f$. En FM comercial $\Delta f=75$ kHz.

### Ancho de banda: regla de Carson
El índice de modulación es $\beta=\Delta f/f_m$. Carson estima que ~98 % de la potencia cae en

$$B_{C}\approx 2(\Delta f+f_m)$$

Con $\Delta f=75$ kHz y $f_m=15$ kHz: $B_C=2(75+15)=180$ kHz, que cabe en el canal de 200 kHz de la banda de 88–108 MHz.

> **Precisión importante:** la desviación **no es lo que limita** el audio a 15 kHz. Es una decisión de diseño de la norma: se elige $f_m=15$ kHz para que Carson ($180$ kHz) quepa en el espaciado de 200 kHz. Si el mensaje fuese más ancho o $\Delta f$ mayor, la señal invadiría canales vecinos. Con el estéreo, el MPX llega a 53 kHz ($B_C=2(75+53)=256$ kHz), pero como la energía a esas frecuencias es pequeña la señal real sigue cabiendo en ~200 kHz.

### Señal compuesta estéreo (MPX)
$$m(t)=\underbrace{\tfrac{L+R}{2}}_{\text{mono, 0–15 kHz}}+\underbrace{0.1\cos(2\pi\,19\text{k}\,t)}_{\text{piloto}}+\underbrace{\tfrac{L-R}{2}\cos(2\pi\,38\text{k}\,t)}_{\text{DSB-SC, 23–53 kHz}}+\text{RDS (57 kHz)}$$

El piloto ocupa el 10 % de la desviación (7.5 kHz). Al ser el 38 kHz exactamente el doble del piloto, el receptor estéreo lo regenera a partir de éste. Un receptor mono simplemente filtra a 15 kHz.

### Pre-énfasis / de-énfasis
El ruido de un discriminador FM crece linealmente con la frecuencia (su PSD $\propto f^2$). El transmisor realza los agudos con $H_{pre}(s)=1+s\tau$ y el receptor los restituye con

$$H_{de}(s)=\frac{1}{1+s\tau},\quad \tau=75\,\mu\text{s (América)},\quad f_c=\frac{1}{2\pi\tau}\approx 2.12\text{ kHz}$$

Discretización (Tustin, $s=2f_s\frac{1-z^{-1}}{1+z^{-1}}$): se implementa con `scipy.signal.bilinear` y es la misma operación que `analog.fm_deemph`.

## 2. Receptor SDR (RTL2832U + tuner)

1. **Antena → LNA → mezclador** (tuner, p. ej. R820T2): convierte la frecuencia de RF a una FI baja.
2. **ADC** de 8 bits (RTL2832U) muestrea la FI a 28.8 MHz.
3. **Conversión digital a banda base (DDC)**: mezcla con un oscilador complejo, filtra y decima, entregando muestras **I/Q** complejas a $f_s\le 2.4$ Msps (estable).
4. **USB → PC**: GNU Radio recibe $x[n]=I[n]+jQ[n]$ centrada en la frecuencia sintonizada.

Muestrear con I/Q permite representar frecuencias positivas y negativas respecto a la portadora, por eso un banda base de ±600 kHz se captura con solo 1.2 Msps.
Un SDR de 12 bits ofrece más rango dinámico (~+24 dB de piso de cuantización teórico frente a 8 bits, $\approx 6.02$ dB/bit), útil cuando hay una estación fuerte cerca de una débil. El proyecto es agnóstico al hardware: solo cambia el perfil en `sdr_config.py`.

## 3. Demodulador de cuadratura (discriminador)

En banda base, la señal FM es $x[n]=A\,e^{j\varphi[n]}$ con $\varphi[n]=\varphi(nT_s)$. Multiplicar por el conjugado de la muestra anterior:

$$x[n]\,x^*[n-1]=A^2 e^{\,j(\varphi[n]-\varphi[n-1])}$$

El ángulo es el incremento de fase en un periodo de muestreo. Como $\varphi'(t)=2\pi\Delta f\,m(t)$,

$$\varphi[n]-\varphi[n-1]\approx 2\pi\,\Delta f\,m[n]\,T_s=\frac{2\pi\,\Delta f\,m[n]}{f_s}$$

Despejando el mensaje:

$$\boxed{m[n]=\frac{f_s}{2\pi\Delta f}\;\arg\!\big(x[n]\,x^*[n-1]\big)}$$

Es exactamente `analog.quadrature_demod_cf(gain = fs/(2πΔf))`. Condición para no tener ambigüedad de fase: $|\Delta\varphi|<\pi\Rightarrow|f_i|<f_s/2$; con $f_s=240$ kHz y $\Delta f=75$ kHz hay margen.

Ventaja: no requiere conocer la fase de la portadora ni un lazo PLL, y es insensible a la amplitud $A$ (el ángulo no depende de $A^2$).

## 4. Cadena implementada y por qué cada parámetro

| Etapa | Parámetro | Justificación |
|---|---|---|
| Fuente | 1.2 Msps | Estable en RTL-SDR; divisible por 5 y por 25 (a 240 k y 48 k) |
| LPF de canal | corte 100 kHz, transición 50 kHz, Kaiser ~60 dB, decim 5 | Deja ±100 kHz (canal de 200 kHz) y rechaza vecinas; el discriminador es no lineal y una vecina fuerte lo perturba |
| Discriminador | ganancia $f_s/(2\pi\Delta f)$ | Normaliza $\Delta f$ a ±1 |
| De-énfasis | 75 µs | Estándar en México/EE. UU. |
| LPF de audio | 15 kHz, transición 4 kHz, decim 5 | Elimina piloto (19 kHz), estéreo y RDS; entrega 48 kHz |

Longitud del FIR de Kaiser: $N\approx\frac{A-7.95}{2.285\,\Delta\omega}$ con $A$ la atenuación en dB y $\Delta\omega=2\pi\,\Delta f_{trans}/f_s$ (implementado por `scipy.signal.kaiserord`).

## 5. Verificación (evidencia)

Se sintetiza una emisora estéreo con tonos conocidos (`fm_synth.py`) más una vecina a +400 kHz y ruido AWGN a 30 dB de SNR, y se demodula.

| Comprobación | Esperado | Medido | Fuente |
|---|---|---|---|
| Piloto en MPX | 0.100 | 0.099 | `results/metrics/fase1_sint_metricas.json` |
| Tonos (L+R)/2, 100 Hz–12 kHz | ver JSON | error ≤ 0.11 dB | idem |
| Residuo de piloto en el audio | — | −109 dBFS | idem |
| GNU Radio vs NumPy | — | correlación 0.99998 | `results/metrics/fase1_validacion_gnuradio_vs_numpy.json` |

> **Limitación:** son señales **sintéticas**. Validan la cadena y el cálculo, pero no sustituyen una captura real (multitrayecto, ruido, desviación real de una emisora). La captura real está pendiente hasta contar con el SDR. También, el "ancho de banda ocupado" y la "desviación pico" de las métricas sintéticas reflejan los tonos de prueba (poca modulación), no los 75 kHz de una emisora real.
