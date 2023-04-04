#!/bin/bash

SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd ${SCRIPTS_DIR}/../

boi="# begin of installation"
eoi="# end of installation"
for colab_file in ./docs/notebooks/*.ipynb ; do
    file_name="${colab_file%.ipynb}"
    python_file="${file_name}.py"
    python_basename_file=$(basename ${python_file})
    jupyter nbconvert --to python ${colab_file} --output ${python_basename_file} --TagRemovePreprocessor.remove_cell_tags remove_from_CI
    if [ ! $? == 0 ]; then
        rm ./docs/notebooks/*.py
        echo " FAILED ${colab_file} conversion to python"
        exit 1
    fi
    echo -n "  -> Testing ${python_basename_file}..."
    output=`ipython3 ${python_file} 2>&1`
    if [ ! $? == 0 ]; then
        rm ./docs/notebooks/*.py
        echo " FAILED for the following reason:"
        echo "${output}"
        exit 1
    fi
    echo " DONE!"
done
rm ./docs/notebooks/*.py
exit 0
