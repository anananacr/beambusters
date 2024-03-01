import settings
import subprocess as sub
import h5py
import numpy as np
from utils import open_dark_and_gain_files, apply_calibration, centering_converged
import matplotlib.pyplot as plt
import sys

sys.path.append("/home/rodria/scripts/bblib")
import os
import pathlib
from bblib.methods import CenterOfMass, FriedelPairs, MinimizePeakFWHM, CircleDetection
from bblib.models import PF8Info, PF8


config = settings.read("config.yaml")
BeambustersParam = settings.parse(config)
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

if not config["calibration"]["skip"]:
    dark, gain = open_dark_and_gain_files(
        calibration_files_directory=config["calibration"]["calibration_files_directory"]
    )

initialized_arrays = False
## check plots info
if config["plots"]["flag"]:
    config["plots_flag"] = True
    plots_info = {
        "file_name": config["plots"]["file_name"],
        "folder_name": config["plots"]["folder_name"],
        "root_path": config["plots"]["root_path"],
    }
    number_of_frames = 20
    starting_frame = config["starting_frame"]
else:
    config["plots_flag"] = False
    plots_info = {"file_name": "", "folder_name": "", "root_path": ""}
    number_of_frames = len(paths)
    starting_frame = 0

## Set peakfinder8 config
PF8Config = settings.get_pf8_info(config)

try:
    list_index = int(config["raw_data_list_file"].split("lst")[-1])
except ValueError:
    list_index = 0

for index, path in enumerate(paths[starting_frame : starting_frame + number_of_frames]):
    file_name, frame_number = path.split(" //")
    frame_number = int(frame_number)
    plots_info["file_name"] = config["plots"]["file_name"] + f"_{frame_number}"

    with h5py.File(f"{file_name}", "r") as f:
        data = np.array(f[h5_path][frame_number], dtype=np.int32)
        if not initialized_arrays:
            _data_shape = data.shape

    if not initialized_arrays:
        raw_dataset = np.ndarray((number_of_frames, *_data_shape), dtype=np.int32)
        dataset = np.ndarray((number_of_frames, *_data_shape), dtype=np.int32)
        refined_detector_center = np.ndarray((number_of_frames, 2), dtype=np.float32)
        initial_guess_center = np.ndarray((number_of_frames, 2), dtype=np.float32)
        detector_center_from_center_of_mass = np.ndarray(
            (number_of_frames, 2), dtype=np.int16
        )
        detector_center_from_circle_detection = np.ndarray(
            (number_of_frames, 2), dtype=np.int16
        )
        detector_center_from_minimize_peak_fwhm = np.ndarray(
            (number_of_frames, 2), dtype=np.int16
        )
        detector_center_from_friedel_pairs = np.ndarray(
            (number_of_frames, 2), dtype=np.float32
        )
        shift_x_mm = np.ndarray((number_of_frames,), dtype=np.float32)
        shift_y_mm = np.ndarray((number_of_frames,), dtype=np.float32)
        initialized_arrays = True

    raw_dataset[index, :, :] = data

    if not config["calibration"]["skip"]:
        calibrated_data = apply_calibration(data=data, dark=dark, gain=gain)
    else:
        calibrated_data = data

    dataset[index, :, :] = calibrated_data

    ## Refine the detector center
    ## Set geometry in PF8

    PF8Config.set_geometry_from_file(config["geometry_file"])

    if "center_of_mass" not in config["skip_methods"]:
        center_of_mass_method = CenterOfMass(
            config=config, PF8Config=PF8Config, plots_info=plots_info
        )
        detector_center_from_center_of_mass[index, :] = center_of_mass_method(
            data=calibrated_data
        )

    if "circle_detection" not in config["skip_methods"]:
        circle_detection_method = CircleDetection(
            config=config, PF8Config=PF8Config, plots_info=plots_info
        )
        detector_center_from_circle_detection[index, :] = circle_detection_method(
            data=calibrated_data
        )

    ## define initial_guess

    if config["force_center"]["mode"]:
        initial_guess = [config["force_center"]["x"], config["force_center"]["y"]]
    elif config["method"] == "center_of_mass":
        initial_guess = detector_center_from_center_of_mass[index]
    elif config["method"] == "circle_detection":
        initial_guess = detector_center_from_circle_detection[index]
    else:
        initial_guess = PF8Config.detector_center_from_geom

    initial_guess_center[index, :] = initial_guess
    ## final refinement

    if "minimize_peak_fwhm" not in config["skip_methods"]:
        minimize_peak_fwhm_method = MinimizePeakFWHM(
            config=config, PF8Config=PF8Config, plots_info=plots_info
        )
        detector_center_from_minimize_peak_fwhm[index, :] = minimize_peak_fwhm_method(
            data=calibrated_data, initial_guess=initial_guess
        )

        # update initial guess if converged
        if centering_converged(detector_center_from_minimize_peak_fwhm[index, :]):
            initial_guess = detector_center_from_minimize_peak_fwhm[index,:]

    if "friedel_pairs" not in config["skip_methods"]:
        friedel_pairs_method = FriedelPairs(
            config=config, PF8Config=PF8Config, plots_info=plots_info
        )
        detector_center_from_friedel_pairs[index, :] = friedel_pairs_method(
            data=calibrated_data, initial_guess=initial_guess
        )

    ## Refined detector center assignement
    if "friedel_pairs" not in config["skip_methods"] and centering_converged(
        detector_center_from_friedel_pairs[index, :]
    ):
        refined_detector_center[index, :] = detector_center_from_friedel_pairs[index, :]
    elif "minimize_peak_fwhm" not in config["skip_methods"] and centering_converged(
        detector_center_from_minimize_peak_fwhm[index, :]
    ):
        refined_detector_center[index, :] = detector_center_from_minimize_peak_fwhm[
            index, :
        ]
    else:
        refined_detector_center[index, :] = initial_guess

    beam_position_shift_in_pixels = (
        refined_detector_center[index] - PF8Config.detector_center_from_geom
    )

    detector_shift_in_mm = [
        np.round(-1 * x * 1e3 / PF8Config.pixel_resolution, 4)
        for x in beam_position_shift_in_pixels
    ]
    shift_x_mm[index] = detector_shift_in_mm[0]
    shift_y_mm[index] = detector_shift_in_mm[1]

## Create output path
file_label = os.path.basename(file_name).split(".")[0]
root_directory, path_on_raw = os.path.dirname(file_name).split("/raw/")
output_path = config["output_path"] + "/centered/" + path_on_raw
path = pathlib.Path(output_path)
path.mkdir(parents=True, exist_ok=True)

## get camera length from PF8 pixel maps
clen = float(np.mean(PF8Config.pixel_maps["z"]))

## Write centered file

with h5py.File(f"{output_path}/{file_label}_{list_index}.h5", "w") as f:
    entry = f.create_group("entry")
    entry.attrs["NX_class"] = "NXentry"
    grp_data = entry.create_group("data")
    grp_data.attrs["NX_class"] = "NXdata"
    grp_data.create_dataset("data", data=dataset, compression="gzip")
    grp_data.create_dataset("raw_data", data=raw_dataset, compression="gzip")
    grp_shots = entry.create_group("shots")
    grp_shots.attrs["NX_class"] = "NXdata"
    grp_shots.create_dataset(
        "detector_shift_x_in_mm", data=shift_x_mm, compression="gzip"
    )
    grp_shots.create_dataset(
        "detector_shift_y_in_mm", data=shift_y_mm, compression="gzip"
    )
    grp_proc = f.create_group("pre_processing")
    grp_proc.attrs["NX_class"] = "NXdata"
    for key, value in BeambustersParam.items():
        grp_proc.create_dataset(key, data=value)
    grp_proc.create_dataset("raw_path", data=paths)
    grp_proc.create_dataset(
        "refined_detector_center", data=refined_detector_center, compression="gzip"
    )
    grp_proc.create_dataset(
        "center_from_center_of_mass",
        data=detector_center_from_center_of_mass,
        compression="gzip",
    )
    grp_proc.create_dataset(
        "center_from_circle_detection",
        data=detector_center_from_circle_detection,
        compression="gzip",
    )
    grp_proc.create_dataset(
        "center_from_minimize_peak_fwhm",
        data=detector_center_from_minimize_peak_fwhm,
        compression="gzip",
    )
    grp_proc.create_dataset(
        "center_from_friedel_pairs",
        data=detector_center_from_friedel_pairs,
        compression="gzip",
    )
    grp_proc.create_dataset(
        "initial_guess_center",
        data=initial_guess_center,
        compression="gzip",
    )
    grp_proc.create_dataset(
        "detector_center_from_geometry_file",
        data=PF8Config.detector_center_from_geom,
        compression="gzip",
    )
    grp_proc.create_dataset("pixel_resolution", data=PF8Config.pixel_resolution)
    grp_proc.create_dataset("camera_length", data=clen)
