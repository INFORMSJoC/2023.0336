[![INFORMS Journal on Computing Logo](https://INFORMSJoC.github.io/logos/INFORMS_Journal_on_Computing_Header.jpg)](https://pubsonline.informs.org/journal/ijoc)

# Microgrid Planner: An Open-Source Software Platform

This archive is distributed in association with the [INFORMS Journal on
Computing](https://pubsonline.informs.org/journal/ijoc) under the [MIT License](LICENSE).

The software and data in this repository are a snapshot of the software and data
that were used in the research reported on in the paper 
[Microgrid Planner: An Open-Source Software Platform](https://doi.org/10.1287/ijoc.2023.0336) by D. Reich and L. Frye. 
The snapshot is based on 
[this SHA](https://github.com/reichd/MicrogridPlanner/commit/ee1f8189a80d0d293a6d66633558562473c533f0) 
in the development repository.

**Important: This code is being developed on an on-going basis at 
https://github.com/reichd/MicrogridPlanner. Please go there if you would like to
get a more recent version or you would like to request support.**

## Cite

To cite the contents of this repository, please cite both the paper "Microgrid Planner: An Open-Source Software Platform" and this repo, using their respective DOIs.

https://doi.org/10.1287/ijoc.2023.0336

https://doi.org/10.1287/ijoc.2023.0336.cd

Below is the BibTex for citing this snapshot of the repository.

```
@misc{MicrogridPlanner,
  author =        {Reich, Daniel and Frye, Leah},
  publisher =     {INFORMS Journal on Computing},
  title =         {{Microgrid Planner: An Open-Source Software Platform}},
  year =          {2024},
  doi =           {10.1287/ijoc.2023.0336.cd},
  url =           {https://github.com/INFORMSJoC/2023.0336},
  note =          {Available for download at https://github.com/INFORMSJoC/2023.0336},
}  
```

## Description

The goal of this software is to deploy analytical methods for microgrid planning.

## File Organization

    ├── data                            <- Data and SQL scripts
    ├── run                             <- Scripts for running mathematical models and compiling results
    │   └── README                      <- See README file for more details on available scripts
    ├── src                             <- Source code for use in this project.
    │   ├── components                  <- Classes for components of electrical system
    │   ├── data                        <- Classes for data and data processing scripts
    │   ├── grid                        <- Classes for microgrid
    │   ├── models                      <- Classes for mathematical models 
    │   ├── reports                     <- Classes for summarizing model outputs
    │   ├── utils                       <- Helper classes and functions
    │   └── visualization               <- Classes for visualizations
    ├── webapps
    │   ├── api                         <- Flask app for API
    │   └── frontend                    <- Flask app for GUI
    |
    ├── config.env.template             <- MySQL configuration file template (copy to config.env and update parameter values)
    ├── config.ini.template             <- Configuration file template (copy to config.ini and update parameter values)
    ├── docker-compose.yaml.template    <- Configuration file for Docker multi-container application services (copy to docker-compose.yaml)
    ├── Dockerfile-api.template         <- Command-line instructions for building a Docker image and running the API (copy to Dockerfile-api)
    ├── Dockerfile-frontend.template    <- Command-line instructions for building a Docker image and running the frontend web app (copy to Dockerfile-frontend)
    ├── LICENSE                         <- License terms
    ├── make_data.py                    <- Script to build databases and generate all processed data required
    ├── make_data.yaml.template         <- Settings for `make_data.py` (copy to make_data.yaml and update parameter values)
    ├── requirements-api.txt            <- Python imports to be installed using `pip` to run api web app or scripts in run folder offline
    └── requirements-fronted.txt        <- Python imports to be installed using `pip` to run frontend web app


## Instructions for Slurm

Note: web app may be run without Slurm, but functionality will be limited
1. Place a copy of the project in your high-performance computing account


## Instructions to Run Locally

1. Setup a **Python 3.9** environment for the run scripts (Note: **Python 3.10 and newer** break Matplotlib features) and API; and a **Python 3.11** environment for the frontend
2. Install all packages required, by executing `pip3.9 install -r requirements-api.txt` and `pip3.11 install -r requirements-frontend.txt`
3. Install **mysql**, add it to `${PATH}` and ensure it is running in the background
4. Run `export PYTHONPATH="${PYTHONPATH}:."` to add the project directory to your Python path
5. Create configuration files, per instructions below
    - `config.ini`
        - Generate `SECRET_KEY` by running `python3 make_data.py --secret_key`
    - `config.env`
        - `MYSQL_ROOT_PASSWORD`, `MYSQL_USER`, `MYSQL_PASSWORD` and `MYSQL_DATABASE` can be set to any values
        - `MYSQL_PORT` should be set to `3306`
        - `MYSQL_HOST` should be set to `localhost`
6. Build databases and generate data
    - `make_data.yaml` update values as required
    - Run `python3 make_data.py -c make_data.yaml`
    - Note: password values in `data/mysql/*data*.sql` are stored in plain text and are automatically hashed with the secret key in `config.ini` when the database is created using `make_data`
7. Scripts in the `run` directory are executable, but should be run from the root directory, e.g., `python3.9 run/simulate_grid.py`
8. To run the API, execute `python3.9 webapps/api/app.py` (if prior two steps are skipped, the API will build the database and generate the required data)
9. To run the frontend web app
    - Copy `webapps/frontend/static/js/paths.js.template` to `webapps/frontend/static/js/paths.js`
    - Update the API `server` address in `webapps/frontend/static/js/paths.js`
    - Execute `python3.11 webapps/frontend/app.py`


## Instructions to Deploy via Docker

1. Create configuration files, per instructions below
    - `config.ini`
        - Generate `SECRET_KEY` by running `python3 make_data.py --secret_key`
    - `config.env`, if using docker to run MySQL
        - `MYSQL_ROOT_PASSWORD`, `MYSQL_USER`, `MYSQL_PASSWORD` and `MYSQL_DATABASE` can be set to any values
        - `MYSQL_PORT` should be set to `3306`
        - `MYSQL_HOST` should be set to `database` or to `mysql` to match the container name in `docker-compose.yaml`
    - Copy `webapps/frontend/static/js/paths.js.template` to `webapps/frontend/static/js/paths.js`    
    - Update the API `server` address in `webapps/frontend/static/js/paths.js`, if required
2. For development and testing, you may wish to update the boolean parameter values passed to `make_data.microgrid_database` in `webapps/api/app.py`
3. Run `docker-compose up` (by default, Docker will run the docker-compose.yaml file) to run three containers for the API, frontend, and MySQL database server
4. Reset the `admin` account password to a secure one by logging into the app and using the graphical user interface
    - initial password is set in `data/mysql/data.sql`
