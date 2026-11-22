#!/bin/bash -l
#SBATCH --job-name=P13
#SBATCH --account=dtu_00075
#SBATCH --partition=thinnode
#SBATCH --nodes=1
#SBATCH --ntasks=8
#SBATCH --mem-per-cpu=2G
#SBATCH --time=03:00:00
#SBATCH --output=slurm.%j.out
# Usage, from the case folder:  sbatch runSlurm.sh
# Options of Allrun are passed on:  sbatch --export=ALL,MESH=coarse runSlurm.sh
export PAGER=cat MODULES_PAGER=cat
module use /services/tools/modulefiles
module load tools gcc/14.2.0 gsl/2.7 fftw/3.3.10 ucx/1.20.0 openmpi/5.0.2 cuda/toolkit/11.0.3 openfoam.com/2506
source /services/tools/openfoam.com/2506/OpenFOAM-v2506/etc/bashrc
export OMPI_MCA_pml=ob1 OMPI_MCA_btl=self,vader
export NP=${SLURM_NTASKS}
cd "$SLURM_SUBMIT_DIR" || exit 1
./Allclean
./Allrun
