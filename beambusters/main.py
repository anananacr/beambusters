import typer
from beambusters import settings
import subprocess as sub
import h5py
import numpy as np
from beambusters.utils import centering_converged, list_events
import matplotlib.pyplot as plt
import math
import hdf5plugin
import os
import pathlib
import sys
from bblib.methods import CenterOfMass, FriedelPairs, MinimizePeakFWHM, CircleDetection
from bblib.models import PF8Info, PF8

app = typer.Typer()


@app.command("run_centering")
def run_centering(input: str, path_to_config: str, test_only: bool = False):
    """
    Runs the detector center refinement.

    The centering receives an INPUT, that is a list (.lst) file containing the name of HDF5 files in which the centering will be applied.

    The configuration parameters for the centering are passed throug a config.yaml file indicated by PATH_TO_CONFIG

    Options:

    --test-only     Use the test only if you don't want to save the output centered files.

    """

    config = settings.read(path_to_config)
    BeambustersParam = settings.parse(config)
    files = open(input, "r")
    paths = files.readlines()
    files.close()

    if len(paths[0][:-1].split(" //")) == 1:
        list_name = input
        events_list_file = (
            f"{list_name.split('.')[0]}_events.lst{list_name.split('.lst')[-1]}"
        )
        list_events(list_name, events_list_file, config["geometry_file"])
        files = open(events_list_file, "r")
        paths = files.readlines()
        files.close()

    geometry_txt = open(config["geometry_file"], "r").readlines()
    data_hdf5_path = [
        x.split(" = ")[-1][:-1] for x in geometry_txt if x.split(" = ")[0] == "data"
    ][0]

    initialized_arrays = False

    ## Check plots info

    if config["plots"]["flag"]:
        config["plots_flag"] = True
        plots_info = settings.parse_plots_info(config=config)
        number_of_frames = config["plots"]["maximum_number_of_frames"]
        starting_frame = config["starting_frame"]
    else:
        config["plots_flag"] = False
        plots_info = {"file_name": "", "folder_name": "", "root_path": ""}
        number_of_frames = len(paths)
        starting_frame = 0

    ## Set peakfinder8 configuration
    PF8Config = settings.get_pf8_info(config)

    raw_file_id = []

    for index, path in enumerate(
        paths[starting_frame : starting_frame + number_of_frames]
    ):
        raw_file_id.append(path)
        file_name, frame_number = path.split(" //")
        print(f"Image filename: {file_name}")
        print(f"Event: //{frame_number}")
        frame_number = int(frame_number)

        if config["plots_flag"]:
            plots_info["file_name"] = config["plots"]["file_name"] + f"_{frame_number}"

        with h5py.File(f"{file_name}", "r") as f:
            data = np.array(f[data_hdf5_path][frame_number], dtype=np.int32)
            if not initialized_arrays:
                _data_shape = data.shape

            if config["burst_mode"]["is_active"]:
                storage_cell_hdf5_path = config["burst_mode"]["storage_cell_hdf5_path"]
                debug_hdf5_path = config["burst_mode"]["debug_hdf5_path"]

                storage_cell_number_of_frame = int(
                    f[f"{storage_cell_hdf5_path}"][frame_number]
                )
                debug_from_raw_of_frame = np.array(
                    f[f"{debug_hdf5_path}"][frame_number]
                )

        if not initialized_arrays:
            raw_dataset = np.zeros((number_of_frames, *_data_shape), dtype=np.int32)
            dataset = np.zeros((number_of_frames, *_data_shape), dtype=np.int32)
            refined_detector_center = np.zeros((number_of_frames, 2), dtype=np.float32)
            refined_center_flag = np.zeros(number_of_frames, dtype=np.int16)

            initial_guess_center = np.zeros((number_of_frames, 2), dtype=np.float32)
            detector_center_from_center_of_mass = np.zeros(
                (number_of_frames, 2), dtype=np.int16
            )
            detector_center_from_circle_detection = np.zeros(
                (number_of_frames, 2), dtype=np.int16
            )
            detector_center_from_minimize_peak_fwhm = np.zeros(
                (number_of_frames, 2), dtype=np.int16
            )
            detector_center_from_friedel_pairs = np.zeros(
                (number_of_frames, 2), dtype=np.float32
            )
            shift_x_mm = np.zeros((number_of_frames,), dtype=np.float32)
            shift_y_mm = np.zeros((number_of_frames,), dtype=np.float32)
            if config["burst_mode"]["is_active"]:
                storage_cell_number = np.zeros((number_of_frames,), dtype=np.int16)
                debug_from_raw = np.zeros((number_of_frames, 2), dtype=np.int16)
            initialized_arrays = True

        raw_dataset[index, :, :] = data

        if config["burst_mode"]["is_active"]:
            storage_cell_number[index] = storage_cell_number_of_frame
            debug_from_raw[index, :] = debug_from_raw_of_frame

        calibrated_data = data

        dataset[index, :, :] = calibrated_data

        ## Refine the detector center
        ## Set geometry in PF8

        PF8Config.set_geometry_from_file(config["geometry_file"])

        if "center_of_mass" not in config["skip_centering_methods"]:
            center_of_mass_method = CenterOfMass(
                config=config, PF8Config=PF8Config, plots_info=plots_info
            )
            detector_center_from_center_of_mass[index, :] = center_of_mass_method(
                data=calibrated_data
            )

        if "circle_detection" not in config["skip_centering_methods"]:
            circle_detection_method = CircleDetection(
                config=config, PF8Config=PF8Config, plots_info=plots_info
            )
            detector_center_from_circle_detection[index, :] = circle_detection_method(
                data=calibrated_data
            )

        ## Define the initial_guess

        initial_guess = [-1, -1]
        if config["centering_method_for_initial_guess"] == "center_of_mass":
            initial_guess = detector_center_from_center_of_mass[index]
        elif config["centering_method_for_initial_guess"] == "circle_detection":
            initial_guess = detector_center_from_circle_detection[index]

        if config["force_center"]["state"]:
            if config["force_center"]["anchor_x"]:
                initial_guess[0] = config["force_center"]["x"]

            if config["force_center"]["anchor_y"]:
                initial_guess[1] = config["force_center"]["y"]

        if initial_guess[0] == -1 and initial_guess[1] == -1:
            initial_guess = PF8Config.detector_center_from_geom

        initial_guess_center[index, :] = initial_guess

        distance = math.sqrt(
            (initial_guess[0] - config["reference_center"]["x"]) ** 2
            + (initial_guess[1] - config["reference_center"]["y"]) ** 2
        )

        if distance < config["outlier_distance"]:
            ## Ready for detector center refinement
            PF8Config.update_pixel_maps(
                initial_guess[0] - PF8Config.detector_center_from_geom[0],
                initial_guess[1] - PF8Config.detector_center_from_geom[1],
            )

            pf8 = PF8(PF8Config)
            peak_list = pf8.get_peaks_pf8(data=calibrated_data)
            PF8Config.set_geometry_from_file(config["geometry_file"])

            if "friedel_pairs" not in config["skip_centering_methods"]:
                PF8Config.set_geometry_from_file(config["geometry_file"])
                friedel_pairs_method = FriedelPairs(
                    config=config, PF8Config=PF8Config, plots_info=plots_info
                )
                detector_center_from_friedel_pairs[index, :] = friedel_pairs_method(
                    data=calibrated_data, initial_guess=initial_guess
                )
                if centering_converged(detector_center_from_friedel_pairs[index, :]):
                    center_is_refined = True
                else:
                    center_is_refined = False
        else:
            center_is_refined = False

        ## Refined detector center assignement
        if center_is_refined:
            refined_detector_center[index, :] = detector_center_from_friedel_pairs[
                index, :
            ]
            refined_center_flag[index] = 1

        else:
            refined_detector_center[index, :] = initial_guess
            refined_center_flag[index] = 0

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
    file_label = os.path.basename(file_name).split("/")[-1][:-3]
    converted_path = config["input_path"].split("/")[-1]
    root_directory, path_in_raw = os.path.dirname(file_name).split(converted_path)
    output_path = config["output_path"] + path_in_raw
    path = pathlib.Path(output_path)
    path.mkdir(parents=True, exist_ok=True)

    ## Get camera length from PF8 pixel maps
    clen = float(np.mean(PF8Config.pixel_maps["z"]))

    ## Write centered file
    if not test_only:
        with h5py.File(f"{output_path}/{file_label}.h5", "w") as f:
            entry = f.create_group("entry")
            entry.attrs["NX_class"] = "NXentry"
            grp_data = entry.create_group("data")
            grp_data.attrs["NX_class"] = "NXdata"
            if not config["compression"]["compress_output_data"]:
                grp_data.create_dataset("data", data=dataset)
            else:
                grp_data.create_dataset(
                    "data",
                    data=dataset,
                    compression=config["compression"]["filter"],
                    compression_opts=config["compression"]["opts"],
                )

            grp_data.create_dataset("raw_file_id", data=raw_file_id)
            if config["burst_mode"]["is_active"]:
                grp_data.create_dataset("storage_cell_number", data=storage_cell_number)
                grp_data.create_dataset("debug", data=debug_from_raw)
            grp_shots = entry.create_group("shots")
            grp_shots.attrs["NX_class"] = "NXdata"
            grp_shots.create_dataset("detector_shift_x_in_mm", data=shift_x_mm)
            grp_shots.create_dataset("detector_shift_y_in_mm", data=shift_y_mm)
            grp_shots.create_dataset("refined_center_flag", data=refined_center_flag)
            grp_proc = f.create_group("preprocessing")
            grp_proc.attrs["NX_class"] = "NXdata"
            for key, value in BeambustersParam.items():
                grp_proc.create_dataset(key, data=value)
            grp_proc.create_dataset("raw_path", data=paths)
            grp_proc.create_dataset(
                "refined_detector_center", data=refined_detector_center
            )
            grp_proc.create_dataset(
                "center_from_center_of_mass", data=detector_center_from_center_of_mass
            )
            grp_proc.create_dataset(
                "center_from_circle_detection",
                data=detector_center_from_circle_detection,
            )
            grp_proc.create_dataset(
                "center_from_minimize_peak_fwhm",
                data=detector_center_from_minimize_peak_fwhm,
            )
            grp_proc.create_dataset(
                "center_from_friedel_pairs", data=detector_center_from_friedel_pairs
            )
            grp_proc.create_dataset("initial_guess_center", data=initial_guess_center)
            grp_proc.create_dataset(
                "detector_center_from_geometry_file",
                data=PF8Config.detector_center_from_geom,
            )
            grp_proc.create_dataset("pixel_resolution", data=PF8Config.pixel_resolution)
            grp_proc.create_dataset("camera_length", data=clen)


@app.callback()
def main():
    """
    Beambusters performs the detector center refinement of each diffraction patterns for serial crystallography.

    For more information, type the following command:

    beambusters run_centering --help
    """
