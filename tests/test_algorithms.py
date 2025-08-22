from beambusters.algorithms import calculate_detector_center_on_a_frame
import numpy as np
from bblib.models import PF8Info

config = {
    "plots_flag": False,
	"search_radius": 10,
	"force_center": {
	    "state": False
	},
	"offset": {
		"x": 0,
		"y": 0
		},
	"reference_center": {
		"x": 50,
		"y": 50
		},
	"outlier_distance": {
	    "x": 50,
		"y": 50
	    },
	"peak_region":{
		"min": 100,
		"max": 140
		},
	"canny":{
		"sigma": 10,
		"low_threshold": 0.5,
		"high_threshold": 0.99
		},
	"hough": {
	    "maximum_rank": 1,
		"outlier_distance":
		    {
			"x": 10,
			"y": 10
			}
	},
	"centering_method_for_initial_guess": "circle_detection",
	"bragg_peaks_positions_for_center_of_mass_calculation": -1,
	"pixels_for_mask_of_bragg_peaks": 1,
	"polarization": {
		"apply_polarization_correction": False,
		"axis": "x",
		"value": 0.99
		},
	"skip_centering_methods": ["minimize_peak_fwhm"]
    }

def test_calculate_detector_center_on_a_frame():
    calibrated_data = np.random.randint(0,255,(1024,1024))
    memory_cell_id = 0
    PF8Config = PF8Info()
    geometry_filename = f"example/simple.geom"
    PF8Config.set_geometry_from_file(geometry_filename)
    center = calculate_detector_center_on_a_frame(calibrated_data=calibrated_data, memory_cell_id=memory_cell_id, config = config, PF8Config=PF8Config)
    assert isinstance(center, list)
