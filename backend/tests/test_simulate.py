import pytest
from datetime import datetime
import src.data.mysql.simulate as database_simulate
import run.helpers as run_helpers

def test_simulate():

    # parameters for test
    user_id = 2 # system guest account
    grid_id = 4 # guest account grid with all component types
    energy_management_system_id = 1 # default energy management system
    powerload_id = 1 # guest account power load
    location_id = 145612 # Monterey, California
    startdatetime = datetime.strptime("2023-09-01_08:00:00", '%Y-%m-%d_%H:%M:%S')
    enddatetime = datetime.strptime("2023-09-01_10:30:00", '%Y-%m-%d_%H:%M:%S')

    # get database id of test case (returns None if test does not already exist)
    id = database_simulate.MODEL_HELPERS.result_get_by_params(
        grid_id = grid_id,
        energy_management_system_id = energy_management_system_id,
        powerload_id = powerload_id,
        location_id = location_id,
        startdatetime = startdatetime,
        enddatetime = enddatetime,
    )

    # if test already exists, delete it
    exists = False
    if id is not None:
        exists = True
        database_simulate.MODEL_HELPERS.remove(id)

    # add test into database
    id = database_simulate.MODEL_HELPERS.result_add(
        user_id = user_id,
        grid_id = grid_id,
        energy_management_system_id = energy_management_system_id,
        powerload_id = powerload_id,
        location_id = location_id,
        startdatetime = startdatetime,
        enddatetime = enddatetime,
    )

    params = {
        run_helpers.LOAD_ID:powerload_id,
        run_helpers.GRID_ID:grid_id,
        run_helpers.LOCATION_ID: location_id,
        run_helpers.ENERGY_MANAGEMENT_SYSTEM_ID:energy_management_system_id,
        run_helpers.STARTDATETIME:startdatetime,
        run_helpers.ENDDATETIME:enddatetime,
        run_helpers.WEATHER_SAMPLE_METHOD : "mean",
    }

    # run simulate method (stores results to database)
    run_helpers.run_analysis(
        table_name="simulate",
        id=id,
        params=params,
        results_relative_url="simulate/compute/?id=",
        send_email=False
    )
    
    # retrieve results from database
    stats = database_simulate.metrics_get(id)["summary_stats"]["Contribution as a % of Total Energy"]
    
    # delete test from database
    if not exists: database_simulate.MODEL_HELPERS.remove(id)

    # test passes if all component types aside from battery have a non-negative contribution
    assert(stats['DieselGenerator'] >= 0.0 and 
        stats['SolarPhotovoltaicPanel'] >= 0.0 and stats['WindTurbine'] >= 0.0
        and stats['Unmet Energy'] >= 0.0)
