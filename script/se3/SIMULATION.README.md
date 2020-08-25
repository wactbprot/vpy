# How to build simulated se3 calibration data

Change to vpy root dir activate the venv:
```shell
cd vpy
source bin/activate
```
If there is something new in in the base docs (e.g. `constants`, `std-se3` etc.):

```shell
python script/se3/sim_base_doc.py
```

Change the list of target pressures in
`script/se3/sim_gen_data.py`. Save script  and run:

```shell
python script/se3/sim_gen_data.py
```

Recalculate the simulation pressures and uncertainties by:

```shell
python script/se3/sim_cal_data.py -s
```
The `-s` flag saves a document with the id `"cal-sim-se3"`. Use this document to generate a plot by:

```shell
python script/se3/sim_plot_data.py
```
