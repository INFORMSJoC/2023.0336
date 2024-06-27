# Run scripts

- `old/sizing.py` performs rightsizing method of Reich & Oriti (2021); not integrated in web app
- `sizing.py` sizing method of Reich (202?) integrated in web app
- `sizing.sbatch` wrapper to run `sizing.py` on Slurm


# Parameter files

- `sizing.yml.template` is a template to pass options to `sizing.py` when running in offline mode (not through web app), using the `-c` command line option (copy these to *.yaml to use)


# Reproduce computational results in Reich (202?)

Build database with data
- `python3.9 make_data.py --data_paper`

3-DER instance (change `-n` to number of levels reported)
- `python3.9 run/sizing/sizing.py -g 250 -p 1 -s 2020-09-01_00:00:00 -a exact -n 6`
- `python3.9 run/sizing/sizing.py -g 250 -p 1 -s 2020-09-01_00:00:00 -a heuristic -n 11`

4-DER instance (change `-n` to number of levels reported)
- `python3.9 run/sizing/sizing.py -g 251 -p 1 -s 2020-09-01_00:00:00 -a exact -n 6`
- `python3.9 run/sizing/sizing.py -g 251 -p 1 -s 2020-09-01_00:00:00 -a heuristic -n 11`

To run instances on Slurm, use instead, e.g.,
- `squb run/sizing/sizing.sbatch -g 250 -p 1 -s 2020-09-01_00:00:00 -a exact -n 6`

To produce the comparison set of results from Reich & Oriti (2021)
- `python3.9 run/sizing/old/sizing.py`
