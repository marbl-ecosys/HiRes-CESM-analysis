#!/bin/bash

usage () {
  echo "$0 NOTEBOOK [NOTEBOOK2 ... NOTEBOOKN]"
  echo "Submit job(s) to run all notebooks on casper node via jupyter nbconvert"
  echo ""
  echo "For each specified file, the full call is:"
  echo "jupyter nbconvert --to notebook --inplace --ExecutePreprocessor.kernel_name=python \\
                  --ExecutePreprocessor.timeout=3600 --execute NOTEBOOK"
  echo ""
  echo "Output from the pbs job is written in the logs/ directory,"
  echo "which will be created if it does not exist."
}

#########################

# Function that creates a temporary script
# that is submitted via qsub
submit_pbs_script () {

  nbname=`echo ${notebook} | sed -e "s/ /_/g"`

  echo "running ${notebook}.ipynb..."
  cat > ${nbname}.sub << EOF
#!/bin/bash
#
#PBS -N ${nbname}
#PBS -A P93300606
#PBS -l select=1:ncpus=1:mem=100G
#PBS -l walltime=6:00:00
#PBS -q casper
#PBS -j oe
#PBS -m ea

${set_env}
jupyter nbconvert --to notebook --inplace --ExecutePreprocessor.kernel_name=python \\
                  --ExecutePreprocessor.timeout=3600 --execute "${notebook}.ipynb"
EOF

  qsub ${nbname}.sub
  rm -f ${nbname}.sub
}

########################

# Function that creates a temporary script
# that is submitted via sbatch
submit_slurm_script () {

  nbname=`echo ${notebook} | sed -e "s/ /_/g"`

  echo "running ${notebook}.ipynb..."
  cat > ${nbname}.sub << EOF
#!/bin/bash
#
#SBATCH -n 16
#SBATCH -N 1
#SBATCH --ntasks-per-node=16
#SBATCH -t 6:00:00
#SBATCH -p dav
#SBATCH -J ${nbname}
#SBATCH --account=P93300606
#SBATCH --mem 100G
#SBATCH -e logs/${nbname}.err.%J
#SBATCH -o logs/${nbname}.out.%J
#SBATCH --mail-type=ALL
#SBATCH --mail-user=${USER}@ucar.edu
#SBATCH -m block

${set_env}
jupyter nbconvert --to notebook --inplace --ExecutePreprocessor.kernel_name=python \\
                  --ExecutePreprocessor.timeout=3600 --execute "${notebook}.ipynb"
EOF

  sbatch ${nbname}.sub
  rm -f ${nbname}.sub
}

#########################

if [ $# == 0 ]; then
  usage
  exit 1
fi

for args in "$@"
do
  if [ "$args" == "-h" ] || [ "$args" == "--help" ]; then
    usage
    exit 0
  fi
done

# not sure why conda activate doesn't work but source activate does...
set_env="export PATH=/glade/work/${USER}/miniconda3/bin/:$PATH ; source activate hires-marbl || exit -1"

# make sure log directory exists
mkdir -p logs

for notebook_full in "$@"
do
  if [ ! -f "${notebook_full}" ]; then
    echo "WARNING: can not find ${notebook_full}"
    continue
  fi
  notebook=`echo ${notebook_full} | cut -d '.' -f 1`
  submit_pbs_script $notebook
done
