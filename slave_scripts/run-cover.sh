#!/bin/bash -xe

# Run coverage via tox. Also, run pbr freeze on the
# resulting environment at the end so that we have a record of exactly
# what packages we ended up testing.

export NOSE_COVER_HTML=1
args=$1
venv=cover

# Workaround the combo of tox running setup.py outside of virtualenv
# and RHEL having an old distribute. The next line can be removed
# when either get fixed.
python setup.py --version

tox -e$venv $args
result=$?
[ -e .tox/$venv/bin/pbr ] && freezecmd=pbr || freezecmd=pip

echo "Begin $freezecmd freeze output from test virtualenv:"
echo "======================================================================"
.tox/${venv}/bin/${freezecmd} freeze
echo "======================================================================"

exit $result
