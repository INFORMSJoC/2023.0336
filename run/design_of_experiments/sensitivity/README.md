# Files

- `doe_cloud_lower_dependence.py` scales output of `stack_nolhs_wrapper.py` to interpret `cloud_lower` as a fraction of `cloud_upper`
- `rng_distribution_defaults.yml` is a default set of weather parameters for `run/sensitivity/run_single_design.py`
- `parameters.csv` is an the input file from Reich & Sanchez (2023) for `stack_nolhs_wrapper.py`

# Experiment from Reich & Sanchez (2023)

- run `run/design_of_experiments/stack_nolhs_wrapper.py -c run/design_of_experiments/sensitivity/stack_nolhs_wrapper.yml` to generate `run/design_of_experiments/sensitivity/designs.csv`
- run  `run/design_of_experiments/sensitivity/doe_cloud_lower_dependence.py --doe_experiment_file run/design_of_experiments/sensitivity/designs.csv` to generate `run/design_of_experiments/sensitivity/designs_cloud_lower_modified.csv`
- use `designs_cloud_lower_modified.csv` when running sensitivity analysis method
