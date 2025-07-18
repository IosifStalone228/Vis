# application.py
import os

import dash
from dash import dcc, html, no_update
from dash.dependencies import Input, Output, State
from flask import Flask
from flask_caching import Cache

from src.data import (
    data,
    filter_data,
    prepare_radar_data,
    prepare_scatter_plot,
    prepare_stacked_bar_chart,
    prepare_state_data,
    prepare_treemap_data,
)
from src.layouts import main_layout
from src.mappings import dropdown_options_rev
from src.visualizations import (
    create_map,
    create_radar_chart,
    create_scatter_plot,
    create_splom,
    create_stacked_bar_chart,
    create_treemap,
)

# Initialize Flask application
application = Flask(__name__)
# Configure caching
cache = Cache(application, config={"CACHE_TYPE": "SimpleCache"})

# Initialize Dash application
app = dash.Dash(
    __name__,
    server=application,
    title="US Workplace Safety Tracker",
    update_title="Updating data...",
)
app.layout = main_layout


@app.callback(
    [Output("kpi-select-container", "style")],
    [Input("tabs", "value")],
)
def update_left_menu_visibility(tab_name: str) -> list[dict]:
    """
    Update the visibility of the left menu based on the selected tab.

    Args:
        tab_name (str): Name of the currently selected tab.

    Returns:
        list[dict]: Style dictionary to show or hide the menu.
    """
    if tab_name == "state_analysis_tab":
        return [{"display": "block"}]

    elif tab_name == "metric_analysis_tab":
        return [{"display": "none"}]

    return [{"display": "none"}]


@cache.memoize(timeout=600)  # Cache result for 10 minutes
def filter_data_cached(df, start_date: str, end_date: str, incident_types: list[str]):
    """
    Cache-enabled function to filter data based on the provided parameters.

    Args:
        df: Dataframe to filter.
        start_date (str): Start date for filtering.
        end_date (str): End date for filtering.
        incident_types (list[str]): List of incident types to include.

    Returns:
        Filtered dataframe.
    """
    return filter_data(df, start_date, end_date, incident_types)


@cache.memoize(timeout=600)  # Cache result for 10 minutes
def prepare_scatter_plot_cached(df, state_code: str):
    """
    Cache-enabled function to prepare scatter plot data for a given state.

    Args:
        df: Dataframe containing the data.
        state_code (str): State code to filter data for scatter plot.

    Returns:
        Data prepared for the scatter plot.
    """
    return prepare_scatter_plot(df, state_code)


@cache.memoize(timeout=600)  # Cache result for 10 minutes
def prepare_treemap_data_cached(df, state_code: str, selected_kpi: str):
    """
    Cache-enabled function to prepare data for the treemap visualization.

    Args:
        df: Dataframe containing the data.
        state_code (str): State code to filter data for the treemap.
        selected_kpi (str): Key performance indicator to visualize.

    Returns:
        Data prepared for the treemap.
    """
    return prepare_treemap_data(df, state_code, selected_kpi)


@cache.memoize(timeout=600)  # Cache result for 10 minutes
def prepare_stacked_bar_chart_cached(df, state_code: str):
    """
    Cache-enabled function to prepare data for the stacked bar chart.

    Args:
        df: Dataframe containing the data.
        state_code (str): State code to filter data for the stacked bar chart.

    Returns:
        Data prepared for the stacked bar chart.
    """
    return prepare_stacked_bar_chart(df, state_code)


@cache.memoize(timeout=600)  # Cache result for 10 minutes
def prepare_radar_data_cached(df, dropdown_state: str):
    """
    Cache-enabled function to prepare data for the radar chart visualization.

    Args:
        df: Dataframe containing the data.
        dropdown_state (str): State selected in the dropdown for filtering.

    Returns:
        Data prepared for the radar chart.
    """
    return prepare_radar_data(df, dropdown_state)


@cache.memoize(timeout=600)  # Cache result for 10 minutes
def prepare_state_data_cached(df, kpi: str):
    """
    Cache-enabled function to prepare state data based on the selected KPI.

    Args:
        df: Dataframe containing the data.
        kpi (str): Key performance indicator to visualize.

    Returns:
        Data prepared for the state visualization.
    """
    return prepare_state_data(df, kpi)


@app.callback(
    Output("state-dropdown", "value"),
    [Input("map-container", "clickData")],
    [State("state-dropdown", "value")],
)
def update_selected_state(click_data: dict, current_state: str) -> str:
    """
    Update the selected state based on the user's click on the map.

    Args:
        click_data (dict): Data of the clicked point on the map.
        current_state (str): Currently selected state.
`
    Returns:
        str: Updated selected state.
    """
    print(">>> update_selected_state triggered")
    if click_data:
        clicked_state = click_data["points"][0]["location"]  # Get clicked state
        return current_state if clicked_state == current_state else clicked_state
    return current_state  # Retain the current state if no new click


@app.callback(
    Output("kpi-select-dropdown", "value"),
    Input("radar-chart", "clickData"),
)
def update_on_radar_click(click_data: dict) -> str:
    """
    Update the KPI dropdown selection based on clicks on the radar chart.

    Args:
        click_data (dict): Data of the clicked point on the radar chart.

    Returns:
        str: Updated KPI value for the dropdown.
    """
    print(">>> update_on_radar_click triggered")
    return (
        dropdown_options_rev.get(click_data["points"][0]["theta"], no_update)
        if click_data and "points" in click_data
        else no_update
    )


@app.callback(
    [
        Output("store-treemap2", "data"),
        Output("store-bar2", "data"),
    ],
    [
        Input("scatter-plot", "relayoutData"),
        State("date-picker-range", "start_date"),
        State("date-picker-range", "end_date"),
        State("incident-filter-dropdown", "value"),
        State("kpi-select-dropdown", "value"),
        State("state-dropdown", "value"),
    ],
    prevent_initial_call=True,
)
@cache.memoize(timeout=600)  # Cache result for 10 minutes
def update_dependent_charts(
    scatter_relayoutData: dict,
    start_date: str,
    end_date: str,
    incident_types: list[str],
    kpi: str,
    dropdown_state: str,
) -> tuple:
    """
    Update treemap and bar chart data based on scatter plot relayout events.

    Args:
        scatter_relayoutData (dict): Relayout data from the scatter plot.
        start_date (str): Start date for filtering.
        end_date (str): End date for filtering.
        incident_types (list[str]): Selected incident types for filtering.
        kpi (str): Selected KPI for visualization.
        dropdown_state (str): State selected in the dropdown.

    Returns:
        tuple: Updated data for the treemap and stacked bar chart.
    """
    print(">>> update_dependent_charts triggered")

    if not scatter_relayoutData or "autosize" in scatter_relayoutData:
        print(">>> Preventing update_dependent_charts due to insufficient relayoutData")
        raise dash.exceptions.PreventUpdate

    # Re-filter data based on date and incident filters
    filtered_data = filter_data_cached(data, start_date, end_date, incident_types)

    # If zoom info is available, further filter the data
    if scatter_relayoutData:
        x_min = scatter_relayoutData.get("xaxis.range[0]", None)
        x_max = scatter_relayoutData.get("xaxis.range[1]", None)
        y_min = scatter_relayoutData.get("yaxis.range[0]", None)
        y_max = scatter_relayoutData.get("yaxis.range[1]", None)
        if x_min is not None and x_max is not None:
            filtered_data = filtered_data[
                (
                    filtered_data["time_started_work"].dt.hour
                    + filtered_data["time_started_work"].dt.minute / 60
                    >= float(x_min)
                )
                & (
                    filtered_data["time_started_work"].dt.hour
                    + filtered_data["time_started_work"].dt.minute / 60
                    <= float(x_max)
                )
            ]
        if y_min is not None and y_max is not None:
            filtered_data = filtered_data[
                (
                    filtered_data["time_of_incident"].dt.hour
                    + filtered_data["time_of_incident"].dt.minute / 60
                    >= float(y_min)
                )
                & (
                    filtered_data["time_of_incident"].dt.hour
                    + filtered_data["time_of_incident"].dt.minute / 60
                    <= float(y_max)
                )
            ]

    # Prepare data and figures for treemap and stacked bar chart
    treemap_data = prepare_treemap_data_cached(filtered_data, dropdown_state, kpi)
    stacked_bar_data = prepare_stacked_bar_chart_cached(filtered_data, dropdown_state)

    treemap_fig = create_treemap(treemap_data, "incident_rate", dropdown_state)
    stacked_bar_fig = create_stacked_bar_chart(stacked_bar_data, dropdown_state)

    return treemap_fig, stacked_bar_fig


@app.callback(
    [
        Output("store-treemap1", "data"),
        Output("store-scatter1", "data"),
        Output("bar-selected-data", "data"),
    ],
    [
        Input("stacked-bar-chart", "clickData"),
        State("date-picker-range", "start_date"),
        State("date-picker-range", "end_date"),
        State("incident-filter-dropdown", "value"),
        State("kpi-select-dropdown", "value"),
        State("state-dropdown", "value"),
        State("bar-selected-data", "data"),
    ],
    prevent_initial_call=True,
)
@cache.memoize(timeout=600)  # Cache result for 10 minutes
def update_graphs_on_barchart_click(
    barchart_clickData: dict,
    start_date: str,
    end_date: str,
    incident_types: list[str],
    kpi: str,
    selected_state: str,
    selected_data: str,
) -> tuple:
    """
    Update graphs based on bar chart click events.

    Args:
        barchart_clickData (dict): Data of the clicked bar in the stacked bar chart.
        start_date (str): Start date for filtering.
        end_date (str): End date for filtering.
        incident_types (list[str]): Selected incident types for filtering.
        kpi (str): Selected KPI for visualization.
        selected_state (str): Selected state for visualization.
        selected_data (str): Data related to the previously selected bar.

    Returns:
        tuple: Updated treemap, scatter plot, and bar click data.
    """
    print(">>> update_graphs_on_barchart_click triggered")

    if not barchart_clickData:
        print(">>> Preventing update_graphs_on_barchart_click due to no clickData")
        raise dash.exceptions.PreventUpdate

    # Filter data based on the date range and incident types
    filtered_data = filter_data_cached(data, start_date, end_date, incident_types)

    # Handle filtering based on the clicked bar
    new_outcome = None
    if "points" in barchart_clickData:
        clicked_outcome = barchart_clickData["points"][0]["y"]  # Incident outcome

        # Check if the same outcome was clicked consecutively
        if selected_data == clicked_outcome:
            print(
                ">>> Resetting incident_outcome filter due to double-click or same point click"
            )
            new_outcome = None
        else:
            print(clicked_outcome)
            filtered_data = filtered_data[
                filtered_data["incident_outcome"] == clicked_outcome
            ]
            new_outcome = clicked_outcome  # Update the last clicked outcome

    # Prepare data and figures for treemap and scatter plot
    treemap_data = prepare_treemap_data_cached(
        filtered_data, selected_state, "incident_rate"
    )
    scatter_plot_data = prepare_scatter_plot_cached(filtered_data, selected_state)

    treemap_fig = create_treemap(treemap_data, "incident_rate", selected_state)
    scatter_plot_fig = create_scatter_plot(scatter_plot_data, selected_state)

    return treemap_fig, scatter_plot_fig, new_outcome


@app.callback(
    [
        Output("store-bar1", "data"),
        Output("store-scatter2", "data"),
    ],
    [
        Input("treemap-chart", "clickData"),
    ],
    [
        State("date-picker-range", "start_date"),
        State("date-picker-range", "end_date"),
        State("incident-filter-dropdown", "value"),
        State("kpi-select-dropdown", "value"),
        State("state-dropdown", "value"),
    ],
    prevent_initial_call=True,
)
@cache.memoize(timeout=600)  # Cache result for 10 minutes
def update_graphs_with_treemap_click(
    treemap_clickData: dict,
    start_date: str,
    end_date: str,
    incident_types: list[str],
    kpi: str,
    selected_state: str,
) -> tuple:
    """
    Update graphs based on treemap click events.

    Args:
        treemap_clickData (dict): Data of the clicked region in the treemap.
        start_date (str): Start date for filtering.
        end_date (str): End date for filtering.
        incident_types (list[str]): Selected incident types for filtering.
        kpi (str): Selected KPI for visualization.
        selected_state (str): Selected state for visualization.

    Returns:
        tuple: Updated stacked bar chart and scatter plot data.
    """
    print(">>> update_graphs_with_treemap_click triggered")
    if not treemap_clickData:
        print(">>> Preventing update_graphs_with_treemap_click due to no clickData")
        raise dash.exceptions.PreventUpdate

    # Filter data based on the date range and incident types
    filtered_data = filter_data_cached(data, start_date, end_date, incident_types)

    # If a region on the treemap was clicked, further filter by the clicked region
    if "points" in treemap_clickData:
        print(treemap_clickData)
        clicked_label = treemap_clickData["points"][0]["label"]  # Get clicked label
        clicked_parent = treemap_clickData["points"][0].get(
            "parent", None
        )  # Get parent label if present
        # Filter data based on the clicked region
        if clicked_parent and clicked_parent != "US Market":
            filtered_data = filtered_data[
                (filtered_data["soc_description_1"] == clicked_parent)
                & (filtered_data["soc_description_2"] == clicked_label)
            ]
        elif clicked_label != "US Market":
            filtered_data = filtered_data[
                (filtered_data["soc_description_1"] == clicked_label)
            ]

    # Prepare data and figures for stacked bar chart and scatter plot
    stacked_bar_data = prepare_stacked_bar_chart_cached(filtered_data, selected_state)
    scatter_plot_data = prepare_scatter_plot_cached(filtered_data, selected_state)

    stacked_bar_fig = create_stacked_bar_chart(stacked_bar_data, selected_state)
    scatter_plot_fig = create_scatter_plot(scatter_plot_data, selected_state)

    return stacked_bar_fig, scatter_plot_fig


@app.callback(
    Output("stacked-bar-chart", "figure"),
    Input("store-bar1", "data"),
    Input("store-bar2", "data"),
    prevent_initial_call=True,
)
def update_stacked_bar_figure(bar_figure_dict1: dict, bar_figure_dict2: dict) -> dict:
    """
    Update the stacked bar chart figure based on stored data.

    Args:
        bar_figure_dict1 (dict): Data for the first stacked bar chart.
        bar_figure_dict2 (dict): Data for the second stacked bar chart.

    Returns:
        dict: Updated figure for the stacked bar chart.
    """
    print(">>> update_stacked_bar_figure triggered")
    if bar_figure_dict1 is None and bar_figure_dict2 is None:
        print(">>> Preventing update_stacked_bar_figure due to None data")
        raise dash.exceptions.PreventUpdate
    return bar_figure_dict1 if bar_figure_dict1 is not None else bar_figure_dict2


@app.callback(
    Output("scatter-plot", "figure"),
    Input("store-scatter1", "data"),
    Input("store-scatter2", "data"),
    prevent_initial_call=True,
)
def update_scatter_figure(
    scatter_figure_dict1: dict, scatter_figure_dict2: dict
) -> dict:
    """
    Update the scatter plot figure based on stored data.

    Args:
        scatter_figure_dict1 (dict): Data for the first scatter plot.
        scatter_figure_dict2 (dict): Data for the second scatter plot.

    Returns:
        dict: Updated figure for the scatter plot.
    """
    print(">>> update_scatter_figure triggered")
    if scatter_figure_dict1 is None and scatter_figure_dict2 is None:
        print(">>> Preventing update_scatter_figure due to None data")
        raise dash.exceptions.PreventUpdate
    return (
        scatter_figure_dict1
        if scatter_figure_dict1 is not None
        else scatter_figure_dict2
    )


@app.callback(
    Output("treemap-chart", "figure"),
    Input("store-treemap1", "data"),
    Input("store-treemap2", "data"),
    prevent_initial_call=True,
)
def update_treemap_figure(
    treemap_figure_dict1: dict, treemap_figure_dict2: dict
) -> dict:
    """
    Update the treemap figure based on stored data.

    Args:
        treemap_figure_dict1 (dict): Data for the first treemap.
        treemap_figure_dict2 (dict): Data for the second treemap.

    Returns:
        dict: Updated figure for the treemap.
    """
    print(">>> update_treemap_figure triggered")
    if treemap_figure_dict1 is None and treemap_figure_dict2 is None:
        print(">>> Preventing update_treemap_figure due to None data")
        raise dash.exceptions.PreventUpdate
    return (
        treemap_figure_dict1
        if treemap_figure_dict1 is not None
        else treemap_figure_dict2
    )


@app.callback(
    [Output("content", "children"), Output("content-metric-analysis", "children")],
    [
        Input("tabs", "value"),
        Input("date-picker-range", "start_date"),
        Input("date-picker-range", "end_date"),
        Input("incident-filter-dropdown", "value"),
        Input("kpi-select-dropdown", "value"),
        Input("state-dropdown", "value"),
    ],
)
@cache.memoize(timeout=600)  # Cache result for 10 minutes
def update_tab_contents(
    tab_name: str,
    start_date: str,
    end_date: str,
    incident_types: list[str],
    kpi: str,
    dropdown_state: str,
) -> tuple:
    """
    Update the content of the tabs based on the selected filters and tab name.

    Args:
        tab_name (str): Name of the currently selected tab.
        start_date (str): Start date for filtering the data.
        end_date (str): End date for filtering the data.
        incident_types (list[str]): List of selected incident types for filtering.
        kpi (str): Key performance indicator to visualize.
        dropdown_state (str): Selected state in the dropdown for visualization.

    Returns:
        tuple: Updated content for the state analysis and metric analysis tabs.
    """
    print(">>> update_tab_contents triggered")
    filtered_data = filter_data_cached(data, start_date, end_date, incident_types)
    metric_analysis_content = html.Div()
    state_analysis_content = html.Div()
    if filtered_data.empty:
        return html.Div(
            html.H2(
                "No data for filters. Try to change the filters or refresh the page to reset them",
                style={"margin": "1em 2em"},
            )
        ), html.Div(
            html.H2(
                "No data for filters. Try to change the filters or refresh the page to reset them",
                style={"margin": "1em 2em"},
            )
        )
    if tab_name == "state_analysis_tab" and start_date and end_date:
        map_data = prepare_state_data_cached(filtered_data, kpi)

        radar_chart_data = prepare_radar_data_cached(filtered_data, dropdown_state)

        state_analysis_content = html.Div(
            style={
                "display": "flex",
                "flexDirection": "column",  # Stack rows vertically
                "padding": "10px",
                "height": "calc(100vh - 8rem - 40px)",
            },
            children=[
                # Row 1: Radar (left) and Map (right)
                html.Div(
                    style={
                        "display": "flex",
                        "flexDirection": "row",  # Place children side by side
                        "width": "100%",
                    },
                    children=[
                        html.Div(
                            style={
                                "width": "50%",
                                "padding": "5px",
                            },
                            children=[
                                dcc.Loading(
                                    children=[
                                        dcc.Graph(
                                            figure=create_radar_chart(
                                                radar_chart_data, dropdown_state
                                            ),
                                            id="radar-chart",
                                        ),
                                    ]
                                )
                            ],
                        ),
                        html.Div(
                            style={"width": "50%", "padding": "5px"},
                            children=[
                                dcc.Loading(
                                    children=[
                                        dcc.Graph(
                                            figure=create_map(
                                                map_data, kpi, dropdown_state
                                            ),
                                            id="map-container",
                                        ),
                                    ]
                                )
                            ],
                        ),
                    ],
                ),
                # Row 2: The splom below
                html.Div(
                    style={
                        "width": "100%",
                        "height": "800px",
                        "marginTop": "20px",
                        "flex": "1",
                    },
                    children=[
                        dcc.Loading(
                            children=[
                                dcc.Graph(
                                    figure=create_splom(map_data, kpi, dropdown_state),
                                    id="splom-container",
                                )
                            ],
                        )
                    ],
                ),
            ],
        )

    if tab_name == "metric_analysis_tab":
        scatter_plot_data = prepare_scatter_plot_cached(
            filtered_data,
            dropdown_state,
        )
        treemap_data = prepare_treemap_data_cached(
            filtered_data,
            dropdown_state,
            "incident_rate",
        )
        stacked_bar_chart = prepare_stacked_bar_chart_cached(
            filtered_data, dropdown_state
        )
        metric_analysis_content = html.Div(
            style={
                "display": "flex",
                "alignContent": "center",
                "justifyContent": "center",
                "flexDirection": "column",
                "padding": "1rem",
                "height": "calc(100vh - 8rem - 40px)",
            },
            children=[
                html.Div(
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "1fr 1fr",  # Two equal-width columns
                        "gridTemplateRows": "1fr 1fr",  # Equal-height rows
                        "gap": "1rem",  # Add spacing between graphs
                        "flexGrow": "1",  # Allow grid to grow to fill space
                        "height": "100%",  # Occupy full height of parent
                    },
                    children=[
                        # First Graph: Spanning from [0,0] to [1,1]
                        html.Div(
                            dcc.Loading(
                                children=[
                                    dcc.Graph(
                                        figure=create_scatter_plot(
                                            scatter_plot_data,
                                            dropdown_state,
                                        ),
                                        id="scatter-plot",
                                        style={"height": "100%", "width": "100%"},
                                    )
                                ]
                            ),
                        ),
                        # Second Graph: Spanning [2,0] to [2,2]
                        html.Div(
                            dcc.Loading(
                                children=[
                                    dcc.Graph(
                                        figure=create_treemap(
                                            treemap_data,
                                            "incident_rate",
                                            dropdown_state,
                                        ),
                                        id="treemap-chart",
                                    )
                                ]
                            ),
                            style={
                                "gridColumn": "1/3",  # Spans columns 1 to 3
                                "gridRow": "2",
                                "height": "100%",
                                "width": "100%",  # Occupies the third row
                            },
                        ),
                        # Third Graph: Spanning [2,0] to [2,1]
                        html.Div(
                            dcc.Loading(
                                children=[
                                    dcc.Graph(
                                        figure=create_stacked_bar_chart(
                                            stacked_bar_chart, dropdown_state
                                        ),
                                        id="stacked-bar-chart",
                                        style={"height": "100%", "width": "100%"},
                                    )
                                ]
                            ),
                            style={
                                "gridColumn": "2",  # Spans columns 1 to 2
                                "gridRow": "1",
                                "height": "100%",
                                "width": "100%",  # Occupies the third row
                            },
                        ),
                    ],
                ),
            ],
        )

    return state_analysis_content, metric_analysis_content


if __name__ == "__main__":
    application.run(
        debug=True, host=os.environ.get("HOST", None), port=os.environ.get("PORT", None)
    )
