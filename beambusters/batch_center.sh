#!/bin/sh

#SBATCH --partition=allcpu,upex
#SBATCH --time=2-00:00:00
#SBATCH --requeue
#SBATCH --nodes=1
#SBATCH --mincpus=32
#SBATCH --mem=10G
#SBATCH --nice=100
#SBATCH --job-name  bb
#SBATCH --output   /gpfs/cfel/group/cxi/scratch/2021/ESRF-2024-Meents-Mar-ID09/processed/rodria/error/bb-%N-%j.out
#SBATCH --error    /gpfs/cfel/group/cxi/scratch/2021/ESRF-2024-Meents-Mar-ID09/processed/rodria/error/bb-%N-%j.err
ROOT=/gpfs/cfel/group/cxi/scratch/2021/ESRF-2024-Meents-Mar-ID09/processed/rodria/
source /etc/profile.d/modules.sh
source /home/rodria/software/beambusters-dev-env/bin/activate

python /home/rodria/scripts/beambusters/beambusters/center_data.py $ROOT/lists/split_lyso_07_sweep_events.lst26 config.yaml