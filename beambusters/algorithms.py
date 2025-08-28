"""
This module defines the algorithms used to process the data.
"""

from bblib.methods import CenterOfMass, FriedelPairs, CircleDetection, MinimizePeakFWHM
from beambusters.utils import centering_converged
import numpy as np
import math
from bblib.models import PF8, PF8Info


def calculate_detector_center_on_a_frame(
    calibrated_data: np.array, memory_cell_id: int, config: dict, PF8Config: PF8Info
) -> list:
    """
    Calculate the detector center on a frame.

    Args:
        calibrated_data (np.array): The data in which the center determination will be performed.

        memory_cell_id (int): The memory cell id of the frame, only necessary when operating in storage cell mode.

        config (dict): A configuration dictionary in the format expected by beambusters.

        PF8Config (PF8Info): Peakfinder8 parameters.

    Returns:
        results (list): A list with the calculated detector center shit in x and y in mm, if it is a hit, if it was pre-centered and if the center was refined.
    """
    plots_info = {"filename": "", "folder_name": "", "root_path": ""}
    config["plots_flag"] = False

    if "center_of_mass" not in config["skip_centering_methods"]:
        center_of_mass_method = CenterOfMass(
            config=config, PF8Config=PF8Config, plots_info=plots_info
        )
        detector_center_from_center_of_mass = center_of_mass_method(
            data=calibrated_data
        )
    else:
        detector_center_from_center_of_mass = [-1, -1]
    if "circle_detection" not in config["skip_centering_methods"]:
        for rank in range(config["hough"]["maximum_rank"]):
            config["hough_rank"] = rank
            circle_detection_method = CircleDetection(
                config=config, PF8Config=PF8Config, plots_info=plots_info
            )
            detector_center_from_circle_detection = circle_detection_method(
                data=calibrated_data
            )

            ## Calculate distance from the calculated center to the reference point in each axis
            distance_in_x = math.sqrt(
                (
                    detector_center_from_circle_detection[0]
                    - config["reference_center"]["x"]
                )
                ** 2
            )

            distance_in_y = math.sqrt(
                (
                    detector_center_from_circle_detection[1]
                    - config["reference_center"]["y"]
                )
                ** 2
            )

            if (
                distance_in_x < config["hough"]["outlier_distance"]["x"]
                and distance_in_y < config["hough"]["outlier_distance"]["y"]
            ):
                break
        ## Check for the case where rank reached the maximum value and the detector center is not within the allowed region
        else:
            detector_center_from_circle_detection = [-1, -1]
    else:
        detector_center_from_circle_detection = [-1, -1]
    if "minimize_peak_fwhm" not in config["skip_centering_methods"]:
        minimize_peak_fwhm_method = MinimizePeakFWHM(
            config=config, PF8Config=PF8Config, plots_info=plots_info
        )
        detector_center_from_minimize_peak_fwhm = minimize_peak_fwhm_method(
            data=calibrated_data, initial_guess=detector_center_from_circle_detection
        )
    else:
        detector_center_from_minimize_peak_fwhm = [-1, -1]

    ## Define the initial_guess
    initial_guess = [-1, -1]
    pre_centering_flag = 0
    is_a_hit = 0
    refined_center_flag = 0

    if config["centering_method_for_initial_guess"] == "center_of_mass":
        calculated_detector_center = detector_center_from_center_of_mass
        distance_in_x = math.sqrt(
            (calculated_detector_center[0] - config["reference_center"]["x"]) ** 2
        )
        distance_in_y = math.sqrt(
            (calculated_detector_center[1] - config["reference_center"]["y"]) ** 2
        )

        if (
            distance_in_x < config["outlier_distance"]["x"]
            and distance_in_y < config["outlier_distance"]["y"]
        ):
            pre_centering_flag = 1
            initial_guess = detector_center_from_center_of_mass
    elif config["centering_method_for_initial_guess"] == "circle_detection":
        calculated_detector_center = detector_center_from_circle_detection
        distance_in_x = math.sqrt(
            (calculated_detector_center[0] - config["reference_center"]["x"]) ** 2
        )
        distance_in_y = math.sqrt(
            (calculated_detector_center[1] - config["reference_center"]["y"]) ** 2
        )
        if (
            distance_in_x < config["outlier_distance"]["x"]
            and distance_in_y < config["outlier_distance"]["y"]
        ):
            pre_centering_flag = 1
            initial_guess = detector_center_from_circle_detection
    elif config["centering_method_for_initial_guess"] == "minimize_peak_fwhm":
        calculated_detector_center = detector_center_from_minimize_peak_fwhm
        distance_in_x = math.sqrt(
            (calculated_detector_center[0] - config["reference_center"]["x"]) ** 2
        )
        distance_in_y = math.sqrt(
            (calculated_detector_center[1] - config["reference_center"]["y"]) ** 2
        )

        if (
            distance_in_x < config["outlier_distance"]["x"]
            and distance_in_y < config["outlier_distance"]["y"]
        ):
            pre_centering_flag = 1
            initial_guess = detector_center_from_minimize_peak_fwhm
    elif config["centering_method_for_initial_guess"] == "manual_input":
        initial_guess = [
            config["manual_input"][f"{memory_cell_id}"]["x"],
            config["manual_input"][f"{memory_cell_id}"]["y"],
        ]

    # If the method chosen didn't converge change to the detector center from the geometry file
    if initial_guess[0] == -1 and initial_guess[1] == -1:
        initial_guess = PF8Config.detector_center_from_geom

    # Force center override the initial guess calculated to coordinates defined in config
    if config["force_center"]["state"]:
        if config["force_center"]["anchor_x"]:
            initial_guess[0] = config["force_center"]["x"]
        if config["force_center"]["anchor_y"]:
            initial_guess[1] = config["force_center"]["y"]

    # Compares if the calculated center is within the outlier distance in each axis
    distance_in_x = math.sqrt((initial_guess[0] - config["reference_center"]["x"]) ** 2)
    distance_in_y = math.sqrt((initial_guess[1] - config["reference_center"]["y"]) ** 2)

    # Start refine the detector center by FriedelPairs
    center_is_refined = False

    if (
        distance_in_x < config["outlier_distance"]["x"]
        and distance_in_y < config["outlier_distance"]["y"]
    ):

        ## Ready for detector center refinement
        PF8Config.update_pixel_maps(
            initial_guess[0] - PF8Config.detector_center_from_geom[0],
            initial_guess[1] - PF8Config.detector_center_from_geom[1],
        )
        pf8 = PF8(PF8Config)
        peak_list = pf8.get_peaks_pf8(data=calibrated_data)

        if config["vds_format"] and config["vds_id"] == "vds_spb_jf4m":
            geometry_filename = (
                config["geometry_file"].split(".geom")[0] + "_hyperslab.geom"
            )
        else:
            geometry_filename = config["geometry_file"]

        PF8Config.set_geometry_from_file(geometry_filename)

        if (
            "friedel_pairs" not in config["skip_centering_methods"]
            and peak_list["num_peaks"] > config["pf8"]["min_num_peaks"]
        ):
            is_a_hit = 1
            friedel_pairs_method = FriedelPairs(
                config=config, PF8Config=PF8Config, plots_info=plots_info
            )
            detector_center_from_friedel_pairs = friedel_pairs_method(
                data=calibrated_data, initial_guess=initial_guess
            )
            if centering_converged(detector_center_from_friedel_pairs):
                center_is_refined = True
            else:
                center_is_refined = False
    else:
        center_is_refined = False
    ## Refined detector center assignement
    if center_is_refined:
        refined_detector_center = detector_center_from_friedel_pairs
        refined_center_flag = 1
    else:
        refined_detector_center = initial_guess

    # Global offset
    if "offset" in config:
        if "x" in config["offset"]:
            refined_detector_center[0] += config["offset"]["x"]
        if "y" in config["offset"]:
            refined_detector_center[1] += config["offset"]["y"]

    beam_position_shift_in_pixels = [
        refined_detector_center[x] - PF8Config.detector_center_from_geom[x]
        for x in range(2)
    ]

    detector_shift_in_mm = [
        np.round(-1 * x * 1e3 / PF8Config.pixel_resolution, 4)
        for x in beam_position_shift_in_pixels
    ]
    detector_shift_x_in_mm = detector_shift_in_mm[0]
    detector_shift_y_in_mm = detector_shift_in_mm[1]

    return [
        detector_shift_x_in_mm,
        detector_shift_y_in_mm,
        is_a_hit,
        pre_centering_flag,
        refined_center_flag,
    ]
