#!/bin/bash
cat "/root/.bashrc" | tail -n +102 | head -n -2 > /opt/env.sh
source "/opt/env.sh"

cmake -G Ninja \
    -S /opt/acts-source \
    -B /opt/build \
    -DCMAKE_INSTALL_PREFIX="/opt/acts" \
    -DACTS_BUILD_ODD=ON \
    -DACTS_BUILD_PLUGIN_DD4HEP=ON \
    -DACTS_BUILD_PLUGIN_FPEMON=ON \
    -DACTS_BUILD_PLUGIN_GEANT4=ON \
    -DACTS_BUILD_FATRAS=ON \
    -DACTS_BUILD_FATRAS_GEANT4=ON \
    -DACTS_BUILD_EXAMPLES_DD4HEP=ON \
    -DACTS_BUILD_EXAMPLES_GEANT4=ON \
    -DACTS_BUILD_EXAMPLES_PYTHON_BINDINGS=ON
cmake --build /opt/build
cmake --build /opt/build --target install

rm -rf /opt/build
