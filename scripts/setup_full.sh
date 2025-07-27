# Setup full SiliconAI Validator environment

# Bash location
SETUP_LOCATION=${BASH_SOURCE[0]}
# Zsh fallback
if [[ -z ${BASH_SOURCE[0]+x} ]]; then
    SETUP_LOCATION=${(%):-%N}
fi
SETUP_SCRIPT_LOCATION=$(cd "$(dirname "${SETUP_LOCATION}")" && pwd)

source "${SETUP_SCRIPT_LOCATION}/setup_LCG_view.sh"
source "${SETUP_SCRIPT_LOCATION}/setup_venv.sh"
source "${SETUP_SCRIPT_LOCATION}/setup_acts.sh"
