# Run Scripts for Microgrid Planner

## File Organization

    ├── simulate                            <- Scripts to run simulate methods
    ├── sizing                              <- Scripts to run sizing methods
    ├── archive_results.sbatch              <- Slurm script to archive a specified directory on an HPC server
    ├── compute_sbatch_wrapper.sh.template  <- Bash script template to submit compute jobs to Slurm
    ├── helpers.py                          <- global variables and functions used by run scripts

## Parameter files

- `compute.yml.template` are templates to pass options to `*/compute.py` when running in offline mode (not through web app), using the `-c` command line option (copy these to *.yml to use)
