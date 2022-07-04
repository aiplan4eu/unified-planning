#!/bin/bash

SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd ${SCRIPTS_DIR}/../

export PYTHONPATH="${SCRIPTS_DIR}/../:$PYTHONPATH"

for python_file in ./docs/code_snippets/*.py ; do
    python_basename_file=$(basename ${python_file})
    echo -n "  -> Testing ${python_basename_file}..."
    output=`python3 ${python_file} 2>&1`
    if [ ! $? == 0 ]; then
        echo " FAILED for the following reason:"
        echo "${output}"
        exit 1
    fi
    echo " DONE!"
done
exit 0
