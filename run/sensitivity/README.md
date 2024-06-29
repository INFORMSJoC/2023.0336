# Run scripts

- `run_single_design.py` performs sensitivity analysis on a speficied microgrid design, including generating design modifications and executing a design of experiments
- `run_all_designs.py` wrapper to run `run_single_design.py` on all microgrid designs
- `compile_single_design.py` compiles sensitivity analysis results for a single microgrid design, including all generated modifications
- `compile_all_designs.py` wrapper to run `compile_single_design.py` on all microgrid designs
- `aggregate_compiled_results.py` aggregates sensitivity analysis results compiled by `compile_results_all` in a single file
- `plot_interactive_aggregated_results.py` generates an interactive plot from the sensitivity analysis results file output by `aggregate_compiled_results.py`
- `plot_threshold_aggregated_results.py` generates and saves a plot from the sensitivity analysis results file output by `aggregate_compiled_results.py`

# Parameter files

- `*.yaml.template` are config files to set values for command-line options in Python scripts (copy these to *.yaml to use)
