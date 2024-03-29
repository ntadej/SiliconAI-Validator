# SiliconAI-ACTS

## Setup

### Python and LCG environment

Python 3.9 or later is required to run the code. LCG environment can be used
to simplify the dependency setup for ACTS. In that case run

```bash
setupATLAS -t devatlr
source ./scripts/setup_LCG_view.sh
```

first before setting up any other tool or dependency.

### Python project management

The Python project currently uses
[PDM](https://pdm-project.org). To install PDM, run the convenience script

```bash
source ./scripts/setup_pdm.sh
```

This will install PDM in the parent directory of this project and add it
to the `PATH`. For more installation options, see the PDM documentation.

To make the virtual environment and install the required packages,
run the following command:

```bash
python -m venv .venv
pdm install
```

Due to usage of external Python code the virtual environment should be entered.

```bash
source .venv/bin/activate
```

### ACTS build and setup

To build ACTS, run the following commands:

```bash
cmake -G Ninja \
    -S "${ACTS_SOURCE_PATH}" \
    -B "${ACTS_BUILD_PATH}" \
    -DCMAKE_INSTALL_PREFIX="${ACTS_INSTALL_PATH}" \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
    -DACTS_BUILD_ODD=ON \
    -DACTS_BUILD_PLUGIN_DD4HEP=ON \
    -DACTS_BUILD_PLUGIN_FPEMON=ON \
    -DACTS_BUILD_PLUGIN_GEANT4=ON \
    -DACTS_BUILD_PLUGIN_TGEO=ON \
    -DACTS_BUILD_FATRAS=ON \
    -DACTS_BUILD_FATRAS_GEANT4=ON \
    -DACTS_BUILD_EXAMPLES_DD4HEP=ON \
    -DACTS_BUILD_EXAMPLES_GEANT4=ON \
    -DACTS_BUILD_EXAMPLES_PYTHON_BINDINGS=ON
cmake --build "${ACTS_BUILD_PATH}"
cmake --build "${ACTS_BUILD_PATH}" --target install
```

Inside the virtual environment do the following setup each time:

```bash
source "${ACTS_INSTALL_PATH}/bin/this_acts.sh"
source "${ACTS_INSTALL_PATH}/python/setup.sh"
export PYTHONPATH="${SILICONAI_ACTS_PATH}/.venv/lib/python3.9/site-packages:${PYTHONPATH}"
```

### Full setup

A convenience script is available for full setup:

```bash
source ./scripts/setup_full.sh
```
