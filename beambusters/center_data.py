import settings
import subprocess as sub
import h5py
import numpy as np
from utils import open_dark_and_gain_files, apply_calibration
import matplotlib.pyplot as plt

config = settings.read("config.yaml")

files = open(config["raw_data_list_file"], "r")
paths = files.readlines()
files.close()

if len(paths[0][:-1].split(" //")) == 1:
    # Not listed events
    command = f"source /etc/profile.d/modules.sh; module load maxwell crystfel; list_events -i {config['raw_data_list_file']} -o {config['raw_data_list_file'][:-4]}_tmp.lst -g {config['geometry_file']}"
    sub.call(command, shell=True)
    files = open(f"{config['raw_data_list_file'][:-4]}_tmp.lst", "r")
    paths = files.readlines()
    files.close()
    command = f"rm {config['raw_data_list_file'][:-4]}_tmp.lst"
    sub.call(command, shell=True)

geometry_txt = open(config["geometry_file"], "r").readlines()
h5_path = [
    x.split(" = ")[-1][:-1] for x in geometry_txt if x.split(" = ")[0] == "data"
][0]

if config["calibration"]["apply_calibration"]:
    dark, gain = open_dark_and_gain_files(
        calibration_files_directory=config["calibration"]["calibration_files_directory"]
    )

for path in paths:
    file_name, frame_number = path.split(" //")
    frame_number = int(frame_number)

    with h5py.File(f"{file_name}", "r") as f:
        data = np.array(f[h5_path][frame_number], dtype=np.int32)

    if config["calibration"]["apply_calibration"]:
        calibrated_data = apply_calibration(data=data, dark=dark, gain=gain)
    else:
        calibrated_data = data
