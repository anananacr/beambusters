# Configuration file

## Parameters description

The `config.yaml` file sets the configuration parameters of beambusters.

**geometry_file**: Absolute path to the geometry file. Type: str.

**output_hdf5_root_path**: Absolute path inside the hdf5 file to create a dataset with the output results. Type: str.

**chunks**: Number of frames in a chunk for parallel processing. Type: int

**number_of_processors**: Number of processors to use in parallel processing. Type: int.

**vds_format**: True if the file is saved in VDS format. Type: bool.

**vds_id**: Identification of which detector is being used. Currently it is supported `vds_spb_jf4m` and `generic`. Type: str.

**burst_mode**: Indicate if the detector is on burst mode.

  **state**: Burst or storage cell mode (true) or single cell mode (false). Type: bool.

  **storage_cell_hdf5_path**: Absolute HDF5 path to the storage cell id per frame. Type: str

**plots**:

  **flag**: Indicate if plots should be saved in intermediate steps (true) or not (false). Type: bool.

  **maximum_number_of_frames**: Number of frames to save plots. Type: int.

  **file_name**: The plots file name for saving. Type: str.

  **folder_name**: The plots folder name for saving. Type: str.

  **root_path**: Absolute path for the root directory for saving. Plots output are `/root_path/folder_name/*/file_name_*.png`. Type: str.

  **value_auto**: Control the automatic intensity adjustment of plots level (true). The normalization used is in logarithmic scale. Type: bool.

  **value_min**: If value_auto is false, minimum value of the intensity level should be passed. The normalization used is in logarithmic scale. Type: int.

  **value_max**: If value_auto is false, maximum value of the intensity level should be passed. The normalization used is in logarithmic scale. Type: int.

  **axis_lim_auto**: Control the automatic axis limits of the plots (true). Type: bool.

  **xlim_min**: If axis_lim_auto is false, minimum coordinate of the x axis should be passed. Type: int.

  **xlim_max**: If axis_lim_auto is false, maximum coordinate of the x axis should be passed. Type: int.

  **ylim_min**: If axis_lim_auto is false, minimum coordinate of the y axis should be passed. Type: int.

  **ylim_max**: If axis_lim_auto is false, maximum coordinate of the y axis should be passed. Type: int.

  **color_map**: Colormap preference for the plots, for example, viridis. Type: str.

  **marker_size**: Scatter marker size of center coordinates. Type: float.


**starting_frame**: Change the index of the starting frame, it will jump the first n images of the container file. Type: int.

**force_center**: Anchor the initial guess to a fixed point, if enabled this option will override other bblib pre-centering methods.

  **state**: Turn force mode on (true) or off (false). Type: bool.

  **anchor_x**: Turn force mode on (true) or off (false) for the x-axis. Type: bool.

  **anchor_y**: Turn force mode on (true) or off (false) for the y-axis. Type: bool.

  **x**: Initial guess pixel coordinates in x of the assembled data, i.e. image stored in a single array with the detector panels' geometric transformations applied, according to CrystFEL referential convention. Type: int.

  **y**: Initial guess pixel coordinates in y of the assembled data, i.e. image stored in a single array with the detector panels' geometric transformations applied, according to CrystFEL referential convention. Type: int.

**search_radius**: Search radius used in the FriedelPairs bblib method. Type: float.

**pf8**: peakfinder8 paratemers for Bragg peaks search. For more information, see the [Cheetah Documentation](https://www.desy.de/~barty/cheetah/Cheetah/SFX_hitfinding.html).
  **min_num_peaks**: Minimum number of peaks. Type: int.

  **max_num_peaks**: Maximum number of peaks. Type: int.

  **adc_threshold**: Arbitrary detector counts (ADC) threshold. Type: int.

  **minimum_snr**: Minimum signal-to-noise ratio (SNR). Type: float.

  **min_pixel_count**: Minimum number of pixels to consider a peak. Type: int.

  **max_pixel_count**: Maximum number of pixels to consider a peak. Type: int.

  **local_bg_radius**: Radius of the peaks local background, in pixels. Type: int.

  **min_res**: Minimum resolution region, in pixels. Type: int.

  **max_res**: Maximum resolution region, in pixels. Type: int.

**offset**: Add an offset to the final calculated detector center.

  **x**: Offset in x direction, in pixels. Type: float.

  **y**: Offset in y direction, in pixels. Type: float.

**peak_region**: Defines the approximate background peak distance from the center of the diffraction pattern, in pixels. This option is used in CircleDetection bblib pre-centering methods.

  **min**: Minimum distance, in pixels, of the background peak to the center of the diffraction pattern. Type: int.

  **max**: Maximum distance, in pixels, of the background peak to the center of the diffraction pattern. Type: int.

**outlier_distance**: Don't refine the detector center with FriedelPairs method if the distance from the initial_guess (in a certain axis) to the reference_center coordinates is bigger than the outlier_distance.

  **x**: Outlier distance in x. Type: float.

  **y**: Outlier distance in y. Type: float.

**reference_center**: Reference center of the diffraction pattern to filter outliers in the initial_guess calculation.

  **x**: Reference center pixel coordinates in x of the assembled data, i.e. image stored in a single array with the detector panels' geometric transformations applied, according to CrystFEL referential convention. Type: int.

  **y**: Reference center pixel coordinates in y of the assembled data, i.e. image stored in a single array with the detector panels' geometric transformations applied, according to CrystFEL referential convention. Type: int.

**canny**: Controls skimage.feature.canny function, used in the CircleDetection bblib method. For more information, see the [Scikit-image Documentation](https://scikit-image.org/docs/stable/auto_examples/edges/plot_circular_elliptical_hough_transform.html").

  **sigma**: Standard deviation of the Gaussian filter, used in the Canny function. Usually, 3 is good. Type: float.

  **low_threshold**: Lower bound for hysteresis thresholding (linking edges), as quantiles of the edge magnitude image. Threshold must be in the range [0, 1). Usually, 0.9 is good. Type: float.

  **high_threshold**: Upper bound for hysteresis thresholding (linking edges), as quantiles of the edge magnitude images. Threshold must be in the range [0, 1). Usually, 0.99 is good. Type: float.

**hough**:

  **maximum_rank**: Test up until the nth peak of the Hough Space, in order of decreasing voting number. Type: int.

  **outlier_distance**: If the ranked solution (from the most voted to the less voted) is within the outlier shift in x and y this solution is chosen as the detector center.

    x: Outlier shift in the x-axis. Type: int.

    y: Outlier shift in the y-axis. Type: int.

**centering_method_for_initial_guess**: Choose the bblib pre-centering method for the initial_guess assignment. The options available are `center_of_mass`, `circle_detection` or `manual_input`. Type: str.

**bragg_peaks_for_center_of_mass_calculation**: Choose if Bragg peaks should be masked out (0) from the image in the CenterOfMass bblib method, or use only the Bragg peaks (1), or use the image as it is (-1). Type: int

**pixels_for_mask_of_bragg_peaks**: Radius of the Bragg peaks, in pixels, to be masked in the pre-centering step. Type: int.

**grid_search_radius**: Radius of the square grid search region (in pixels) around the initial guess
used for the minimized peak FWHM centering method. Type: int.

**skip_centering_methods**: List of bblib pre-centering methods to be skipped. Options: `center_of_mass`, `circle_detection` , `minimize_peak_fwhm` or `friedel_pairs`. Type: List[str]

  - Method label you want to skip. Type: str.

**polarization**: Configure the polarization correction before refining the center in the FridelPairs bblib method.

  **apply_polarization_correction**: Aoply polarization correction (true) or not (false). Type: bool

  **axis**: Polarization axis direction. Options: `x` and `y`, as defined by the CrystFEL referential convention. Type: str.

  **value**: Polarization fraction in the axis direction. Type: float.


## Configuration file example

```yaml
geometry_file: /path/to/geom/detector.geom
output_hdf5_root_path: /entry/data

burst_mode:
  is_active: false
  storage_cell_hdf5_path: /entry/data/storage_cell_number

chunks: 500
number_of_processors: 16

vds_format: true
vds_id: generic

plots:
  flag: true
  maximum_number_of_frames: 50
  file_name: my_sample_label
  folder_name: run_label
  root_path: /path/to/plots
  value_auto: false
  value_min: 1e0
  value_max: 5e2
  axis_lim_auto: false
  xlim_min: 200
  xlim_max: 900
  ylim_min: 200
  ylim_max: 900
  color_map: viridis
  marker_size: 100

force_center:
  state: false
  anchor_x: true
  anchor_y: false
  x: 554
  y: 522

search_radius: 4.5

pf8:
  min_num_peaks: 1
  max_num_peaks: 10000
  adc_threshold: 100
  minimum_snr: 5
  min_pixel_count: 2
  max_pixel_count: 10000
  local_bg_radius: 5
  min_res: 0
  max_res: 600

starting_frame: 500

peak_region:
  min: 50
  max: 70

outlier_distance:
  x: 10
  y: 100

reference_center:
  x: 554
  y: 522

canny:
  sigma: 3
  low_threshold: 0.9
  high_threshold: 0.99

hough:
  maximum_rank:
  outlier_distance:
    x: 10
    y: 100

centering_method_for_initial_guess: circle_detection

bragg_peaks_for_center_of_mass_calculation: -1

pixels_for_mask_of_bragg_peaks: 4

grid_search_radius: 5

skip_centering_methods:
  - center_of_mass

polarization:
  apply_polarization_correction: true
  axis: x
  value: 0.99
```
