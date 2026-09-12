# Branch Education Acoustic Physics & Superposition Blueprint

> **Reference**: [Branch Education: How Do Noise Canceling Headphones Work?](https://youtu.be/VIi04uD8LtY)  
> **Target Hardware**: boAt Rockerz 411 (40mm Drivers, On-Ear Cushion Seal)  
> **System Architecture**: Anush X HRL Active Noise Cancellation Engine  

---

## 1. Physics of Sound: Compressions & Rarefactions

Sound traveling through air is not a transverse wave like ripples on water; it is a **longitudinal pressure wave** composed of vibrating air molecules ($N_2, O_2, CO_2$):

```
                        [ SOUND SOURCE: FAN / SPEAKER CONE ]
                                         |
                                         v
   +---+       +---+       +---+       +---+       +---+       +---+
   | : |       |   |       | : |       |   |       | : |       |   |
   | : |       |   |       | : |       |   |       | : |       |   |
   | : |       |   |       | : |       |   |       | : |       |   |
   +---+       +---+       +---+       +---+       +---+       +---+
Compression  Rarefaction Compression Rarefaction Compression Rarefaction
   (+P)        (-P)        (+P)        (-P)        (+P)        (-P)
```

- **Compression ($+P$)**: Air molecules are pushed together, creating a localized pocket of high pressure relative to ambient atmospheric equilibrium ($P_0 = 101,325\text{ Pa}$). When a compression hits the eardrum, it pushes the tympanic membrane inward.
- **Rarefaction ($-P$)**: As the sound source pulls back, air molecules spread apart, creating a localized low-pressure trough. When a rarefaction hits the eardrum, it pulls the tympanic membrane outward.
- **Continuous Oscillations**: The rapid alternating arrival of compressions and rarefactions vibrates the middle ear ossicles (malleus, incus, stapes), sending auditory impulses to the brainstem.

---

## 2. Destructive Interference: The Zero-Pressure Collision

Active Noise Cancellation does not "absorb" sound; it uses the principle of **wave superposition** to create an intentional counter-wave of inverted pressure:

$$\Delta P_{\text{net}}(x, t) = \Delta P_{\text{noise}}(x, t) + \Delta P_{\text{anti}}(x, t)$$

$$\Delta P_{\text{net}}(x, t) = (+P) + (-P) = 0\text{ Pa}$$

When the incoming external noise produces a **compression** (+P), the headphone speaker diaphragm retracts rapidly, generating a **rarefaction** (-P) in the ear canal at the exact same instant. The air molecules find perfect equilibrium: net pressure deviation becomes **zero**, the eardrum remains stationary, and the user perceives complete silence.

---

## 3. The Frequency vs Wavelength Ceiling ($\lambda = c / f$)

Why can headphones easily eliminate a $100\text{ Hz}$ room fan or airplane drone, but struggle with high-pitched clicks or clatter?

### The Acoustic Wavelength Equation:
$$\lambda = \frac{c}{f} \quad \text{where } c = 343.0\text{ m/s (speed of sound in room air)}$$

| Frequency ($f$) | Acoustic Wavelength ($\lambda$) | Half-Wavelength ($\lambda / 2$) | Spatial Tolerance Margin |
|---|---|---|---|
| **60 Hz** (AC mains hum) | **5.72 meters** (572 cm) | 2.86 meters | Extremely forgiving (>100 ms margin) |
| **120 Hz** (Room fan blade pass) | **2.86 meters** (286 cm) | 1.43 meters | High tolerance (>50 ms margin) |
| **250 Hz** (Traffic rumble) | **1.37 meters** (137 cm) | 68.6 cm | Broad tolerance |
| **1,000 Hz** (Low speech vowel) | **34.3 cm** | 17.1 cm | Tight tolerance (~170 μs margin) |
| **3,000 Hz** (Speech sibilance) | **11.4 cm** | 5.7 cm | Sub-millimeter timing required |
| **10,000 Hz** (High-frequency hiss) | **3.43 cm** | 1.7 cm | Wavelength is smaller than ear cushion |

### The Critical Constructive Amplification Danger:
If an anti-noise wave is delayed by time $\Delta t$, it incurs a phase error:
$$\Delta \theta = 2\pi f \Delta t$$

The net acoustic power ratio at the eardrum is:
$$P_{\text{ratio}} = |1 - e^{j \Delta \theta}|^2 = 4 \sin^2\left(\frac{\Delta \theta}{2}\right)$$

- When $\Delta \theta = 0$: $P_{\text{ratio}} = 0$ ($-\infty\text{ dB}$, complete destructive cancellation).
- When $\Delta \theta = 60^\circ$ ($\frac{\pi}{3}$): $P_{\text{ratio}} = 1.0$ ($0\text{ dB}$, break-even point).
- When $\Delta \theta > 60^\circ$: $P_{\text{ratio}} > 1.0$ (**Constructive amplification**). At $\Delta \theta = 180^\circ$, $P_{\text{ratio}} = 4.0$ (**$+6\text{ dB}$, sound volume doubles!**).

### The boAt Rockerz 411 Acoustic Boundary:
The physical distance from the external stem mic to the 40mm driver is $4.5\text{ cm}$, producing an acoustic propagation delay of:
$$\tau = \frac{0.045\text{ m}}{343\text{ m/s}} \approx 131.2\ \mu\text{s}$$

Setting the maximum safe phase error to $\Delta \theta = 60^\circ$:
$$f_{\text{crit}} = \frac{\pi / 3}{2\pi \cdot 131.2 \times 10^{-6}} \approx 1,270.3\text{ Hz}$$

**Engineering Rule implemented in Anush X HRL**:
Active anti-phase cancellation is hard-limited to frequencies below $1,200\text{ Hz}$ via the `anti_constructive_filter`. For frequencies above $1,200\text{ Hz}$, the system transitions to **passive acoustic damping** (the thick foam on-ear ear cushions of the boAt Rockerz 411 absorb short wavelengths as heat), completely eliminating constructive hiss or noise doubling!

---

## 4. The Superposition Principle: Playing Music During Cancellation

A common paradox: *If headphones cancel sound waves, why don't they cancel the music you are listening to?*

As demonstrated in Branch Education's blueprint, the headphone DSP leverages **Linear Acoustic Superposition**:

```
                       [ Desired Music Track: s_music(t) ]
                                      |
                                      v
                                    +---+
  [ Ambient Noise: x_noise(t) ] --->| + |  (Digital Summation in DSP)
                                    +---+
                                      |
                                      v
     [ Speaker Driver Output: s_speaker(t) = s_music(t) - x_noise(t) ]
                                      |
                                      v  (Acoustic waves emitted into ear canal)
     ==================== PHYSICAL EAR CANAL AIR ====================
                                      |
                                      v
     [ Net Ear Pressure: p_ear(t) = s_speaker(t) + x_ambient(t) ]
                                  = [s_music(t) - x_noise(t)] + x_noise(t)
                                  = s_music(t)
                                      |
                                      v
                       [ Human Eardrum (Tympanic Membrane) ]
                          Pristine Music, Zero Room Noise!
```

Because acoustic air and the dynamic speaker driver operate in a linear regime:
1. The driver produces a composite wave: $s_{\text{speaker}} = s_{\text{music}} + (-x_{\text{noise}})$.
2. The physical ambient room noise $x_{\text{noise}}$ leaks into the ear canal.
3. In the air volume inside the headphone cushion, $-x_{\text{noise}}$ and $+x_{\text{noise}}$ collide and cancel to 0 Pa.
4. The remaining air movement consists exclusively of $s_{\text{music}}$, which reaches the eardrum with $>60\text{ dB}$ SNR fidelity.

---

## 5. Summary of Branch Education Integration in Anush X HRL

| Module | Location | Function |
|---|---|---|
| `BranchAcousticPhysics` | [`hrl_noise_cancellation/dsp/branch_physics.py`](file:///Users/pavankumars/.gemini/antigravity/scratch/hrl-x-noise-cancellation/hrl_noise_cancellation/dsp/branch_physics.py) | Mathematical engine for wavelength, phase error, coherence boundaries, and linear superposition. |
| `anti_constructive_filter` | [`hrl_noise_cancellation/dsp/branch_physics.py`](file:///Users/pavankumars/.gemini/antigravity/scratch/hrl-x-noise-cancellation/hrl_noise_cancellation/dsp/branch_physics.py) | 2nd-order biquad cutoff preventing high-frequency phase flipping. |
| `blueprint` CLI command | [`hrl_noise_cancellation/cli.py`](file:///Users/pavankumars/.gemini/antigravity/scratch/hrl-x-noise-cancellation/hrl_noise_cancellation/cli.py) | Interactive terminal report displaying acoustic wavelengths, constructive limits, and superposition verification. |
| Air Molecule Visualizer | [`web/index.html`](file:///Users/pavankumars/.gemini/antigravity/scratch/hrl-x-noise-cancellation/web/index.html) | Real-time particle simulation showing air molecule compressions (+P) meeting driver rarefactions (-P) in physical space. |
