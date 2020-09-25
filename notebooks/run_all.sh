#!/bin/bash

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
#SBATCH --account=CESM0010
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


# not sure why conda activate doesn't work but source activate does...
set_env="export PATH=/glade/work/mlevy/miniconda3/bin/:$PATH ; source activate hires-marbl || exit -1"

for notebook in Sanity\ Check
do
  submit_slurm_script
done
for case in 003 004
do
  for yr in {1..61}
  do
    year=$(printf "%04d" ${yr})
    for notebook in plot_suite_maps_${year}_${case}
    do
      if [ ! -f ${notebook}.ipynb ]; then
        continue
      fi
      submit_slurm_script
    done
  done
  # For now, these don't run with nbconvert (maybe NCAR_jobqueue related?
#  for notebook in plot_suite_${case} trend_maps_${case}
#  do
#    submit_slurm_script
#  done
done
