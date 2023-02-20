#!/bin/bash

SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd ${SCRIPTS_DIR}/../docs/

boi="# begin of installation"
eoi="# end of installation"
for colab_file in ./notebooks/*.ipynb ; do
    file_name="${colab_file%.ipynb}"
    python_file="${file_name}.py"
    python_basename_file=$(basename ${python_file})
    jupyter nbconvert --to python ${colab_file} --output ${python_basename_file}
    if [ ! $? == 0 ]; then
        rm ./notebooks/*.py
        echo " FAILED ${colab_file} conversion to python"
        exit 1
    fi
    file_tested_name="${file_name}_rewritten.py"
    trim_rows="false"
    touch ${file_tested_name}
    while IFS= read -r line
    do
        if [[ "${line}" == *"${boi}"* ]]
        then
            trim_rows="true"
        elif [[ "${line}" == *"${eoi}"* ]]
        then
            trim_rows="false"
        elif [ "${trim_rows}" = "false" ]
        then
            echo "${line}" >> ${file_tested_name}
        fi
    done < "${python_file}"
    echo -n "  -> Testing ${file_tested_name}..."
    output=`ipython3 ${file_tested_name} 2>&1`
    if [ ! $? == 0 ]; then
        rm ./notebooks/*.py
        echo " FAILED for the following reason:"
        echo "${output}"
        exit 1
    fi
    echo " DONE!"
done
rm ./notebooks/*.py
exit 0
