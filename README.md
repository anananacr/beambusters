# beambusters

[![PyPI pyversions](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/release/python-3100/)

Beambusters is an application developed to determine the detector center directly from still diffraction patterns collected in serial crystallography experiments.

Beambusters uses the methods implemented in bblib to calculate the detector center shift in each diffraction pattern, according to your initial detector geometry (CrystFEL format).

You can find more information about bblib on [this page](https://anananacr.github.io/bblib/).

## Installation

To install beambusters, run the following command in a terminal:

```bash
pip install beambusters
```

## Usage

To run beambusters, use the following command in your terminal:

```bash
beambusters run_centering /path/to/list/file /path/to/config/file
```

The configuration file uses the YAML format. An example of a configuration file can be found [on this page](https://anananacr.github.io/beambusters/example/config/#example).


## Contact

Ana Carolina Rodrigues led the development of Beambusters from 2021 to 2025 at the Deutsches Elektronen-Synchrotron (DESY) in Hamburg, Germany.

For questions, please contact:

**Email**: sc.anarodrigues@gmail.com
