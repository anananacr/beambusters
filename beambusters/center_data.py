import settings
import subprocess as sub
config = settings.read("config.yaml")

files = open(config["raw_data_list_file"], "r")
paths = files.readlines()
files.close()

if len(paths[0][:-1].split(" //")) ==1:
    # Not listed events
    command = f"source /etc/profile.d/modules.sh; module load maxwell crystfel; list_events -i {config['raw_data_list_file']} -o {config['raw_data_list_file'][:-4]}_tmp.lst -g {config['geometry_file']}"
    sub.call(command, shell=True)
    files = open(f"{config['raw_data_list_file'][:-4]}_tmp.lst", "r")
    paths = files.readlines()
    files.close()
    command = f"rm {config['raw_data_list_file'][:-4]}_tmp.lst"
    sub.call(command, shell=True)

for path in paths:

    file_name, frame_number = path.split(" //")
    frame_number=int(frame_number)

    #if config["calibration"]["on"]:
        ## start calibration pipeline

