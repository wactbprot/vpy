# How to generate simulated se3 calibration data

Change to `vpy` root dir and activate the venv:
```shell
cd vpy
source bin/activate
```

Edit the config file `script/se3/sim_config.json`. Run:

```shell
python script/se3/sim_gen_data.py
python script/se3/sim_cal_data.py
python script/se3/sim_plot_data.py
python script/se3/sim_latex_table.py
```

If there is something new in the base docs
(e.g. `constants`, `std-se3` etc.) run:

```shell
python script/se3/sim_base_doc.py
```
