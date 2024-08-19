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

def expand_data_to_hyperslab(data:np.array, format: str)-> np.array:
    # TO TEST
    if format=="vds_spb_jf4m":
        hyperslab=np.zeros((2048,2048), np.int32)
        expected_shape = (8, 512, 1024) 
        if data.shape != expected_shape:
            raise ValueError(f"Data shape for {format} format not in expected shape: {expected_shape}.")
    else:
        raise NameError("Unknown data format.")

    ## Concatenate panels in one hyperslab keep the order break after panel 4 to second column, as described here: https://extra-geom.readthedocs.io/en/latest/jungfrau_geometry.html. 
    for panel_id, panel in enumerate(data):
        if panel_id<4:
            hyperslab[512*panel_id:512*(panel_id+1),0:1024]=panel
        else:
            if panel_id==4:
                hyperslab[512*(-panel_id+3):,1024:2048]=panel 
            else:
                hyperslab[512*(-panel_id+3):512*(-panel_id+4),1024:2048]=panel

    return hyperslab

def translate_geom_to_hyperslab(geometry_filename:str)-> str:
    # TO TEST
    output_file = geometry_filename.split(".geom")[0]+"_hyperslab.geom"
    lines = open(geometry_filename, "r").readlines()
    input_geom.close()
    
    jf_4m_hyperslab = slab_to_hyperslab()

    f = open(output_file, "w")
    
    for line in lines:
        key = line.split("=")[0]
        value = int(line.split("=")[1])
        key_parts = key.split("/")
        if len(key_parts)>1 and  key_parts[1] in ("min_ss", "min_fs", "max_ss", "max_fs"):
            new_value = get_slab_coordinates_in_hyperslab(panel_name=key_parts[0], key=key_parts[1], value=value, detector=jf_4m_hyperslab)
            f.write(f"{key} = {new_value}")
        else:
            f.write(line)
    f.close()

def slab_to_hyperslab()->dict:
    # TO TEST
    jf_4m_in_hyperslab = {}
    slab_name = p1
    jf_4m_in_hyperslab.update(get_500k_slab(slab_name, 0, 0))
    slab_name = p2
    jf_4m_in_hyperslab.update(get_500k_slab(slab_name, 512, 0))
    slab_name = p3
    jf_4m_in_hyperslab.update(get_500k_slab(slab_name, 1024, 0))
    slab_name = p4
    jf_4m_in_hyperslab.update(get_500k_slab(slab_name, 1536, 0))
    slab_name = p5
    jf_4m_in_hyperslab.update(get_500k_slab(slab_name, 1536, 1024))
    slab_name = p6
    jf_4m_in_hyperslab.update(get_500k_slab(slab_name, 1024, 1024))
    slab_name = p7
    jf_4m_in_hyperslab.update(get_500k_slab(slab_name, 512, 1024))
    slab_name = p8
    jf_4m_in_hyperslab.update(get_500k_slab(slab_name, 0, 1024))

def get_500k_slab(slab_name: str, offset_ss:int, offset_fs:int)->dict:
    # TO TEST
    return {
        f"{panel_name}": {
            "a1": {
                "min_ss": 256 + offset_ss,
                "min_fs": 768 + offset_fs,
                "max_ss": 511 + offset_ss,
                "max_fs": 1023 + offset_fs
            }
            "a2": {
                "min_ss": 256  + offset_ss,
                "min_fs": 512  + offset_fs,
                "max_ss": 511  + offset_ss,
                "max_fs": 767  + offset_fs
            }
            "a3": {
                "min_ss": 256  + offset_ss,
                "min_fs": 256  + offset_fs,
                "max_ss": 511  + offset_ss,
                "max_fs": 511  + offset_fs
            }
            "a4": {
                "min_ss": 256  + offset_ss,
                "min_fs": 0  + offset_fs,
                "max_ss": 511  + offset_ss,
                "max_fs": 255  + offset_fs
            }
            "a5": {
                "min_ss": 0  + offset_ss,
                "min_fs": 768  + offset_fs,
                "max_ss": 255  + offset_ss,
                "max_fs": 1023  + offset_fs
            }
            "a6": {
                "min_ss": 0  + offset_ss,
                "min_fs": 512  + offset_fs,
                "max_ss": 255  + offset_ss,
                "max_fs": 767  + offset_fs
            }
            "a7": {
                "min_ss": 0 + offset_ss,
                "min_fs": 256  + offset_fs,
                "max_ss": 255  + offset_ss,
                "max_fs": 511  + offset_fs
            }
            "a8": {
                "min_ss": 0  + offset_ss,
                "min_fs": 0  + offset_fs,
                "max_ss": 255  + offset_ss,
                "max_fs": 255  + offset_fs
            }
        }
    }

def get_slab_coordinates_in_hyperslab(slab_name:str, key:str, detector:dict) -> int:
    # TODO