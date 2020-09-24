#!/bin/bash -l
#
#SBATCH -n 64
#SBATCH -N 4
#SBATCH --ntasks-per-node=16
#SBATCH -t 24:00:00
#SBATCH -p dav
#SBATCH -J Pop.h.nday1_t13
#SBATCH --account=CESM0010
#SBATCH --mem 100G
#SBATCH -e logs/Pop.h.nday1_t13.err.%J
#SBATCH -o logs/Pop.h.nday1_t13.out.%J
#SBATCH -m block
#
module purge
conda deactivate || echo "conda not loaded"
#
# PARSE COMMAND LINE ARGUMENTS
CASE=g.e22.G1850ECO_JRA_HR.TL319_t13.${1} ; export CASE
YEAR=${2}
echo "Reshaping year ${YEAR} for ${CASE}..."
#
cd /glade/p/cesm/postprocessing_dav/cesm-env2/bin
. activate
#
module load intel/17.0.1
module load ncarenv
module load ncarcompilers
module load impi
module load netcdf/4.6.1
module load nco/4.7.4
module load ncl/6.4.0
#
HIST=pop.h.nday1 ; export HIST
#
PATH=/glade/p/cesm/postprocessing_dav/cesm-env2/bin:/usr/local/bin:${PATH} ; export PATH
#
NCKS=`which ncks`  ; export NCKS
PROCHOST=`hostname`;export PROCHOST
#
BASEDIR=/glade/u/home/strandwg/CCP_Processing_Suite
LOCALDSK=/glade/scratch/mlevy/archive/${CASE} ; export LOCALDSK
PROCBASE=/glade/scratch/$USER/T13/${CASE}     ; export PROCBASE
#
HTYP=`echo $HIST | cut -d'.' -f1` ; export HTYP
case "$HTYP" in
  cam2 | cam )
    COMP_NAME=atm ;;
  cism )
    COMP_NAME=glc ;;
  clm2 )
     COMP_NAME=lnd ;;
  pop  )
    COMP_NAME=ocn ;;
  rtm | mosart )
    COMP_NAME=rof ;;
  cice | csim )
    COMP_NAME=ice ;;
  * )
    echo "Unable to continue because "$HIST" not known."
    exit 1 ;;
esac
#
LOCAL_HIST=${LOCALDSK}/${COMP_NAME}/hist ; export LOCAL_HIST
LOCAL_PROC=${PROCBASE}/${HIST}/proc      ; export LOCAL_PROC
CACHEDIR=${LOCAL_PROC}/COMPLETED         ; export CACHEDIR
#
VERBOSITY=0 ; export VERBOSITY
PREFIX="${CACHEDIR}/${CASE}.${HIST}." ; export PREFIX
NCFORMAT=netcdf4c ; export NCFORMAT ; export NCFORMAT
#
if [ ! -d $LOCAL_PROC ] ; then
 mkdir -p $LOCAL_PROC
fi
if [ ! -d $CACHEDIR ] ; then
 mkdir -p $CACHEDIR
fi
#
cd $LOCAL_PROC
ln -s -f $BASEDIR/run_slice2series_dav Transpose_Data
#
rm -f ${CASE}.${HIST}.*nc
if [ ! -f ${LOCAL_PROC}/.DONE.${CASE}.${HIST}.${YEAR} ] ; then
  ln -s -f ${LOCAL_HIST}/${CASE}.${HIST}.${YEAR}*nc .
  NHISTF=`/bin/ls ${CASE}.${HIST}.${YEAR}*nc | wc -l`
  if [ $NHISTF -eq 12 ] ; then
    OUTTIME="${YEAR}0101-${YEAR}1231"
    SUFFIX=".${OUTTIME}.nc" ; export SUFFIX
    echo -n "TS transpose_data start: " ; date
    ./Transpose_Data
    if [ $? -ne 0 ] ; then
      echo "Transpose_Data failed"
      exit 1
    fi
    echo -n "TS transpose_data end  : " ; date
    touch ${LOCAL_PROC}/.DONE.${CASE}.${HIST}.${YEAR}
  else
    echo "File count mismatch on "${CASE}"."${HIST}"."${YEAR}": "${NHISTF}" instead of 12"
  fi
fi
#
echo -n "TS COMPLETE: " ; date
#
exit
