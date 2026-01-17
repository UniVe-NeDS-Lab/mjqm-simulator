# Import packages

import dash_daq as daq
import plotly.express as px
from dash import (
    Dash,
    Input,
    Output,
    State,
    callback,
    dash_table,
    dcc,
    html,
    no_update,
)
from load_experiment_data import (
    load_experiment_data,
    load_experiments_list,
)
from plot_cells import prepare_cosmetics

base, available_experiments = load_experiments_list()

y_axis_mappings = dict(
    response_time=dict(
        column="RespTime Total",
        label="Response Time",
        class_column="T{} RespTime",
        uom=" [s]",
        per_class=True,
    ),
    waiting_time=dict(
        column="WaitTime Total",
        label="Waiting Time",
        class_column="T{} Waiting",
        uom=" [s]",
        per_class=True,
    ),
    # run_duration=dict(
    #     column="Run Duration",
    #     label="Simulation Run Duration",
    #     uom=" [s]",
    #     per_class=False,
    # ),
    wasted_servers=dict(
        column="Wasted Servers",
        label="Wasted Servers",
        uom="",
        per_class=False,
    ),
    queue=dict(
        column="Queue Total",
        label="Queue",
        class_column="T{} Queue",
        uom="",
        per_class=True,
    ),
)


# Initialize the app
app = Dash("mjqm")
# App layout
app.layout = [
    html.H1(
        [
            "MJQM Simulation results ",
            html.Span("", id="title-slug"),
        ],
        id="title",
    ),
    html.Div(
        children=[
            html.Div(
                [
                    html.Div(
                        "Experiment",
                        style=dict(margin="0 .5em"),
                    ),
                    dcc.Dropdown(
                        options=list(
                            map(
                                lambda f: str(f.relative_to(base)),
                                available_experiments,
                            )
                        ),
                        value=None,
                        placeholder="Select the experiment to analyse",
                        id="experiment-selection",
                        persistence=True,
                        persistence_type="session",
                        style=dict(margin="0 .5em", width="99%"),
                    ),
                ],
                style={
                    "vertical-align": "middle",
                    "width": "39%",
                },
            ),
            daq.NumericInput(
                id="experiment-cores",
                min=1,
                max=10_000_000,
                value=2048,
                label="Simulated cores",
                persistence=True,
                persistence_type="session",
                style=dict(margin="0 .5em"),
                size=100,
            ),
            daq.BooleanSwitch(
                id="display-data-table",
                on=False,
                label="Show data table",
                labelPosition="top",
                style=dict(margin="0 .5em"),
            ),
        ],
        style={
            "justifyContent": "flex-start",
            "display": "flex",
            "margin": ".5em 0",
        },
    ),
    html.Div(
        [
            dcc.Loading(
                children=[
                    dash_table.DataTable(
                        data=None,
                        page_size=10,
                        id="experiment-data-table",
                        persistence=True,
                        persistence_type="session",
                        fixed_columns=dict(headers=True, data=2),
                        sort_action="native",
                        sort_mode="multi",
                        export_format="csv",
                        export_headers="names",
                        css=[
                            dict(
                                selector=".dash-spreadsheet.dash-freeze-left",
                                rule="max-width: 100%",
                            )
                        ],
                        style_table={"overflowX": "auto"},
                    ),
                ],
                target_components={
                    "experiment-data-table": "data",
                },
                overlay_style={"visibility": "visible", "filter": "blur(2px)"},
                type="circle",
                show_initially=False,
                parent_style=dict(margin="0 .5em", width="99%"),
            ),
        ],
        id="table-container",
        style={"margin": ".5em 0", "display": "none"},
    ),
    dcc.Loading(
        [
            dcc.Tabs(
                id="y-axis-value",
                value="response_time",
                children=[
                    dcc.Tab(label=x[1]["label"], value=x[0])
                    for x in y_axis_mappings.items()
                ],
                style={
                    "border": "thin lightgrey solid",
                    "overflowX": "scroll",
                    "margin": "0 .5em",
                    "flex": "1 0 100%",
                },
                parent_style={"flex": "1 0 50%"},
            ),
            dcc.Tabs(
                id="y-axis-group",
                value="overall",
                children=[
                    dcc.Tab(label="Overall", value="overall"),
                    dcc.Tab(
                        label="Smallest Class",
                        value="smallest_class",
                        id="smallest-class-tab",
                    ),
                    dcc.Tab(
                        label="Biggest Class",
                        value="biggest_class",
                        id="biggest-class-tab",
                    ),
                    dcc.Tab(
                        label="Select Class",
                        value="select_class",
                        id="select-class-tab",
                        children=[
                            dcc.Dropdown(
                                id="custom-class-selection",
                                options=[],
                                value=None,
                                clearable=False,
                                placeholder="Class to analyse",
                                persistence=True,
                                persistence_type="session",
                                style=dict(padding="0 .5em"),
                            ),
                        ],
                    ),
                ],
                style={
                    "border": "thin lightgrey solid",
                    "overflowX": "scroll",
                    "margin": "0 .5em",
                    "flex": "1 0 100%",
                },
                parent_style={"flex": "1 0 50%"},
            ),
        ],
        target_components={
            "custom-class-selection": "options",
        },
        overlay_style={"visibility": "visible", "filter": "blur(2px)"},
        type="circle",
        show_initially=False,
        parent_style={
            "display": "flex",
            "width": "100%",
        },
        style=dict(margin=".5em 0", flex="1 0 100%"),
    ),
    dcc.Loading(
        children=[
            dcc.Graph(
                figure={},
                id="main-mjqm-plot",
                config=dict(
                    autosizable=True,
                    responsive=True,
                    scrollZoom=True,
                    toImageButtonOptions=dict(
                        filename="mjqm-chart",
                    ),
                    edits=dict(
                        legendPosition=True,
                    ),
                    # showEditInChartStudio=True,
                    # plotlyServerURL="https://chart-studio.plotly.com",
                ),
                responsive=True,
                mathjax=True,
                style={"width": "100%", "height": "550px", "flex": "1 0 100%"},
            ),
            # html.Br(),
            # dcc.Clipboard(target_id="structure"),
            # html.Pre(
            #     id="structure",
            #     style={
            #         "border": "thin lightgrey solid",
            #         "overflowX": "scroll",
            #         "height": "275px",
            #         "width": "100%",
            #     },
            # ),
        ],
        target_components={
            "main-mjqm-plot": "figure",
        },
        overlay_style={"visibility": "visible", "filter": "blur(2px)"},
        type="circle",
        show_initially=False,
        parent_style={
            "display": "flex",
            "width": "99%",
        },
    ),
]


@callback(
    Output("title-slug", "children"),
    Input("experiment-selection", "value"),
)
def update_title(experiment):
    if experiment is None:
        return None
    return "from " + experiment


@callback(
    Output("table-container", "style", allow_duplicate=True),
    Input("display-data-table", "on"),
    prevent_initial_call=True,
)
def update_table_view(display_table):
    return dict(display="block" if display_table else "none")


@callback(
    Output("experiment-data-table", "data"),
    Output("table-container", "style", allow_duplicate=True),
    Output("experiment-cores", "value"),
    Output("experiment-cores", "disabled"),
    Output("custom-class-selection", "options"),
    Output("custom-class-selection", "value"),
    Input("experiment-selection", "value"),
    Input("experiment-cores", "value"),
    State("display-data-table", "on"),
    running=[
        (Output("experiment-selection", "disabled"), True, False),
        (Output("custom-class-selection", "disabled"), True, False),
    ],
    prevent_initial_call=True,
)
def update_table(experiment, cores, display_table):
    global dfs, Ts, exp, asymptotes, actual_util
    if experiment is None:
        return None, dict(display="none"), no_update, False, None, None
    results = load_experiment_data(experiment, n_cores=cores or 2048)
    if results is None:
        return None, dict(display="none"), no_update, False, None, None
    dfs, Ts, exp, asymptotes, actual_util = results
    if "cores" in dfs.columns:
        cores = dfs["cores"].max()
        cores_selectable = False
    else:
        cores = no_update
        cores_selectable = True
    return (
        dfs.to_dict("records"),
        dict(
            width="100%",
            display="block" if display_table else "none",
        ),
        cores,
        not cores_selectable,
        Ts,
        min(Ts),
    )


@callback(
    Output("y-axis-group", "value"),
    Output("smallest-class-tab", "disabled"),
    Output("biggest-class-tab", "disabled"),
    Output("select-class-tab", "disabled"),
    Input("experiment-data-table", "data"),
    Input("y-axis-value", "value"),
)
def only_overall_value(experiment, y_axis):
    if experiment is None or y_axis is None:
        return no_update, False, False, False
    per_class = y_axis_mappings[y_axis]["per_class"]
    if not per_class:
        return "overall", True, True, True
    return no_update, False, False, False


@callback(
    Output("main-mjqm-plot", "figure"),
    Output("main-mjqm-plot", "style"),
    Input("experiment-data-table", "data"),
    Input("y-axis-value", "value"),
    Input("y-axis-group", "value"),
    Input("custom-class-selection", "value"),
    running=[
        (Output("experiment-selection", "disabled"), True, False),
        (Output("custom-class-selection", "disabled"), True, False),
    ],
)
def show_main_plot(experiment, y_axis, y_group, selected_class):
    global dfs, Ts, exp, asymptotes, actual_util
    if experiment is None:
        return None, dict(visibility="hidden")

    label = y_axis_mappings[y_axis]["label"]
    uom = y_axis_mappings[y_axis]["uom"]
    per_class = y_axis_mappings[y_axis]["per_class"]

    if y_group == "overall" or not per_class:
        col = y_axis_mappings[y_axis]["column"]
    elif y_group == "smallest_class":
        col = y_axis_mappings[y_axis]["class_column"]
        col = col.format(min(Ts))
        label += " for the Smallest Class"
    elif y_group == "biggest_class":
        col = y_axis_mappings[y_axis]["class_column"]
        col = col.format(max(Ts))
        label += " for the Biggest Class"
    elif y_group == "select_class":
        col = y_axis_mappings[y_axis]["class_column"]
        col = col.format(selected_class)
        label += f" for Class {selected_class}"

    colors, marks, marks_plotly = prepare_cosmetics(dfs, exp)
    dfs.set_index(["label"], drop=False, inplace=True)
    fig = px.line(
        dfs[dfs["stable"]],
        "arrival.rate",
        col,
        color="label",
        line_group="label",
        symbol="label",
        hover_name="label",
        hover_data={
            "label": False,
            "arrival.rate": False,
            col: True,
        },
        log_x=True,
        log_y=True,
        title=f"Avg. {label} vs. Arrival Rate",
        color_discrete_map=colors.to_dict(),
        symbol_sequence=list(map(str, marks_plotly)),
        labels={
            "label": "Policy",
            "arrival.rate": "Arrival Rate [1/s]",
            col: label + uom,
        },
        template="plotly_white",
    )
    for idx in asymptotes.index:
        fig.add_vline(
            asymptotes[idx],
            name=f"{actual_util[idx]:.1f}%",
            legend="legend2",
            line=dict(dash="dot", width=1, color=colors[idx]),
            showlegend=True,
        )
    fig.update_layout(
        title=dict(xanchor="center", x=0.5, yanchor="top"),
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            title=None,
        ),
        legend2=dict(
            yanchor="top",
            y=0.99,
            xanchor="center",
            x=0.99,
            title=None,
        ),
        hoversubplots="axis",
        hovermode="x unified",
    )
    return fig, dict(visibility="visible", display="flex")


# @app.callback(
#     Output("structure", "children"),
#     Input("main-mjqm-plot", component_property="figure"),
# )
# def display_structure(fig_json):
#     return json.dumps(fig_json, indent=2)


# Run the app
if __name__ == "__main__":
    app.run(debug=True)
