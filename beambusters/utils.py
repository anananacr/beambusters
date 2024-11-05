import sys
import h5py
import numpy as np


def centering_converged(center: tuple) -> bool:
    if center[0] == -1 and center[1] == -1:
        return False
    else:
        return True


def list_events(input_file: str, output_file: str, geometry_file: str):
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

    with h5py.File(f"{file_name}", "r") as f:
        num_events = (f[data_hdf5_path]).shape[0]

    events_list = np.arange(0, num_events, 1)

    return events_list, num_events


def expand_data_to_hyperslab(data: np.array, data_format: str) -> np.array:

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
    ## Jungfrau4M SPB EuXFEL
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
    return detector_layout[f"{slab_name}"][f"{asic_name}"][f"{key}"]


def create_simple_vds(input_file: str, data_hdf5_path: str, output_file: str):

    with h5py.File(input_file, "r") as g:
        shape = g[data_hdf5_path].shape
        layouts = h5py.VirtualLayout(shape, dtype=np.int32)
        vsrc = h5py.VirtualSource(input_file, data_hdf5_path, shape)
        layouts[...] = vsrc

    with h5py.File(output_file, "w", libver=("v110", "v110")) as f:
        f.create_dataset("cxi_version", data=[150])
        dgrp = f.create_group("entry/data")
        data = dgrp.create_virtual_dataset("data", layouts)
