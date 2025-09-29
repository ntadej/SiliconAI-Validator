# A script to setup ACTS for usage without building it

# Bash location
SETUP_LOCATION=${BASH_SOURCE[0]}
# Zsh fallback
if [[ -z ${BASH_SOURCE[0]+x} ]]; then
    SETUP_LOCATION=${(%):-%N}
fi

SILICONAI_VALIDATOR_PATH=$(cd "$(dirname "${SETUP_LOCATION}")" && cd .. && pwd)
ACTS_INSTALL_PATH="${SILICONAI_VALIDATOR_PATH}/dependencies/install"

source "${ACTS_INSTALL_PATH}/bin/this_acts.sh"
source "${ACTS_INSTALL_PATH}/python/setup.sh"
if [[ "$PYTHONPATH:" != "${SILICONAI_VALIDATOR_PATH}/.venv/lib/python3.12/site-packages:"* ]];
then
    export PYTHONPATH="${SILICONAI_VALIDATOR_PATH}/.venv/lib/python3.12/site-packages:${PYTHONPATH}"
fi
