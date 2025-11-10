# SiliconAI Validator

[![10.5281/zenodo.17567586][zenodo-img]][zenodo]
[![Latest release][release-img]][release]
[![License][license-img]][license]
[![pre-commit][pre-commit-img]][pre-commit]
[![Continuous Integration][ci-img]][ci]
[![codecov.io][codecov-img]][codecov]

Silicon detector simulation validation suite based on Acts.
It is primarily targeting ML based silicon detector simulation.

## Setup

### Quick full setup

A convenience script is available for full setup on EL9-based systems:

```bash
source ./scripts/setup_full.sh
```

Then the `siliconai_validator` command is available in the shell.

### Python and LCG environment

Python 3.12 or later is required to run the code. LCG environment can be used
to simplify the dependency setup for ACTS. In that case run

```bash
source ./scripts/setup_LCG_view.sh
```

first before setting up any other tool or dependency.

### Python project management

The Python project uses [uv](https://docs.astral.sh/uv/).
It should be installed in the system and available in the `PATH`.

To make the virtual environment and install the required packages,
run the following command:

```bash
python -m venv .venv
uv sync
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
export PYTHONPATH="${SILICONAI_VALIDATOR_PATH}/.venv/lib/python3.12/site-packages:${PYTHONPATH}"
```

## License

Copyright (C) 2024 Tadej Novak

This project is published under the terms of the Mozilla Public
License, v. 2.0, available in the file [LICENSE.md](LICENSE.md)
and at <http://mozilla.org/MPL/2.0/>.

<!--
SPDX-License-Identifier: MPL-2.0
-->

## Acknowledgements

This software is supported by the European Union's Horizon
Europe research and innovation programme under the Marie Skłodowska-Curie
Postdoctoral Fellowship Programme, SMASH, co-funded under the grant agreement
No. 101081355. The SMASH project is co-funded by the Republic of Slovenia and
the European Union from the European Regional Development Fund.

[zenodo]: https://doi.org/10.5281/zenodo.17567586
[zenodo-img]: https://zenodo.org/badge/DOI/10.5281/zenodo.17567586.svg
[release]: https://github.com/ntadej/SiliconAI-Validator/releases/latest
[release-img]: https://img.shields.io/github/release/ntadej/SiliconAI-Validator.svg
[license]: https://github.com/ntadej/SiliconAI-Validator/blob/main/LICENSE.md
[license-img]: https://img.shields.io/github/license/ntadej/SiliconAI-Validator.svg
[pre-commit]: https://results.pre-commit.ci/latest/github/ntadej/SiliconAI-Validator/main
[pre-commit-img]: https://results.pre-commit.ci/badge/github/ntadej/SiliconAI-Validator/main.svg
[ci]: https://github.com/ntadej/SiliconAI-Validator/actions
[ci-img]: https://github.com/ntadej/SiliconAI-Validator/workflows/Continuous%20Integration/badge.svg
[codecov]: https://codecov.io/github/ntadej/SiliconAI-Validator?branch=main
[codecov-img]: https://codecov.io/github/ntadej/SiliconAI-Validator/coverage.svg?branch=main
