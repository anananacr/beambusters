#!/bin/sh

INPUT=$1
START=$2
END=$3
ROOT=/gpfs/cfel/group/cxi/scratch/2021/ESRF-2024-Meents-Mar-ID09/processed/rodria

for i in $(seq $START 1 $END); do
    if [ "$i" -le 9 ];
    then
        LIST_NAME=${INPUT}.lst0${i}
    else 
        LIST_NAME=${INPUT}.lst${i}
    fi
    
    LABEL=center_${i}
    JNAME="center_${i}"
    NAME="center_${i}"
    SLURMFILE="${NAME}_${INPUT}.sh"
    echo "#!/bin/sh" > $SLURMFILE
    echo >> $SLURMFILE
    echo "#SBATCH --partition=allcpu,upex" >> $SLURMFILE  # Set your partition here
    echo "#SBATCH --time=2-00:00:00" >> $SLURMFILE
    echo "#SBATCH --nodes=1" >> $SLURMFILE
    echo >> $SLURMFILE
    echo "#SBATCH --chdir   $PWD" >> $SLURMFILE
    echo "#SBATCH --job-name  $JNAME" >> $SLURMFILE
    echo "#SBATCH --requeue" >> $SLURMFILE
    echo "#SBATCH --output    /gpfs/cfel/group/cxi/scratch/2021/ESRF-2024-Meents-Mar-ID09/processed/rodria/error/${NAME}-%N-%j.out" >> $SLURMFILE
    echo "#SBATCH --error     /gpfs/cfel/group/cxi/scratch/2021/ESRF-2024-Meents-Mar-ID09/processed/rodria/error/${NAME}-%N-%j.err" >> $SLURMFILE
    echo "#SBATCH --nice=100" >> $SLURMFILE
    echo "#SBATCH --mincpus=64" >> $SLURMFILE
    echo "#SBATCH --mem=20G" >> $SLURMFILE
    echo >> $SLURMFILE
    echo "unset LD_PRELOAD" >> $SLURMFILE
    echo "source /etc/profile.d/modules.sh" >> $SLURMFILE
    echo "module purge" >> $SLURMFILE
    echo "source /gpfs/cfel/user/rodria/software/beambusters-dev-env/bin/activate" >> $SLURMFILE
    echo >> $SLURMFILE
    command="python /home/rodria/scripts/beambusters/beambusters/center_data.py ${ROOT}/lists/${LIST_NAME} config.yaml;"
    echo $command >> $SLURMFILE
    echo "chmod a+rw $PWD" >> $SLURMFILE
    sbatch $SLURMFILE 
    mv $SLURMFILE ${ROOT}/shell
done
