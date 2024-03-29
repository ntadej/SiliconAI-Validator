# A script to setup LCG view for ACTS usage

lsetup "views LCG_105a x86_64-el9-gcc13-opt"

# unset PYTHONPATH and PYTHONHOME to avoid conflict with LCG python packages
unset PYTHONPATH PYTHONHOME
# unset include paths to make sure these are not detected as system includes
unset C_INCLUDE_PATH CPLUS_INCLUDE_PATH
