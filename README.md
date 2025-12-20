# 3xOSC Module Synth - ssynth

**ssynth** is a real‑time, polyphonic 3‑oscillator wavetable synthesizer.
It combines a C++17 DSP core (exposed to Python via `pybind11`) with a PyQt6/OpenGL GUI, real‑time audio streaming, and an interactive spectrogram.

## Content

- [Architecture](#architecture-description)
- [Modules](#modules)
- [Dependencies](#dependencies)
- [Build](#build)
- [Run](#run)
- [Usage](#usage)
- [Key technologies](#key-technologies)
- [TODO](#todo)
- [License](#license)
- [Contacts](#contacts)

## Architecture description

```txt
ssynth/
├── CMakeLists.txt
├── bindings
│   └── main_bindings.cpp
├── build.sh
├── engine
│   ├── include
│   │   ├── audiobuffer.h
│   │   ├── defs.h
│   │   ├── engine.h
│   │   ├── envelope.h
│   │   ├── filter.h
│   │   ├── osc.h
│   │   ├── utils.h
│   │   ├── voice.h
│   │   └── wavetable.h
│   └── src
│       ├── engine.cpp
│       ├── low_and_high_filter.cpp
│       ├── voice.cpp
│       └── wavetable.cpp
├── frontend
│   ├── assets
│   │   ├── background
│   │   ├── button
│   │   └── knob
│   ├── gui
│   │   ├── adsr.py
│   │   ├── button.py
│   │   ├── knob.py
│   │   ├── main_gui.py
│   │   ├── osc_panel.py
│   │   ├── visual
│   │   │   ├── spectrogram
│   │   │   │   ├── spectrogram_frame.py
│   │   │   │   └── spectrogram_widget.py
│   │   │   └── visualizer.py
│   │   └── window_gui.py
│   └── utils
│       └── logger.py
├── main.py
├── tables
│   ├── saw.wvt
│   ├── sine.wvt
│   ├── square.wvt
│   └── triangle.wvt
├── tools
│   └── wavemanager.py
├── tree.txt
└── user
    ├── default.json
    ├── new.json
    └── release.json

17 directories, 36 files
```

## Modules

High‑level modules and their responsibilities:

- `engine/` (C++ DSP core)
  - Implements the real‑time synthesis engine in modern C++17.
  - `SynthEngine` (`engine.h` / `engine.cpp`): manages polyphony, voices, global parameters, and renders stereo buffers.
  - `Voice` (`voice.h` / `voice.cpp`): single polyphonic voice with three oscillators, ADSR envelope, gain and pan.
  - `WavetableManager` (`wavetable.h` / `wavetable.cpp`): loads multi‑MIP wavetables from `.wvt` files and renders band‑limited waveforms.
  - `Envelope` (`envelope.h`): ADSR envelope generator with optional auto‑release.
  - `Oscillator` (`osc.h`): wavetable oscillator which mixes selected table into a mono buffer.
  - `RingBuffer` and helpers (`utils.h`, `audiobuffer.h`): lock‑free buffer used to feed FFT data to the GUI.
  - `defs.h`: global synth constants and `ParamID` enum shared with Python.

- `bindings/`
  - `main_bindings.cpp`: `pybind11` bindings exposing `SynthEngine` as the `ssynth_cpp.Engine` Python class and the `Params` enum.
  - Provides a zero‑copy bridge from Python/NumPy to the C++ engine for both audio rendering and spectrum data.

- `frontend/gui/` (Python GUI)
  - `window_gui.py`: main `QMainWindow` that hosts the spectrogram, oscillator panels, and ADSR controls, and manages presets (`user/*.json`).
  - `osc_panel.py`: panel for a single oscillator (waveform type, mix, pitch and fine detune) backed by engine parameters.
  - `adsr.py`: ADSR control panel mapped to the engine amp envelope parameters.
  - `knob.py`: custom high‑performance knob widget with preloaded sprite frames and smooth interaction.
  - `button.py`: image‑based button widget with hover, press and toggle states.
  - `visual/visualizer.py`: OpenGL time‑domain waveform visualizer.
  - `visual/spectrogram/spectrogram_widget.py`: OpenGL spectrogram widget that consumes FFT magnitudes from the engine.
  - `visual/spectrogram/spectrogram_frame.py`: spectrogram frame with glass overlay and styling.

- `frontend/assets/`
  - Static images for background, knobs, buttons and glass overlay used by the GUI.

- `frontend/utils/logger.py`
  - Simple colored logger for debugging with file/line information.

- `tables/`
  - Pre‑computed wavetable files (`*.wvt`) for sine, saw, square and triangle waves.

- `tools/wavemanager.py`
  - Offline tool that generates high‑quality wavetable MIP‑chains using additive synthesis and writes `.wvt` files.

- `user/`
  - Preset storage (`*.json`) for saving and loading synthesizer states from the GUI.

- `main.py`
  - Python entry point.
  - Loads `ssynth_cpp` module, initializes the engine, wavetables and Qt application, starts the audio stream (`sounddevice`) and shows the main window.

## Dependencies

### Platform

- macOS (currently primary/target platform; Windows support is planned but not yet complete).

### Build‑time (C++ core)

- C++17‑compatible compiler (Clang on macOS).
- CMake ≥ 3.15.
- Python (Interpreter + Development components, used by CMake via `find_package(Python ...)`).
- `pybind11` 
- FFTW3 (float version, typically `fftw3f` and `fftw3f_threads`).
- OpenMP (e.g. `libomp` on macOS).

### Python runtime

These packages are used directly in the Python code:

- `numpy`
  - Array math, interpolation and color‑map generation for the spectrogram and visualization tools.
- `sounddevice`
  - Real‑time audio output and callback integration with the C++ engine.
- `PyQt6`
  - Main GUI framework, widgets, layouting and resource handling.
- `PyQt6.QtOpenGLWidgets`
  - OpenGL‑backed widgets used by the waveform and spectrogram visualizers.
- `PyOpenGL`
  - Direct OpenGL calls (`OpenGL.GL`) inside visualization widgets.

## Build

The project is split into a C++ core (built as a Python extension) and a Python application.

1. Install the system and Python dependencies listed above (on macOS, `fftw` and `libomp` can be installed via Homebrew).
2. Configure the CMake project in a `build/` directory (from the project root):

   ```bash
   mkdir -p build
   cd build
   cmake .. -DCMAKE_BUILD_TYPE=Release
   make
   ```

3. Alternatively, use the helper script (expects an already‑configured `build/` directory):

   ```bash
   ./build.sh
   ```

## Run

From the project root, after building the `ssynth_cpp` module:

```bash
python3 main.py
```

## Usage

Currently, three separate oscillators are available, each with four waveforms and adjustable volume, pitch (in semitones), and pitch deviation (fine tuning) in Hz.
To adjust attack, decay, sustain and release, use the ADSR block on the right side of the GUI, separated by a vertical line.
Any changes can be saved (or loaded) as a preset in a JSON file; presets are stored under the `user/` directory.
To load a default preset, use the `default.json` file, which cannot be overwritten from within the program.
A spectrogram at the top of the screen helps monitor the spectrum and dynamics of the sound being played in real time.

## Key technologies

A few of the more interesting / essential techniques used in this project:

- **Wavetable synthesis with MIP‑mapped tables**
  - Multi‑resolution wavetable chains (MIP levels) per waveform, selected per sample based on playback frequency and linearly interpolated across tables to reduce aliasing.

- **Polyphonic, parameter‑driven C++ engine**
  - Up to `MAX_VOICES` voices, each with three oscillators, individual pitch/fine detune and amp envelope, mixed in an equal‑power stereo pan law.
  - Real‑time parameter updates via a shared `ParamID` enum exposed to Python.

- **Zero‑copy Python ↔ C++ bridge**
  - `pybind11` bindings that render directly into NumPy arrays and fetch FFT magnitudes without extra copying.

- **Real‑time spectrogram using FFTW3 + OpenMP + OpenGL**
  - FFTW3 (float) transforms on a ring‑buffered audio signal, converted to 0..1 magnitudes and visualized as an animated texture in an OpenGL `QOpenGLWidget`.
  - Log‑frequency resampling and custom Magma‑style color lookup table implemented with `numpy`.

- **Custom PyQt6 UI components**
  - Sprite‑based knobs and buttons with smooth mouse interaction and text overlays, themed background, and a framed glass overlay for the spectrogram.

- **Preset system**
  - Human‑readable JSON presets mapping directly to oscillator and envelope states, allowing quick recall of patches.

## TODO

- [x] Describe architecture
- [x] Make separate DSP core and API
- [ ] Improve the GUI
- [ ] Improve algorithms
- [ ] Implement new functions
- [ ] Implement effect rack
- Much later
  - [ ] Full Windows support (currently only macOS is available)
  - [ ] Make full documentation

## License

This project is licensed under the MIT License - see the `LICENSE.md` file for details.

## Contacts

- Telegram: [cyrepoor](https://t.me/cyrepoor)
- Email: `st131335@student.spbu.ru`
