# Frontend Application for Microgrid Planner

## File Organization

    ├── webapp                          <- Flask app for GUI
    ├── config.ini.template             <- Configuration file template (copy to config.ini and update parameter values)
    ├── Dockerfile.template             <- Command-line instructions for building a Docker image and running the app (copy to Dockerfile)
    ├── README                          <- Documentation
    ├── requirements.txt                <- Python imports to be installed using `pip` to run frontend web app
    └── setup.py                        <- Configuration file for frontend app

## Instructions

1. Create configuration files, per instructions below
    - `config.ini`
        - `JWT` section defines lifespan of authentication tokens
        - `AZURE` section enables authentication through Microsoft
        - `FRONTEND` section defines the settings for running the frontend web server
    - Copy `webapp/static/js/paths.js.template` to `webapp/static/js/paths.js`
    - Update the API `server` address in `webapp/static/js/paths.js`, if required

## Instructions to Run Locally

The following commands must be run from inside the `frontend` directory:
1. Run `pip3 install .` (use `-e` flag for development)
2. Run `python3 webapp/app.py` to start web server
