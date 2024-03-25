#!/bin/sh

#SBATCH --partition=allcpu,upex
#SBATCH --time=2-00:00:00
#SBATCH --requeue
#SBATCH --nodes=1
#SBATCH --nice=100
#SBATCH --mincpus=64
#SBATCH --mem=10G

#SBATCH --job-name  write_peaks_lyso_index
#SBATCH --output    /gpfs/cfel/group/cxi/scratch/2021/ESRF-2024-Meents-Mar-ID09/processed/rodria/error/peaks-%N-%j.out
#SBATCH --error     /gpfs/cfel/group/cxi/scratch/2021/ESRF-2024-Meents-Mar-ID09/processed/rodria/error/peaks-%N-%j.err

source /home/rodria/software/beambusters-dev-env/bin/activate
python write_peak_list_for_indexing.py lyso_centered