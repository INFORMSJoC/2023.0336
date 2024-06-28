-----------------
File Organization
-----------------

    ├── design_of_experiments   <- Scripts to generate designs (data) for any design of experiments
    │   └── sensitivity         <- Scripts to generate designs for sensitivity analysis
    ├── sensitivity             <- Scripts to run sensitivity analysis, compile and plot results
    ├── sizing                  <- Scripts to run sizing methods
    ├── archive_results.sbatch  <- Slurm script to archive a specified directory on an HPC server
    ├── helpers.py              <- global variables and functions used by run scripts
    ├── simulate_grid.py        <- Script to run a single simulation
