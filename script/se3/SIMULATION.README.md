# How to build simulated se3 calibration data

Change to vpy root dir:
```shell
cd vpy
```
If there is something new in in the base docs (e.g. `constants`, `std-se3` etc.):

```shell
python script/se3/gen_base_doc.py
```

Change the list of target pressures in
`script/se3/gen_sim_data.py`. Save script  and run:

```shell
python script/se3/gen_sim_data.py
```

recalculate pressures and uncertainties by:

```shell
python script/se3/cal_sim_data.py -s
```

This saves a document with the id `"se3-sim"`. Use this document to generate a plot by:

```shell
python script/se3/plot_sim_data.py
```
