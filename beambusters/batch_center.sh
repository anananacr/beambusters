#!/bin/sh

#SBATCH --partition=allcpu,upex
#SBATCH --time=2-00:00:00
#SBATCH --requeue
#SBATCH --nodes=1
#SBATCH --mincpus=128
#SBATCH --mem=10G
#SBATCH --nice=100
#SBATCH --job-name  bb
#SBATCH --output   /home/rodria/error/bb-%N-%j.out
#SBATCH --error    /home/rodria/error/bb-%N-%j.err

source /etc/profile.d/modules.sh
source /home/rodria/software/beambusters-dev-env/bin/activate

python /home/rodria/scripts/beambusters/beambusters/center_data.py