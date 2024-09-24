import typer
from beambusters import settings
import h5py
import numpy as np
from beambusters.utils import centering_converged, list_events, expand_data_to_hyperslab, translate_geom_to_hyperslab
import math
import hdf5plugin
import os
import pathlib
from bblib.methods import CenterOfMass, FriedelPairs, CircleDetection
from bblib.models import PF8

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
        plots_info = {"filename": "", "folder_name": "", "root_path": ""}
        number_of_frames = len(paths)
        starting_frame = 0
        print(config)
        #number_of_frames = config["vds_maximum_number_of_frames"]
        #starting_frame = config["vds_maximum_number_of_frames"] * config["vds_batch_id"]

    ## Set peakfinder8 configuration
    PF8Config = settings.get_pf8_info(config)

    raw_file_id = []

    for index, path in enumerate(
        paths[starting_frame : starting_frame + number_of_frames]
    ):
        raw_file_id.append(path)
        filename, frame_number = path.split(" //")
        print(f"Image filename: {filename}")
        print(f"Event: //{frame_number}")
        frame_number = int(frame_number)

        if config["plots_flag"]:
            plots_info["file_name"] = config["plots"]["filename"] + f"_{frame_number}"
            
        with h5py.File(f"{filename}", "r") as f:
            data = np.array(f[data_hdf5_path][frame_number,:], dtype=np.int32)
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
            if not config["vds_format"]:
                dataset = np.zeros((number_of_frames, *_data_shape), dtype=np.int32)
            refined_detector_center = np.zeros((number_of_frames, 2), dtype=np.float32)
            refined_center_flag = np.zeros(number_of_frames, dtype=np.int16)
            pre_centering_flag = np.zeros(number_of_frames, dtype=np.int16)

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
            hits = np.zeros((number_of_frames,), dtype=np.int16)
            if config["burst_mode"]["is_active"]:
                storage_cell_number = np.zeros((number_of_frames,), dtype=np.int16)
                debug_from_raw = np.zeros((number_of_frames, 2), dtype=np.int16)
            initialized_arrays = True

        if config["burst_mode"]["is_active"]:
            storage_cell_number[index] = storage_cell_number_of_frame
            debug_from_raw[index, 0] = debug_from_raw_of_frame


        if len(_data_shape)>1 and config["vds_format"]:
            vds_id=config["vds_id"]
            calibrated_data = expand_data_to_hyperslab(data=data, data_format=vds_id)
            geometry_filename = config["geometry_file"].split(".geom")[0]+"_hyperslab.geom"
            if not os.path.exists(geometry_filename):
                geometry_filename = translate_geom_to_hyperslab(config["geometry_file"])
        else:
            calibrated_data = data
            geometry_filename = config["geometry_file"]
        
        if not config["vds_format"]:
            dataset[index, :, :] = calibrated_data

        ## Refine the detector center
        ## Set geometry in PF8

        PF8Config.set_geometry_from_file(geometry_filename)

        pf8 = PF8(PF8Config)
        peak_list = pf8.get_peaks_pf8(data=calibrated_data)
        print(peak_list["num_peaks"])

        if "center_of_mass" not in config["skip_centering_methods"] and peak_list["num_peaks"]>config["pf8"]["min_num_peaks"]:
            center_of_mass_method = CenterOfMass(
                config=config, PF8Config=PF8Config, plots_info=plots_info
            )
            detector_center_from_center_of_mass[index, :] = center_of_mass_method(
                data=calibrated_data
            )
        else:
            detector_center_from_center_of_mass[index, :] = [-1, -1]

        if "circle_detection" not in config["skip_centering_methods"] and peak_list["num_peaks"]>config["pf8"]["min_num_peaks"]:
            circle_detection_method = CircleDetection(
                config=config, PF8Config=PF8Config, plots_info=plots_info
            )
            detector_center_from_circle_detection[index, :] = circle_detection_method(
                data=calibrated_data
            )
        else:
            detector_center_from_circle_detection[index, :] = [-1, -1]

        ## Define the initial_guess

        initial_guess = [-1, -1]
        
        
        if config["centering_method_for_initial_guess"] == "center_of_mass":
            calculated_detector_center = detector_center_from_center_of_mass[index]
            distance_in_x = math.sqrt(
                (calculated_detector_center[0] - config["reference_center"]["x"]) ** 2
            )
            distance_in_y =   math.sqrt((calculated_detector_center[1] - config["reference_center"]["y"]) ** 2)
            if distance_in_x<config["outlier_distance"]["x"] and distance_in_y<config["outlier_distance"]["y"]:
                pre_centering_flag[index] = 1
                initial_guess = detector_center_from_center_of_mass[index]
        elif config["centering_method_for_initial_guess"] == "circle_detection":
            calculated_detector_center = detector_center_from_circle_detection[index]
            distance_in_x = math.sqrt(
                (calculated_detector_center[0] - config["reference_center"]["x"]) ** 2
            )
            distance_in_y =   math.sqrt((calculated_detector_center[1] - config["reference_center"]["y"]) ** 2)
            if distance_in_x<config["outlier_distance"]["x"] and distance_in_y<config["outlier_distance"]["y"]:
                pre_centering_flag[index] = 1
                initial_guess = detector_center_from_circle_detection[index]
        # If the method chosen didn't converge change to the detector center from the geometry file

        if initial_guess[0] == -1 and initial_guess[1] == -1:
            initial_guess = PF8Config.detector_center_from_geom

        
        # Background shifting case
        if config["force_center"]["state"]:
            if config["force_center"]["anchor_x"]:
                initial_guess[0] = config["force_center"]["x"]

            if config["force_center"]["anchor_y"]:
                initial_guess[1] = config["force_center"]["y"]
            
        initial_guess_center[index, :] = initial_guess

        distance_in_x = math.sqrt(
            (initial_guess[0] - config["reference_center"]["x"]) ** 2
        )
        distance_in_y =   math.sqrt((initial_guess[1] - config["reference_center"]["y"]) ** 2)

        center_is_refined = False
        
        if distance_in_x<config["outlier_distance"]["x"] and distance_in_y<config["outlier_distance"]["y"]:
            
            ## Ready for detector center refinement
            PF8Config.update_pixel_maps(
                initial_guess[0] - PF8Config.detector_center_from_geom[0],
                initial_guess[1] - PF8Config.detector_center_from_geom[1],
            )

            pf8 = PF8(PF8Config)
            peak_list = pf8.get_peaks_pf8(data=calibrated_data)
            PF8Config.set_geometry_from_file(geometry_filename)
            print(peak_list["num_peaks"])
            if "friedel_pairs" not in config["skip_centering_methods"] and peak_list["num_peaks"]>config["pf8"]["min_num_peaks"]:
                print("hit = 1")
                hits[index] = 1
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
    #file_label = os.path.basename(filename).split("/")[-1][:-3]
    file_label = os.path.basename(filename).split("/")[-1][:-4]
    converted_path = config["input_path"].split("/")[-1]
    root_directory, path_in_raw = os.path.dirname(filename).split(converted_path)
    output_path = config["output_path"] + path_in_raw
    path = pathlib.Path(output_path)
    path.mkdir(parents=True, exist_ok=True)

    ## Get camera length from PF8 pixel maps
    clen = float(np.mean(PF8Config.pixel_maps["z"]))

    ## Write centered file
    output_file= f"{output_path}/{file_label}.cxi"
    print(output_file)
    if not config["vds_format"] and not test_only:
        with h5py.File(output_file, "w") as f:
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
    elif not test_only and config["vds_format"] and os.path.exists(output_file):
        # Append per pattern detector center in a previously created virtual dataset in centered folder
        with h5py.File(output_file, "a") as f: 
            f.create_dataset("entry_1/instrument_1/detector_shift_x_in_mm", data=shift_x_mm)
            f.create_dataset("entry_1/instrument_1/detector_shift_y_in_mm", data=shift_y_mm)
            f.create_dataset("entry_1/instrument_1/refined_center_flag", data=refined_center_flag)
            f.create_dataset("entry_1/instrument_1/pre_centering_flag", data=pre_centering_flag)
            f.create_dataset("entry_1/instrument_1/hit", data=hits)

    elif not test_only and config["vds_format"] and not os.path.exists(output_file):
        raise ValueError("Output files not found, please create the VDS in the centered folder first.")


@app.callback()
def main():
    """
    Beambusters performs the detector center refinement of each diffraction patterns for serial crystallography.

    For more information, type the following command:

    beambusters run_centering --help
    """
