# Setup full SiliconAI Validator environment without building

# Bash location
SETUP_LOCATION=${BASH_SOURCE[0]}
# Zsh fallback
if [[ -z ${BASH_SOURCE[0]+x} ]]; then
    SETUP_LOCATION=${(%):-%N}
fi
SETUP_SCRIPT_LOCATION=$(cd "$(dirname "${SETUP_LOCATION}")" && pwd)
SILICONAI_VALIDATOR_PATH=$(cd "$(dirname "${SETUP_LOCATION}")" && cd .. && pwd)

source "${SETUP_SCRIPT_LOCATION}/setup_LCG_view.sh"

pushd "${SILICONAI_VALIDATOR_PATH}" > /dev/null
source .venv/bin/activate
popd > /dev/null

source "${SETUP_SCRIPT_LOCATION}/setup_acts_nobuild.sh"
