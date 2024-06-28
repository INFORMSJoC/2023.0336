# Backend Application for Microgrid Planner

## File Organization

    ├── api                             <- Flask app for API
    ├── data                            <- Data and SQL scripts
    ├── make                            <- Script and configuration file template for building all databases required
    ├── run                             <- Scripts for running mathematical models and compiling results
    │   └── README                      <- See README file for more details on available scripts
    ├── src                             <- Source code for use in this project
    │   ├── components                  <- Classes for components of electrical system
    │   ├── data                        <- Classes for data and data processing scripts
    │   ├── grid                        <- Classes for microgrid
    │   ├── models                      <- Classes for mathematical models
    │   ├── reports                     <- Classes for summarizing model outputs 
    │   ├── utils                       <- Helper classes and functions
    │   └── visualization               <- Classes for visualizations
    ├── config.ini.template             <- Configuration file template (copy to config.ini and update parameter values)
    ├── database-microgrid.env.template <- MySQL microgrid database configuration file template (copy to database-microgrid.env and update parameter values)
    ├── database-weather.env.template   <- MySQL weather database configuration file template (copy to database-weather.env and update parameter values)
    ├── Dockerfile.template             <- Command-line instructions for building a Docker image and running the API (copy to Dockerfile)
    ├── README                          <- Documentation
    ├── requirements.txt                <- Python imports to be installed using `pip` to run api web app or scripts in run folder offline
    └── setup.py                        <- Configuration file for frontend app

## Instructions

1. Create configuration files, per instructions below
    - `config.ini`
        - `DEFAULT` section defines directory on local machine for run scripts to generate output files
        - `SECURITY` section defines an `ADMIN_PASSWORD` for login to the application as the administrator (overwrites the one in `data/mysql/data.sql`)
        - `API` section defines the settings for running the API web server
        - `QUOTA` section defines user limits
        - `SSH` section defines location of ssh key file for authenticating to the SLURM server
        - `SLURM` section defines the configuration for running computing jobs on Slurm
    - `database-microgrid.env`
        - `MYSQL_ROOT_PASSWORD` may have been set when setting up the MYSQL database
        - `MYSQL_USER`, `MYSQL_PASSWORD` and `MYSQL_DATABASE` can be set to any values
        - `MYSQL_PORT` should be set to `3306`
        - `MYSQL_HOST` should be set to `127.0.0.1` or `localhost` or when running Docker to `mysql`
    - `database-weather.env`
        - `MYSQL_ROOT_PASSWORD` may have been set when setting up the MYSQL database
        - `MYSQL_USER`, `MYSQL_PASSWORD` and `MYSQL_DATABASE` can be set to any values
        - `MYSQL_PORT` should be set to `3306`
        - `MYSQL_HOST` should be set to `127.0.0.1` or `localhost` or when running Docker to `mysql`
    - `data/csv/weather/locations.csv`
        - should contain a record for each location in `data/csv/weather/nsrdb-api-formatted-files/`
2. Download additional locations for the weather database
    - see `data/csv/weather/README.md` for instructions
3. Review `run/README.md` for instructions on running analytical methods

## Instructions for Slurm

1. Place a copy of the project in your high-performance computing account
2. From a compute node, create a virtual environment and install the backend
    - `module load lang/python/3.11.2`
    - `python -m venv ~/virtual_env/microgrid` (after creating `virtual_env` directory in your home folder)
    - `source ~/virtual_env/microgrid/bin/activate`
    - From the `backend` directory, run `pip install .` (use `-e` flag for development)
3. Copy `run/compute_sbatch_wrapper.sh.template` to `run/compute_sbatch_wrapper.sh`, update `#SBATCH` settings and virtual environment reference

## Instructions to Run Locally

The following commands must be run from inside the `backend` directory:
1. Run `pip3 install .` (use `-e` flag for development)
2. Run `python -m pytest tests/` to ensure application is working
3. Run `python3 api/app.py` to start web server
4. For development, you may wish to manually build databases with test data
    - `make/make_data.yaml` update values as required
    - Run `python3 make/make_data.py -c make/make_data.yaml`
    - Note: password values in `data/mysql/*data*.sql` are stored in plain text and are automatically hashed with the secret key in the root `config.ini` when the database is created using `make_data`
5. Scripts in the `run` directory are executable, e.g., `python3 run/compute.py -m "simulate" -c run/simulate/compute.yml`
