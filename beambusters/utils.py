"""
This module defines auxiliary funtions to process the data.
"""

import sys
import h5py
import numpy as np


def centering_converged(center: tuple) -> bool:
    """
    This function receives the detector center coordinates and checks if the centering converged.

    Args:
        center (tuple): Detector center coordinates determined by onxe of the bblib centering methods.

    Returns:
        centering_flag (bool): True if the centering converged, False if the centering didn't converge.
    """
    if center[0] == -1 and center[1] == -1:
        return False
    else:
        return True


def list_events(input_file: str, output_file: str, geometry_file: str):
    """
    Expands a list of filenames into a list of individual events. Similar to the [list_events](https://www.desy.de/~twhite/crystfel/manual-list_events.html#:~:text=list_events%20expands%20a%20list%20of,than%20just%20processing%20all%20events.) in CrystFEL.

    Args:
        input_file (str): Path to the file list containg the data filename.
        output_file (str): Path to the output file list containing the individual events path.
        geometry_file (str): Path to the geometry file in CrystFEL format.

    """

    geometry_txt = open(geometry_file, "r").readlines()
    data_hdf5_path = [
        x.split(" = ")[-1][:-1] for x in geometry_txt if x.split(" = ")[0] == "data"
    ][0]

    with open(input_file, "r") as ifh, open(output_file, "w") as ofh:
        if data_hdf5_path is None:
            print(f"ERROR: Failed to read '{geometry_file}'", file=sys.stderr)
            sys.exit(1)

        for file_name in ifh:
            file_name = file_name.strip()
            if file_name:
                events_list, num_events = image_expand_frames(data_hdf5_path, file_name)
                if events_list is None:
                    print(f"ERROR: Failed to read {file_name}", file=sys.stderr)
                    sys.exit(1)

                for event in events_list:
                    ofh.write(f"{file_name} //{event}\n")

                print(f"{num_events} events found in {file_name}")


def image_expand_frames(data_hdf5_path: str, file_name: str) -> tuple:
    """
    Expands the events of an HDF5 file by specifying the HDF5 path to the data.

    Args:
        file_name (str): Path to the HDF5 file.
        data_hdf5_path (str): Path pointing to the data in the HDF5 file.

    Returns:
        events_list (np.ndarray): Array containing the number each listed event.

        num_events (int): Total number of events in the HDF5 file.
    """
    with h5py.File(f"{file_name}", "r") as f:
        num_events = (f[data_hdf5_path]).shape[0]

    events_list = np.arange(0, num_events, 1)

    return events_list, num_events


def expand_data_to_hyperslab(data: np.array, data_format: str) -> np.array:
    """
    This function takes the data in its original shape (VDS) and map each detector panel into the hyperslab that contains all detector panels in a single Numpy array.

    Supported detectors correspond to the Jungfrau 4M of the SPB/SFX instrument of the European XFEL (`vds_spb_jf4m`), see the [Extra-geom Documentation](https://extra-geom.readthedocs.io/en/latest/jungfrau_geometry.html).

    Args:
        data (np.array): Data array corresponding to one event.
        data_format (str): Data format identification. Option: `vds_spb_jf4m`.

    Returns:
        hyperslab (np.array): Data transformed from the original shape (VDS) to a single array containing all the detector panels.
    """
    if data_format == "vds_spb_jf4m":
        hyperslab = np.zeros((2048, 2048), np.int32)
        expected_shape = (8, 512, 1024)
        if data.shape != expected_shape:
            raise ValueError(
                f"Data shape for {data_format} format not in expected shape: {expected_shape}."
            )
    else:
        raise NameError("Unknown data format.")

    ## Concatenate panels in one hyperslab keep the order break after panel 4 to second column, as described here: https://extra-geom.readthedocs.io/en/latest/jungfrau_geometry.html.
    for panel_id, panel in enumerate(data):
        if panel_id < 4:
            hyperslab[512 * panel_id : 512 * (panel_id + 1), 0:1024] = panel
        else:
            if panel_id == 4:
                hyperslab[512 * (-panel_id + 3) :, 1024:2048] = panel
            else:
                hyperslab[512 * (-panel_id + 3) : 512 * (-panel_id + 4), 1024:2048] = (
                    panel
                )

    return hyperslab


def reduce_hyperslab_to_vds(data: np.array, data_format: str) -> np.array:
    """
    This function takes the data in the hyperslab shape and reduce it to the original shape (VDS).

    Supported detector is the Jungfrau 4M of the SPB/SFX instrument of the European XFEL (`vds_spb_jf4m`), see the [Extra-geom Documentation](https://extra-geom.readthedocs.io/en/latest/jungfrau_geometry.html).

    Args:
        data (np.array): Data array in the hyperslab shape.
        data_format (str): Data format identification. Option: `vds_spb_jf4m`.

    Returns:
        vds_slab (np.array): Data transformed from the hyperslab shape to the original shape (VDS).

    """
    if data_format == "vds_spb_jf4m":
        expected_shape = (2048, 2048)
        vds_slab = np.zeros((1, 8, 512, 1024), np.int32)
        if data.shape != expected_shape:
            raise ValueError(
                f"Data shape for {data_format} format not in expected shape: {expected_shape}."
            )
    else:
        raise NameError("Unknown data format.")

    ## Concatenate panels in one hyperslab keep the order break after panel 4 to second column, as described here: https://extra-geom.readthedocs.io/en/latest/jungfrau_geometry.html.
    jf_4m_matrix = [[1, 8], [2, 7], [3, 6], [4, 5]]

    for j in range(0, 2048, 1024):
        for i in range(0, 2048, 512):
            panel_number = jf_4m_matrix[int(i / 512)][int(j / 1024)]
            vds_slab[0, panel_number - 1, :] = data[i : i + 512, j : j + 1024]

    return vds_slab


def translate_geom_to_hyperslab(geometry_filename: str) -> str:
    """
    Translates the geometry file (CrystFEL format), written for data in the original shape (VDS), to perform the same operations in the panels when using the data in the hyperslab shape.

    Supported detector is the Jungfrau 4M of the SPB/SFX instrument of the European XFEL (`vds_spb_jf4m`), see the [Extra-geom Documentation](https://extra-geom.readthedocs.io/en/latest/jungfrau_geometry.html).

    Args:
        geometry_filename (str): Path to the geometry file in CrystFEL format.

    Returns:
        output_filename (str): Path to the geometry file, in CrystFEL format, for operating the hyperslab.
    """
    input_file = open(geometry_filename, "r")
    lines = input_file.readlines()
    input_file.close()

    output_filename = geometry_filename.split(".geom")[0] + "_hyperslab.geom"

    jf_4m_hyperslab = slab_to_hyperslab()

    f = open(output_filename, "w")

    for line in lines:
        key = line.split("=")[0]
        key_parts = key.split("/")
        if len(key_parts) > 1 and key_parts[1] in (
            "min_ss ",
            "min_fs ",
            "max_ss ",
            "max_fs ",
        ):
            slab_id = key_parts[0].split("a")[0]
            asic_id = key_parts[0].split(slab_id)[-1]
            new_value = get_slab_coordinates_in_hyperslab(
                slab_name=slab_id,
                asic_name=asic_id,
                key=key_parts[1][:-1],
                detector_layout=jf_4m_hyperslab,
            )
            f.write(f"{key} = {new_value}\n")
        else:
            f.write(line)
    f.close()
    return output_filename


def slab_to_hyperslab() -> dict:
    """
    Creates a dictionary containing all the panels of the detector and their corresponding slow-scan and fast-scan axis limits in the hyperslab.

    Returns:
        jf_4m_in_hyperslab (dict): A dictionary containg the panels of the Jungfrau 4M of the SPB/SFX instrument of the European XFEL, see the [Extra-geom Documentation](https://extra-geom.readthedocs.io/en/latest/jungfrau_geometry.html).
    """
    jf_4m_in_hyperslab = {}
    slab_name = "p1"
    jf_4m_in_hyperslab.update(get_500k_slab(slab_name, 0, 0))
    slab_name = "p2"
    jf_4m_in_hyperslab.update(get_500k_slab(slab_name, 512, 0))
    slab_name = "p3"
    jf_4m_in_hyperslab.update(get_500k_slab(slab_name, 1024, 0))
    slab_name = "p4"
    jf_4m_in_hyperslab.update(get_500k_slab(slab_name, 1536, 0))
    slab_name = "p5"
    jf_4m_in_hyperslab.update(get_500k_slab_inverted(slab_name, 1536, 1024))
    slab_name = "p6"
    jf_4m_in_hyperslab.update(get_500k_slab_inverted(slab_name, 1024, 1024))
    slab_name = "p7"
    jf_4m_in_hyperslab.update(get_500k_slab_inverted(slab_name, 512, 1024))
    slab_name = "p8"
    jf_4m_in_hyperslab.update(get_500k_slab_inverted(slab_name, 0, 1024))

    return jf_4m_in_hyperslab


def get_500k_slab(slab_name: str, offset_ss: int, offset_fs: int) -> dict:
    """
    This function creates a Jungfrau panel of 500k pixels with the first pixel (of the first row) positioned at the upper-left corner of the slab. The panel can be translated from the origin by specifying offsets along the slow-scan and fast-scan axes.

    Args:
        slab_name (str): Identification of the panel or slab.
        offset_ss (int): Number of indices to offset the panel along the slow-scan axis.
        offset_fs (int): Number of indices to offset the panel along the fast-scan axis.

    Returns:
        panel (dict): A dictionary containg the panel identification and its slow-scan and fast-scan limits in the hyperslab.
    """
    return {
        f"{slab_name}": {
            "a1": {
                "min_ss": 256 + offset_ss,
                "min_fs": 768 + offset_fs,
                "max_ss": 511 + offset_ss,
                "max_fs": 1023 + offset_fs,
            },
            "a2": {
                "min_ss": 256 + offset_ss,
                "min_fs": 512 + offset_fs,
                "max_ss": 511 + offset_ss,
                "max_fs": 767 + offset_fs,
            },
            "a3": {
                "min_ss": 256 + offset_ss,
                "min_fs": 256 + offset_fs,
                "max_ss": 511 + offset_ss,
                "max_fs": 511 + offset_fs,
            },
            "a4": {
                "min_ss": 256 + offset_ss,
                "min_fs": 0 + offset_fs,
                "max_ss": 511 + offset_ss,
                "max_fs": 255 + offset_fs,
            },
            "a5": {
                "min_ss": 0 + offset_ss,
                "min_fs": 768 + offset_fs,
                "max_ss": 255 + offset_ss,
                "max_fs": 1023 + offset_fs,
            },
            "a6": {
                "min_ss": 0 + offset_ss,
                "min_fs": 512 + offset_fs,
                "max_ss": 255 + offset_ss,
                "max_fs": 767 + offset_fs,
            },
            "a7": {
                "min_ss": 0 + offset_ss,
                "min_fs": 256 + offset_fs,
                "max_ss": 255 + offset_ss,
                "max_fs": 511 + offset_fs,
            },
            "a8": {
                "min_ss": 0 + offset_ss,
                "min_fs": 0 + offset_fs,
                "max_ss": 255 + offset_ss,
                "max_fs": 255 + offset_fs,
            },
        }
    }


def get_500k_slab_inverted(slab_name: str, offset_ss: int, offset_fs: int) -> dict:
    """
    This function creates a Jungfrau panel of 500k pixels with the first pixel (of the first row) positioned at the bottom-right corner of the slab. The panel can be translated from the origin by specifying offsets along the slow-scan and fast-scan axes.

    Args:
        slab_name (str): Identification of the panel or slab.
        offset_ss (int): Number of indices to offset the panel along the slow-scan axis.
        offset_fs (int): Number of indices to offset the panel along the fast-scan axis.

    Returns:
        panel (dict): A dictionary containg the panel identification and its slow-scan and fast-scan limits in the hyperslab.

    """
    return {
        f"{slab_name}": {
            "a1": {
                "min_ss": 0 + offset_ss,
                "min_fs": 0 + offset_fs,
                "max_ss": 255 + offset_ss,
                "max_fs": 255 + offset_fs,
            },
            "a2": {
                "min_ss": 0 + offset_ss,
                "min_fs": 256 + offset_fs,
                "max_ss": 255 + offset_ss,
                "max_fs": 511 + offset_fs,
            },
            "a3": {
                "min_ss": 0 + offset_ss,
                "min_fs": 512 + offset_fs,
                "max_ss": 255 + offset_ss,
                "max_fs": 767 + offset_fs,
            },
            "a4": {
                "min_ss": 0 + offset_ss,
                "min_fs": 768 + offset_fs,
                "max_ss": 255 + offset_ss,
                "max_fs": 1023 + offset_fs,
            },
            "a5": {
                "min_ss": 256 + offset_ss,
                "min_fs": 0 + offset_fs,
                "max_ss": 511 + offset_ss,
                "max_fs": 255 + offset_fs,
            },
            "a6": {
                "min_ss": 256 + offset_ss,
                "min_fs": 256 + offset_fs,
                "max_ss": 511 + offset_ss,
                "max_fs": 511 + offset_fs,
            },
            "a7": {
                "min_ss": 256 + offset_ss,
                "min_fs": 512 + offset_fs,
                "max_ss": 511 + offset_ss,
                "max_fs": 767 + offset_fs,
            },
            "a8": {
                "min_ss": 256 + offset_ss,
                "min_fs": 768 + offset_fs,
                "max_ss": 511 + offset_ss,
                "max_fs": 1023 + offset_fs,
            },
        }
    }


def get_slab_coordinates_in_hyperslab(
    slab_name: str, asic_name: str, key: str, detector_layout: dict
) -> int:
    """
    This function return the value of a key (`min_ss`, `max_ss`, `min_fs` or `max_fs`) from one detector layout dictionary, a slab identification and an asic identification.

    Returns:
        value (int): Value of the slow-scan and fast-scan limits in the hyperslab for a given detector layout, panel and asic.
    """

    return detector_layout[f"{slab_name}"][f"{asic_name}"][f"{key}"]


def create_simple_vds(input_file: str, data_hdf5_path: str, output_file: str):
    """
    This function shows an example how to create a file in the VDS format pointing a virtual dataset to a source. For European XFEL users there is a function in the [Extra-data library](https://rtd.xfel.eu/docs/data-analysis-user-documentation/en/latest/software/hdf5-virtualise/#how-to-make-virtual-cxi-data-files) to create VDS files of the measured runs.

    Args:
        input_file (str): Path to the source file.

        data_hdf5_path (str): HDF5 path to the data in the source file.

        output_file (str): Path to the VDS file.

    """
    with h5py.File(input_file, "r") as g:
        shape = g[data_hdf5_path].shape
        layouts = h5py.VirtualLayout(shape, dtype=np.int32)
        vsrc = h5py.VirtualSource(input_file, data_hdf5_path, shape)
        layouts[...] = vsrc

    with h5py.File(output_file, "w", libver=("v110", "v110")) as f:
        f.create_dataset("cxi_version", data=[150])
        dgrp = f.create_group("entry/data")
        data = dgrp.create_virtual_dataset("data", layouts)
