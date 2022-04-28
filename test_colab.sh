#!/bin/bash

boi="# begin of installation"
eoi="# end of installation"
for colab_file in ./unified_planning/notebook/*.ipynb ; do
    file_name="${colab_file%.ipynb}"
    jupyter nbconvert --to python ${colab_file}
    python_file="${file_name}.py"
    file_tested_name="${file_name}_rewritten.py"
    trim_rows="false"
    echo "  " > ${file_tested_name}
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
    ipython3 ${file_tested_name}
    if [ ! $? == 0 ]; then
        rm ./unified_planning/notebook/*.py
        exit 1
    fi
done
rm ./unified_planning/notebook/*.py
exit 0
