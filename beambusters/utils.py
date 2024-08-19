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
    if format=="vds_spb_jf4m":
        hyperslab=np.zeros((2048,2048))
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