from dash import dcc, html

from src.data import data, incident_types, state_codes
from src.mappings import dropdown_options, state_map

# Main layout of the Dash application
main_layout = html.Div(
    style={
        "display": "flex",
        "flexDirection": "column",  # Vertical stacking
        "height": "100vh",  # Full viewport height
        "margin": "0",
        "padding": "0",
        "boxSizing": "border-box",
    },
    children=[
        # Store components to cache data for callbacks
        dcc.Store(id="store-treemap1"),
        dcc.Store(id="store-bar1"),
        dcc.Store(id="store-scatter1"),
        dcc.Store(id="store-treemap2"),
        dcc.Store(id="store-bar2"),
        dcc.Store(id="store-scatter2"),
        dcc.Store(id="bar-selected-data", data=None),
        # CSS to remove body margins
        html.Link(rel="stylesheet", href="data:text/css,body { margin: 0; }"),
        # Header at the top
        html.Div(
            style={
                "width": "100%",
                "backgroundColor": "#2c3e50",  # Dark background
                "color": "white",  # White text
                "textAlign": "center",  # Center-align text
                "boxSizing": "border-box",
            },
            children=[
                html.H1(
                    "US Workplace Safety Tracker",
                    style={
                        "margin": "0",
                        "fontSize": "2em",  # Large font
                        "padding": "0.5em 0",  # Padding for spacing
                    },
                ),
            ],
        ),
        # Main content area with sidebar and tabs
        html.Div(
            style={
                "display": "flex",  # Side-by-side layout
                "flexGrow": "1",
                "height": "100%",
                "overflow": "hidden",  # Prevent content overflow
            },
            children=[
                # Sidebar for filters and dropdowns
                html.Div(
                    id="left-menu",
                    style={
                        "width": "15%",  # Sidebar width
                        "backgroundColor": "#f4f4f4",  # Light gray background
                        "padding": "1%",
                        "borderRight": "1px solid #dfe4ea",  # Border separator
                        "boxSizing": "border-box",
                        "minHeight": "calc(100vh - 3rem)",  # Ensure full height
                        "flexShrink": "0",  # Prevent shrinking
                        "overflowY": "auto",  # Scroll if content exceeds height
                    },
                    children=[
                        # State selection dropdown
                        html.Div(
                            id="state-dropdown-container",
                            children=[
                                html.H4("Select State", style={"marginBottom": "5%"}),
                                dcc.Dropdown(
                                    id="state-dropdown",
                                    options=state_map,  # List of states
                                    value=state_codes[0],  # Default to the first state
                                    placeholder="Select State",
                                    style={"width": "100%"},
                                    clearable=False,
                                ),
                            ],
                        ),
                        # KPI selection dropdown
                        html.Div(
                            id="kpi-select-container",
                            children=[
                                html.H4("Select KPI", style={"marginBottom": "5%"}),
                                dcc.Dropdown(
                                    id="kpi-select-dropdown",
                                    options=dropdown_options,  # KPI options
                                    value="incident_rate",  # Default selection
                                    placeholder="Select KPI",
                                    style={"width": "100%"},
                                    clearable=False,
                                ),
                            ],
                        ),
                        # Date range picker
                        html.Div(
                            id="date-picker-container",
                            children=[
                                html.H4(
                                    "Select Date Range", style={"marginBottom": "5%"}
                                ),
                                dcc.DatePickerRange(
                                    id="date-picker-range",
                                    start_date=data[
                                        "date_of_incident"
                                    ].min(),  # Min date
                                    end_date=data["date_of_incident"].max(),  # Max date
                                    display_format="DD/MM/YYYY",  # User-friendly format
                                    style={"width": "100%"},
                                ),
                            ],
                        ),
                        # Incident type filter dropdown
                        html.Div(
                            id="incident-filter-container",
                            children=[
                                html.H4(
                                    "Filter by Incident Type",
                                    style={"marginBottom": "5%"},
                                ),
                                dcc.Dropdown(
                                    id="incident-filter-dropdown",
                                    options=[
                                        {"label": cat_value, "value": cat_value}
                                        for cat_value in incident_types
                                    ],
                                    placeholder="Select one or more categories",
                                    multi=True,  # Allow multiple selections
                                    clearable=True,
                                    style={"width": "100%"},
                                ),
                            ],
                        ),
                    ],
                ),
                # Main content area with tabs for visualizations
                html.Div(
                    style={
                        "width": "85%",  # Main content takes the rest of the width
                        "padding": "0",
                        "boxSizing": "border-box",
                        "overflow": "auto",
                        "height": "100%",  # Full height
                    },
                    children=[
                        # Tabs for switching between views
                        dcc.Tabs(
                            id="tabs",
                            value="state_analysis_tab",  # Default tab
                            children=[
                                # Tab 1: State Performance Overview
                                dcc.Tab(
                                    label="State Performance Overview",
                                    value="state_analysis_tab",
                                    children=[
                                        html.Div(
                                            id="content",
                                            style={"width": "100%", "height": "100%"},
                                        ),
                                    ],
                                ),
                                # Tab 2: In-Depth State Insights
                                dcc.Tab(
                                    label="In-Depth State Insights",
                                    value="metric_analysis_tab",
                                    children=[
                                        html.Div(
                                            id="content-metric-analysis",
                                            style={"width": "100%", "height": "100%"},
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)
