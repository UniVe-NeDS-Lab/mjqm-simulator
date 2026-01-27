# Result Analysis

After running simulations with the MJQM simulator, you'll find data files in the `Results` directory, in a subdirectory with the [name](./#/run?id=simulation-parameters) of your simulation. We provide two main ways to visualize and analyze these results:

1. **Static Plots**: Generate publication-quality charts using `plot_experiment.py`
2. **Interactive Dashboard**: Explore results dynamically with the Plotly-based web application

The provided Python environment has all required packages already installed for both methods, and it also includes the [Spyder IDE](https://www.spyder-ide.org/) for a more custom approach to results analysis.

## Understanding the Visualizations

Both visualization methods share some common elements:

- **X-axis**: System arrival rate on a logarithmic scale
- **Y-axis**: Performance metric (response time, waiting time) on a logarithmic scale
- **Policies**: Consistent colors/markers pairs represent different scheduling policies
- **Asymptotes**: Vertical dotted lines show the maximum stable arrival rate that was simulated for each policy
- **Utilization**: Percentage values showing system utilization at stability limit

The plots help identify:

1. **Policy Efficiency**: Which policies perform better at different load levels
2. **Fairness**: How different job classes are treated by each policy
3. **System Stability**: At what arrival rate each policy makes the system unstable
4. **Scalability**: How performance changes as system load increases

## Static Charts

The `plot_experiment.py` script generates high-quality plots suitable for publications, presentations, and detailed analysis. It uses matplotlib to create PDF and PNG visualizations of various metrics.

### Running plot_experiment.py

To generate static plots for a simulation:

```sh
uv run scripts/plot_experiment.py [simulation_folder]
```

Where `[simulation_folder]` is the relative path to your simulation results under the `Results` directory. If you don't specify a simulation, the script will prompt you to select one from the available folders.

### Generated Plots

The script will generate several plots in the simulation folder:

- **Response Time Plots** (in `RespTime` subfolder):
  - `lambdasVsTotRespTime.pdf/png`: Overall response time vs arrival rate
  - `lambdasVsT{N}RespTime.pdf/png`: Response time for each job class vs arrival rate

- **Waiting Time Plots** (in `WaitTime` subfolder):
  - `lambdasVsTotWaitTime.pdf/png`: Overall waiting time vs arrival rate
  - `lambdasVsT{N}WaitTime.pdf/png`: Waiting time for each job class vs arrival rate

### Customizing Plots

You can customize the plots by modifying parameters in `plot_experiment.py`. The key configurations include:

- `n_cores`: Number of cores in the system. If you included the `cores` column in the simulation output, that will be used.
- `cols`: The [colors](https://matplotlib.org/stable/gallery/color/named_colors.html) to use for simulated distributions
- `markers`: The [markers](https://matplotlib.org/stable/api/markers_api.html) to display the executed simulations
- `ylims_*`: Y-axis limits for different plot types

## Interactive report

The Plotly-based report provides an interactive dashboard for exploring simulation results dynamically.

### Running the report

To launch the interactive dashboard:

```sh
uv run scripts/plotly_app.py
```

This will start a local web server (by default at http://127.0.0.1:8050/) where you can access the report.

### Customizing the Dashboard

If you want to customize the dashboard, you can modify the `plotly_app.py` file:

1. **Add New Metrics**: Extend the `y_axis_mappings` dictionary to include additional metrics
2. **Change Default Settings**: Modify initial values for dropdowns and toggles
3. **Update Appearance**: Adjust styling parameters in the layout definition
4. **Modify Plot Settings**: Change plot attributes like coloring, hover data, and axes settings

For example, to add a new metric for execution efficiency:

```python
y_axis_mappings = dict(
    # ... existing metrics ...
    throughput=dict(
        column="Throughput",
        label="Throughput",
        class_column="T{} Throughput",
        uom=" [%]",
        per_class=True,
    ),
)
```

You can also modify, in the `plot_experiment.py` script, the cosmetic variables:

- `cols`: The [colors](https://matplotlib.org/stable/gallery/color/named_colors.html) to use for simulated distributions
- `markers_plotly`: The [markers](https://plotly.com/python/marker-style/#Custom-Marker-Symbols) to display the executed simulations


### Dashboard Features

The dashboard provides the following features:

1. **Simulation Selection**: Choose which simulation to analyze from a dropdown menu
2. **Core Configuration**: Set the number of simulated cores
3. **Data Table**: View and sort raw simulation data (can be hidden)
4. **Y-Axis Selection**: Choose which metric to display:
   - Response Time
   - Waiting Time
   - Wasted Servers
5. **Class Selection**: Choose which job class to analyze:
   - Overall metrics
   - Smallest class metrics
   - Biggest class metrics
   - Select a specific class
6. **Interactive Plot**: A log-log plot displaying the selected metric against arrival rate
   - Different colors for each policy
   - Hover information for precise values
   - Vertical dotted lines showing asymptotic limits
   - Downloadable as PNG


## Development and Custom Analysis

For more advanced analysis and custom visualizations, we provide tools to work with the simulation data directly.

### Using Spyder IDE

For a more interactive development experience, you can use the Spyder IDE that comes with the Python environment:

```sh
uv run spyder
```

When working with the analysis tools, it's helpful to open these three main Python files in Spyder from the `scripts` folder:
- `load_experiment_data.py`: Core module for loading simulation data
- `plot_experiment.py`: Static plot generation
- `plotly_app.py`: Interactive dashboard

This allows you to easily examine, modify, and run the visualization code while having access to data loading functions.

### Working with Data in Spyder

To interactively explore simulation data in Spyder, open the `load_experiment_data.py` file and execute it.
It will let you select the simulation results to load via the command line, and it will prepare the environment with your data.

If the wrong number of cores was picked, or you want to reload the data for any other reason, you can directly execute the following:

```python
# Reload the data with the appropriate number of cores
dfs, Ts, exp, asymptotes, actual_util = load_experiment_data(folder, n_cores=2048)

# Now you can explore the dataframe
dfs.head()
```
