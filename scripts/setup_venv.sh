# A script to setup Python for ACTS/SiliconAI Validator usage

# Bash location
SETUP_LOCATION=${BASH_SOURCE[0]}
# Zsh fallback
if [[ -z ${BASH_SOURCE[0]+x} ]]; then
    SETUP_LOCATION=${(%):-%N}
fi

SILICONAI_VALIDATOR_PATH=$(cd "$(dirname "${SETUP_LOCATION}")" && cd .. && pwd)

if [[ ! -d "${SILICONAI_VALIDATOR_PATH}/.venv" ]]; then
    echo "Setting up Python virtual environment..."
    python3 -m venv "${SILICONAI_VALIDATOR_PATH}/.venv"
fi

pushd "${SILICONAI_VALIDATOR_PATH}" > /dev/null

source .venv/bin/activate
uv sync --active

popd > /dev/null
