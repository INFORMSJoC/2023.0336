#!/bin/bash

#SBATCH --job-name=tar
#SBATCH --cpus-per-task=1
#SBATCH --mem=8gb
#SBATCH --time=2-00:00:00
#SBATCH --output=tar.out

folder=$(echo $1 | sed 's:/*$::')
if [ -z "${folder}" ]
then
    echo "input path to folder"
else 
    if [ ! -d "${folder}" ]
    then
	echo "speficied path does not exist: ${folder}"
    else
	time tar -czvf "${folder}.tar.gz" ${folder}
    fi
fi
