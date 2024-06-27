#!/bin/bash

#SBATCH --job-name=sizing-doe
#SBATCH --cpus-per-task=1
#SBATCH --mem=8gb
#SBATCH --time=2-00:00:00

while getopts ":n:r:g:p:s:a:d" opt; do
  case $opt in
    n | r | g | p | s| a)
      eval $opt=$OPTARG
      ;;
    d)
      DEBUG=--debug
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
  esac
done

# assign unset variables a value of "None"
ARGS_TO_PASS=${DEBUG}
for var_name in n r g p s a
do
    var_value="${!var_name}"
    var_value_length=${#var_value}
    if [ ${var_value_length} -gt 0 ]
    then
       ARGS_TO_PASS="${ARGS_TO_PASS} -${var_name} ${var_value}"
    fi
done

. /etc/profile
export PYTHONPATH=${PYTHONPATH}:.
module load lang/python/3.9.13
pip install -r requirements-api.txt

echo "args_to_pass: ${ARGS_TO_PASS}"

time run/sizing/sizing.py ${ARGS_TO_PASS}
