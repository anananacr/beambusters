import numpy as np
import h5py


def open_dark_and_gain_files(calibration_files_directory: str) -> tuple:
    calibration_config = open(
        f"{calibration_files_directory}/calibration_config.txt", "r"
    ).readlines()
    detector_type = [
        x.split(" = ")[-1][:-1]
        for x in calibration_config
        if x.split(" = ")[0] == "detector_type"
    ][0]
    if detector_type == "jungfrau1M":
        num_panels: int = 2
        pedestal_d0 = (
            calibration_files_directory
            + "/"
            + [
                x.split(" = ")[-1][:-1]
                for x in calibration_config
                if x.split(" = ")[0] == "pedestal_d0"
            ][0]
        )
        pedestal_d1 = (
            calibration_files_directory
            + "/"
            + [
                x.split(" = ")[-1][:-1]
                for x in calibration_config
                if x.split(" = ")[0] == "pedestal_d1"
            ][0]
        )
        gain_d0 = (
            calibration_files_directory
            + "/"
            + [
                x.split(" = ")[-1][:-1]
                for x in calibration_config
                if x.split(" = ")[0] == "gain_d0"
            ][0]
        )
        gain_d1 = (
            calibration_files_directory
            + "/"
            + [
                x.split(" = ")[-1][:-1]
                for x in calibration_config
                if x.split(" = ")[0] == "gain_d1"
            ][0]
        )
        dark_filenames = [pedestal_d0, pedestal_d1]
        gain_filenames = [gain_d0, gain_d1]
        dark = np.ndarray((3, 512 * num_panels, 1024), dtype=np.float32)
        gain = np.ndarray((3, 512 * num_panels, 1024), dtype=np.float64)
        panel_id: int

        for panel_id in range(num_panels):
            gain_file: BinaryIO = open(gain_filenames[panel_id], "rb")
            dark_file: Any = h5py.File(dark_filenames[panel_id], "r")
            gain_mode: int
            for gain_mode in range(3):
                dark[gain_mode, 512 * panel_id : 512 * (panel_id + 1), :] = dark_file[
                    "gain%d" % gain_mode
                ][:]
                gain[gain_mode, 512 * panel_id : 512 * (panel_id + 1), :] = np.fromfile(
                    gain_file, dtype=np.float64, count=1024 * 512
                ).reshape(512, 1024)
            gain_file.close()
            dark_file.close()
    else:
        raise NameError("Unrecognised detector.")        
    
    return dark, gain


def filter_data(data: np.ndarray) -> bool:
    """
    Filter JUNGFRAU 1M faulty images based on number of pixels at gain 2.

    Parameters
    ----------
    data: np.ndarray
        JUNGFRAU 1M single raw image

    Returns
    ----------
    bool
        True if file should be skipped before apply calibration
    """
    gain_3 = np.where(data & 2**15 > 0)
    counts_3 = gain_3[0].shape[0]
    if counts_3 > 1e3:
        return True
    else:
        return False


def apply_calibration(
    data: np.ndarray, dark: np.ndarray, gain: np.ndarray
) -> np.ndarray:
    """
    Applies the calibration to a JUNGFRAU 1M detector data frame.

    This function determines the gain stage of each pixel in the provided data
    frame, and applies the relevant gain and offset corrections.

    Parameters:

        data: The detector data frame to calibrate.

        dark: pedestals

        gain: gain maps
    Returns:

        The calibrated data frame.
    """
    calibrated_data: np.ndarray = data.astype(np.float32)

    where_gain: List[np.ndarray] = [
        np.where((data & 2**14 == 0) & (data & 2**15 == 0)),
        np.where((data & (2**14) > 0) & (data & 2**15 == 0)),
        np.where(data & 2**15 > 0),
    ]

    gain_mode: int

    if filter_data(data):
        return np.zeros((data.shape), dtype=np.int32)
    
    for gain_mode in range(3):
        calibrated_data[where_gain[gain_mode]] -= dark[gain_mode][
            where_gain[gain_mode]
        ]
        calibrated_data[where_gain[gain_mode]] /= gain[gain_mode][
            where_gain[gain_mode]
        ]
        calibrated_data[np.where(dark[0] == 0)] = 0
    
    return calibrated_data.astype(np.int32)
