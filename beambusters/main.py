"""
This module defines a Typer App for CLI usage.
"""

import h5py
import numpy as np
from beambusters.utils import (
    list_events,
    expand_data_to_hyperslab,
    translate_geom_to_hyperslab,
)
from beambusters.algorithms import calculate_detector_center_on_a_frame
from beambusters import settings
from multiprocessing import Pool
import os
from bblib.models import PF8
import typer

app = typer.Typer()


# Define the function for processing each file
def process_file(args: list) -> list:
    """
    Process one event.

    Args:
        args (list): A list of arguments containing the data event as np.ndarray, the memory cell id integer, the path of the event obtained from the input list, the configuration file path.

    Returns:
        results (list): A list with the calculated detector center shit in x and y in mm, if it is a hit, if it was pre-centered and if the center was refined.

    """
    data, memory_cell_id, path, config = args
    filename, frame_number = path.split(" //")
    print(f"Image filename: {filename}")
    print(f"Event: //{frame_number}")
    frame_number = int(frame_number)

    PF8Config = settings.get_pf8_info(config)

    # Transform vds to hyperslab
    if len(data.shape) > 2 and config["vds_format"]:
        calibrated_data = expand_data_to_hyperslab(
            data=data, data_format=config["vds_id"]
        )
        geometry_filename = (
            config["geometry_file"].split(".geom")[0] + "_hyperslab.geom"
        )
        if not os.path.exists(geometry_filename):
            geometry_filename = translate_geom_to_hyperslab(config["geometry_file"])
    else:
        calibrated_data = data
        geometry_filename = config["geometry_file"]

    # PF8 processing
    PF8Config.set_geometry_from_file(geometry_filename)
    pf8 = PF8(PF8Config)
    peak_list = pf8.get_peaks_pf8(data=calibrated_data)

    if peak_list["num_peaks"] > config["pf8"]["min_num_peaks"]:
        result = calculate_detector_center_on_a_frame(
            calibrated_data, memory_cell_id, config, PF8Config
        )
    else:
        result = [0, 0, 0, 0, 0]
    return result


# Main parallel processing
@app.command("run_centering")
def run_centering_parallel(input_file: str, path_to_config: str):
    """
    Process one HDF5 file. Results will be appended to the HDF5 file given as input file.

    Args:
        input_file (str): Full path to the HDF5 file.

        path_to_config (str): Path to the YAML configuration file.
    """
    config = settings.read(path_to_config)
    # BeambustersParam = settings.parse(config)
    files = open(input_file, "r")
    paths = files.readlines()
    files.close()

    if len(paths[0][:-1].split(" //")) == 1:
        list_name = input_file
        events_list_file = (
            f"{list_name.split('.')[0]}_events.lst{list_name.split('.lst')[-1]}"
        )
        list_events(list_name, events_list_file, config["geometry_file"])
        files = open(events_list_file, "r")
        paths = files.readlines()
        files.close()

    output_file, frame_number = paths[0].split(" //")
    filename = output_file

    geometry_txt = open(config["geometry_file"], "r").readlines()
    data_hdf5_path = [
        x.split(" = ")[-1][:-1] for x in geometry_txt if x.split(" = ")[0] == "data"
    ][0]

    ## Initialize results array
    number_of_frames = len(paths)
    refined_center_flag = np.zeros(number_of_frames, dtype=np.int16)
    pre_centering_flag = np.zeros(number_of_frames, dtype=np.int16)
    hits = np.zeros((number_of_frames,), dtype=np.int16)
    detector_shift_x_in_mm = np.zeros((number_of_frames,), dtype=np.float32)
    detector_shift_y_in_mm = np.zeros((number_of_frames,), dtype=np.float32)

    with h5py.File(f"{filename}", "r") as f:
        data_shape = f[data_hdf5_path].shape
    number_of_events = data_shape[0]
    rest = number_of_events % config["chunks"]
    results = []

    for i in range(0, number_of_events - rest, config["chunks"]):
        with h5py.File(f"{filename}", "r") as f:
            events = np.array(
                f[data_hdf5_path][i : i + config["chunks"]], dtype=np.int32
            )
            if config["burst_mode"]["is_active"]:
                memory_cells_id = np.array(
                    f[config["burst_mode"]["storage_cell_hdf5_path"]][
                        i : i + config["chunks"]
                    ],
                    dtype=np.int32,
                )
            else:
                memory_cells_id = np.zeros(config["chunks"], dtype=np.int32)

            # Use multiprocessing Pool for parallel processing
            args = [
                [event, memory_cells_id[index], paths[i + index], config]
                for index, event in enumerate(events)
            ]
            with Pool(config["number_of_processors"]) as p:
                partial_results = p.map(process_file, args)
            ## Join with results
        results = [*results, *partial_results]

    i = number_of_events - rest
    with h5py.File(f"{filename}", "r") as f:
        events = np.array(f[data_hdf5_path][i:number_of_events], dtype=np.int32)
        if config["burst_mode"]["is_active"]:
            memory_cells_id = np.array(
                f[config["burst_mode"]["storage_cell_hdf5_path"]][i:number_of_events],
                dtype=np.int32,
            )
        else:
            memory_cells_id = np.zeros(rest, dtype=np.int32)
        # Use multiprocessing Pool for parallel processing
        args = [
            [event, memory_cells_id[index], paths[index], config]
            for index, event in enumerate(events)
        ]
        with Pool(config["number_of_processors"]) as p:
            partial_results = p.map(process_file, args)

    results = [*results, *partial_results]

    ## Rearrange results arrays
    for index, i in enumerate(results):
        (
            detector_shift_x_in_mm[index],
            detector_shift_y_in_mm[index],
            hits[index],
            pre_centering_flag[index],
            refined_center_flag[index],
        ) = i

    with h5py.File(output_file, "a") as f:
        f.create_dataset(
            f"{config['output_hdf5_root_path']}/detector_shift_x_in_mm",
            data=detector_shift_x_in_mm,
        )
        f.create_dataset(
            f"{config['output_hdf5_root_path']}/detector_shift_y_in_mm",
            data=detector_shift_y_in_mm,
        )
        f.create_dataset(
            f"{config['output_hdf5_root_path']}/refined_center_flag",
            data=refined_center_flag,
        )
        f.create_dataset(
            f"{config['output_hdf5_root_path']}/pre_centering_flag",
            data=pre_centering_flag,
        )
        f.create_dataset(f"{config['output_hdf5_root_path']}/hit", data=hits)


@app.callback()
def main():
    """
    This function perfoms the pre-processing of serial crystallography data by determining the detector center shift in each frame.

    Beambusters support the VDS data format of the EuXFEL. Currently, only the Jungfrau 4M of the SPB/SFX instrument can be invoked when using the VDS data fromat.

    For more information, type the following command:

    ```bash
    beambusters run_centering --help
    ```

    """
