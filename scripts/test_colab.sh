#!/bin/bash

SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd ${SCRIPTS_DIR}/../

for colab_file in `find ./docs/notebooks -name '*.ipynb'` ; do
    file_name="${colab_file%.ipynb}"
    python_file="${file_name}.py"
    python_basename_file=$(basename ${python_file})
    file_dir=$(dirname "${python_file}")
    jupyter nbconvert --to python ${colab_file} --output ${python_basename_file} --TagRemovePreprocessor.remove_cell_tags remove_from_CI
    if [ ! $? == 0 ]; then
        echo " FAILED ${colab_file} conversion to python"
        exit 1
    fi
    echo -n "  -> Testing ${python_basename_file}..."
    output=$(cd "${file_dir}" && ipython3 "${python_basename_file}" 2>&1)
    exit_code=$?
    rm ${python_file}
    
    # NOTE: 14-task-and-motion-planning.ipynb may exit with code 134/139 even on successful execution
    # due to a OMPL issue (crash at shutdown). These exit codes are treated as success.
    if [ $exit_code -eq 0 ] || {
        [ "$(basename "${colab_file}")" = "14-task-and-motion-planning.ipynb" ] &&
        { [ $exit_code -eq 134 ] || [ $exit_code -eq 139 ]; }
    }; then
        echo " DONE!"
    else
        echo " FAILED for the following reason:"
        echo "${output}"
        exit 1
    fi
done
exit 0
