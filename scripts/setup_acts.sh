# A script to setup ACTS for usage and builds it if needed

# Bash location
SETUP_LOCATION=${BASH_SOURCE[0]}
# Zsh fallback
if [[ -z ${BASH_SOURCE[0]+x} ]]; then
    SETUP_LOCATION=${(%):-%N}
fi

SILICONAI_VALIDATOR_PATH=$(cd "$(dirname "${SETUP_LOCATION}")" && cd .. && pwd)
ACTS_SOURCE_PATH="${SILICONAI_VALIDATOR_PATH}/dependencies/ACTS"
ACTS_BUILD_PATH="${SILICONAI_VALIDATOR_PATH}/dependencies/build"
ACTS_INSTALL_PATH="${SILICONAI_VALIDATOR_PATH}/dependencies/install"

echo "SiliconAI Validator path: ${SILICONAI_VALIDATOR_PATH}"
echo "ACTS source path: ${ACTS_SOURCE_PATH}"
echo "ACTS build path: ${ACTS_BUILD_PATH}"
echo "ACTS install path: ${ACTS_INSTALL_PATH}"
echo

# Run CMake
echo "Running CMake..."
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
echo

echo "Running build..."
if [[ -n ${CI+x} ]]; then
    echo "Running in the CI"
    cmake --build "${ACTS_BUILD_PATH}" -j4
else
    cmake --build "${ACTS_BUILD_PATH}"
fi
echo

echo "Running install..."
cmake --build "${ACTS_BUILD_PATH}" --target install
echo

echo "Setting-up ACTS for usage in the environment..."
source "${ACTS_INSTALL_PATH}/bin/this_acts.sh"
source "${ACTS_INSTALL_PATH}/python/setup.sh"
if [[ "$PYTHONPATH:" != "${SILICONAI_VALIDATOR_PATH}/.venv/lib/python3.11/site-packages:"* ]];
then
    export PYTHONPATH="${SILICONAI_VALIDATOR_PATH}/.venv/lib/python3.11/site-packages:${PYTHONPATH}"
fi
