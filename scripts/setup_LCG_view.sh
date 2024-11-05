# A script to setup LCG view for ACTS usage

lsetup "views LCG_106a x86_64-el9-gcc13-opt"

# unset PYTHONPATH and PYTHONHOME to avoid conflict with LCG python packages
export LCG_PYTHONPATH="${PYTHONPATH}"
export LCG_PYTHONHOME="${PYTHONHOME}"
unset PYTHONPATH PYTHONHOME
# set common PYTHONPATH
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/Python/3.11.9-2924c/x86_64-el9-gcc13-opt/lib/python3.11"
# unset include paths to make sure these are not detected as system includes
unset C_INCLUDE_PATH CPLUS_INCLUDE_PATH
