from beambusters.algorithms import calculate_detector_center_on_a_frame
import numpy as np
import os
from beambusters.settings import read, get_pf8_info

def test_calculate_detector_center_on_a_frame():
    calibrated_data = np.random.randint(0,255,(1,1024,1024))
    memory_cell_id = 0
    bb_path = os.getcwd()
    config = read(f"{bb_path}/docs/example/config_test.yaml")
    PF8Config = get_pf8_info(config)
    geometry_filename = config["geometry_file"]
    PF8Config.set_geometry_from_file(geometry_filename)
    center = calculate_detector_center_on_a_frame(calibrated_data=calibrated_data[0], memory_cell_id=memory_cell_id, config = config, PF8Config=PF8Config)
    assert isinstance(center, list)
