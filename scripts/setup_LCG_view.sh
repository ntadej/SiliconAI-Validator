# A script to setup LCG view for ACTS usage

lsetup "views LCG_108 x86_64-el9-gcc15-opt"

# unset PYTHONPATH and PYTHONHOME to avoid conflict with LCG python packages
export LCG_PYTHONPATH="${PYTHONPATH}"
export LCG_PYTHONHOME="${PYTHONHOME}"
unset PYTHONPATH PYTHONHOME
# set common PYTHONPATH
export PYTHONPATH="/cvmfs/sft.cern.ch/lcg/releases/Python/3.12.11-531c6/x86_64-el9-gcc15-opt/lib/python3.12"
# unset include paths to make sure these are not detected as system includes
unset C_INCLUDE_PATH CPLUS_INCLUDE_PATH
