#!/bin/sh

#SBATCH --partition=allcpu,upex
#SBATCH --time=2-00:00:00
#SBATCH --requeue
#SBATCH --nodes=1
#SBATCH --mincpus=64
#SBATCH --mem=10G
#SBATCH --nice=100
#SBATCH --job-name  bb
#SBATCH --output   /gpfs/cfel/group/cxi/scratch/2021/ESRF-2024-Meents-Mar-ID09/processed/rodria/error/bb-%N-%j.out
#SBATCH --error    /gpfs/cfel/group/cxi/scratch/2021/ESRF-2024-Meents-Mar-ID09/processed/rodria/error/bb-%N-%j.err

INPUT=$1
OUTPUT=$2
ROOT=/gpfs/cfel/group/cxi/scratch/2021/ESRF-2024-Meents-Mar-ID09/processed/rodria

source /etc/profile.d/modules.sh
module load maxwell crystfel/0.10.2

command="indexamajig -i ${ROOT}/lists/${INPUT} -p ${ROOT}/cell/lyso.cell -o ${ROOT}/streams/${OUTPUT} -g ${ROOT}/geoms/jungfrau-1m-vertical-v0-70mm.geom --peaks=cxi"
command="$command -j 64 --int-radius=4,5,6 --copy-header=/entry/data/detector_shift_x_in_mm --copy-header=/entry/data/detector_shift_y_in_mm --copy-header=/entry/data/raw_file_id --copy-header=/entry/data/nPeaks --no-check-peaks --integration=rings-nograd-nocen --indexing=xgandalf,asdf --no-refine --no-retry --no-revalidate"
echo $command
$command
