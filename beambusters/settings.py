import yaml
from pathlib import Path
import sys
from bblib.models import PF8Info


def read(path: str) -> dict:
    path = Path(path)
    config = path.read_text()
    config = yaml.safe_load(config)
    return config


def parse(config: dict) -> dict:

    return {
        "pf8_max_num_peaks": config["pf8"]["max_num_peaks"],
        "pf8_adc_threshold": config["pf8"]["adc_threshold"],
        "pf8_minimum_snr": config["pf8"]["minimum_snr"],
        "pf8_min_pixel_count": config["pf8"]["min_pixel_count"],
        "pf8_max_pixel_count": config["pf8"]["max_pixel_count"],
        "pf8_local_bg_radius": config["pf8"]["local_bg_radius"],
        "pf8_min_res": config["pf8"]["min_res"],
        "pf8_max_res": config["pf8"]["max_res"],
        "min_peak_region": config["peak_region"]["min"],
        "max_peak_region": config["peak_region"]["max"],
        "canny_sigma": config["canny"]["sigma"],
        "canny_low_thr": config["canny"]["low_threshold"],
        "canny_high_thr": config["canny"]["high_threshold"],
        "outlier_distance": config["outlier_distance"],
        "search_radius": config["search_radius"],
        "centering_method_for_initial_guess": config[
            "centering_method_for_initial_guess"
        ],
        "bragg_peaks_positions_for_center_of_mass_calculation": config[
            "bragg_peaks_positions_for_center_of_mass_calculation"
        ],
        "pixels_for_mask_of_bragg_peaks": config["pixels_for_mask_of_bragg_peaks"],
        "skipped_centering_methods": config["skip_centering_methods"],
        "polarization_apply": config["polarization"]["apply_polarization_correction"],
        "polarization_axis": config["polarization"]["axis"],
        "polarization_value": config["polarization"]["value"],
        "offset_x": config["offset"]["x"],
        "offset_y": config["offset"]["y"],
        "force_center_state": config["force_center"]["state"],
        "force_center": [config["force_center"]["x"], config["force_center"]["y"]],
        "force_center_in_x": config["force_center"]["anchor_x"],
        "force_center_in_y": config["force_center"]["anchor_y"],
        "reference_center": [
            config["reference_center"]["x"],
            config["reference_center"]["y"],
        ],
        "output_path": config["output_path"],
        "geometry_file": config["geometry_file"],
        "burst_mode_active": config["burst_mode"]["is_active"],
        "burst_mode_storage_cell_hdf5_path": config["burst_mode"][
            "storage_cell_hdf5_path"
        ],
        "burst_mode_debug_hdf5_path": config["burst_mode"]["debug_hdf5_path"],
    }


def get_pf8_info(config: dict):
    return PF8Info(
        max_num_peaks=config["pf8"]["max_num_peaks"],
        adc_threshold=config["pf8"]["adc_threshold"],
        minimum_snr=config["pf8"]["minimum_snr"],
        min_pixel_count=config["pf8"]["min_pixel_count"],
        max_pixel_count=config["pf8"]["max_pixel_count"],
        local_bg_radius=config["pf8"]["local_bg_radius"],
        min_res=config["pf8"]["min_res"],
        max_res=config["pf8"]["max_res"],
    )


def parse_plots_info(config: dict) -> dict:
    return {
        "file_name": config["plots"]["file_name"],
        "folder_name": config["plots"]["folder_name"],
        "root_path": config["plots"]["root_path"],
        "value_auto": config["plots"]["value_auto"],
        "value_max": config["plots"]["value_max"],
        "value_min": config["plots"]["value_min"],
        "axis_lim_auto": config["plots"]["axis_lim_auto"],
        "xlim_min": config["plots"]["xlim_min"],
        "xlim_max": config["plots"]["xlim_max"],
        "ylim_min": config["plots"]["ylim_min"],
        "ylim_max": config["plots"]["ylim_max"],
        "color_map": config["plots"]["color_map"],
    }
