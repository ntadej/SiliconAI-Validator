# A script to setup Python for ACTS/SiliconAI usage

# Bash location
SETUP_LOCATION=${BASH_SOURCE[0]}
# Zsh fallback
if [[ -z ${BASH_SOURCE[0]+x} ]]; then
    SETUP_LOCATION=${(%):-%N}
fi

SILICONAI_ACTS_PATH=$(cd "$(dirname "${SETUP_LOCATION}")" && cd .. && pwd)

if [[ ! -d "${SILICONAI_ACTS_PATH}/.venv" ]]; then
    echo "Setting up Python virtual environment..."
    python3 -m venv "${SILICONAI_ACTS_PATH}/.venv"
fi

pushd "${SILICONAI_ACTS_PATH}" > /dev/null

uv sync
source .venv/bin/activate

popd > /dev/null
