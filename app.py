import dash, os, sys
from dash import dcc, html, callback_context
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import datetime, time, threading, logging

# Import actual modules (adjust paths as necessary)
from simulator import Simulator
from norway_setup import setup_norway_network
from data_handler import verify_data_files, load_zone_data
from config import DEFAULT_SIMULATION_DAYS, SIMULATION_WARM_UP_DAYS, DEFAULT_START_DATE, LOG_LEVEL 
from config import ENABLE_WIND, ENABLE_IMPORT_PHASE1, ENABLE_LOCAL_HYDRO, ENABLE_IMPORT_PHASE2, ENABLE_TWO_HOP
from config import WIND_PRODUCTION_FACTOR, CONSUMPTION_FACTOR, EFFECTIVE_INFLOW_FACTOR, RESERVOIR_FILL_LEVEL_FACTOR
from config import WEBAPP_GRAPH_MAX_CONSUMPTION, WEBAPP_GRAPH_STORAGE_LEVEL, WEBAPP_GRAPH_MAX_PRODUCTIONN
from utils import setup_logging  # Assumes setup_logging writes to file and console
from reporting import generate_simulation_summary_html

# -------------------------
# Configuration and Logging
# -------------------------
setup_logging(log_level=LOG_LEVEL, log_file="simulation.log")
logger = logging.getLogger(__name__)
    
# Determine current directory and parent directory for locating data files.
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
    
# -------------------------
# Global Simulation State
# -------------------------
# We'll store the Simulator instance in a global variable.
simulator_instance = None
simulation_running = False
simulation_thread = None
simulation_lock = threading.Lock()
current_index = 0           # Global index to step through simulation results

# -------------------------
# Function to Run Simulation in Background
# -------------------------
def background_simulation(start_date, duration, phase_settings, demand_factor=CONSUMPTION_FACTOR, wind_factor=WIND_PRODUCTION_FACTOR, hydro_inflow_factor=EFFECTIVE_INFLOW_FACTOR,hydro_resfill_factor=RESERVOIR_FILL_LEVEL_FACTOR):
    global simulator_instance, simulation_running
    # Set up network and load data via your actual code
    zones, connections = setup_norway_network()
    # In a real implementation, you’d load actual data using your data_handler;
    # for now, assume your Simulator can be initialized with these parameters.
    # Replace the following with actual data loading.
    wind_data = {}       # Replace with actual wind data (dictionary keyed by date)
    hydro_inflow_data = {}  # Replace with actual hydro inflow data
    hydro_resfill_data = {}
    demand_data = {}     # Replace with actual demand data

    simulation_days = duration + SIMULATION_WARM_UP_DAYS
    sim_end_date = start_date + datetime.timedelta(days=simulation_days - 1)

   # Loop over each zone and load its respective data.
    for zone_id in zones:
        logger.info(f"Loading data for {zone_id}...")
        # Load the zone's daily data given the parent directory and simulation period.
        zone_data = load_zone_data(zone_id, parent_dir, start_date, sim_end_date)
        
        # Store the daily wind data, keyed by date and zone.
        for dt_item, val in zone_data['wind'].items():
            wind_data.setdefault(dt_item, {})[zone_id] = val * wind_factor
        
        # Store the daily hydro inflow data.
        for dt_item, val in zone_data['inflow'].items():
            hydro_inflow_data.setdefault(dt_item, {})[zone_id] = val * hydro_inflow_factor
        
        # Store the reservoir fill (hydro reserve fill) data.
        for dt_item, val in zone_data['resfill'].items():
            hydro_resfill_data.setdefault(dt_item, {})[zone_id] = val * hydro_resfill_factor
        
        # Store the daily demand data.
        for dt_item, val in zone_data['demand'].items():
            demand_data.setdefault(dt_item, {})[zone_id] = val * demand_factor
 

    # Create the Simulator instance with actual parameters
    simulator_instance = Simulator(
        zones=zones,
        connections=connections,
        start_date=start_date,
        wind_data=wind_data,
        hydro_inflow_data=hydro_inflow_data,
        demand_data=demand_data,
        phase_settings=phase_settings,
        warm_up_days=SIMULATION_WARM_UP_DAYS,
        reservoir_fill_data=hydro_resfill_data  # Replace if you have reservoir fill data
    )
    # Run the simulation (this call should update simulator_instance.results and simulator_instance.transfer_records)
    simulator_instance.run_simulation()
    simulation_running = False

# -------------------------
# Dash App Layout
# -------------------------
app = dash.Dash(__name__)

# -------------------------
# Dash App Layout with Flexbox
# -------------------------
app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div([
    html.H1("Interactive Energy Distribution Simulator"),
    # Main container with left navigation and right simulation view
    html.Div([
        # Left Navigation Pane
        html.Div([
            html.Label("Start Date"),
            dcc.DatePickerSingle(
                id='start-date-picker',
                date=DEFAULT_START_DATE
            ),
            html.Br(),
            html.Br(),
            html.Label("Demand Factor"),
            html.Br(),
            dcc.Input(
                id='demand-factor-input',
                type='number',
                value=CONSUMPTION_FACTOR,
                step=0.01,
                min=0
            ),
            html.Br(),
            html.Br(),
            html.Label("Wind Production Factor"),
            html.Br(),
            dcc.Input(
                id='wind-production-factor-input',
                type='number',
                value=WIND_PRODUCTION_FACTOR,
                step=0.01,
                min=0
            ),
            html.Br(),
            html.Br(),
            html.Label("Effective Inflow Factor"),
            html.Br(),
            dcc.Input(
                id='effective-inflow-factor-input',
                type='number',
                value=EFFECTIVE_INFLOW_FACTOR,
                step=0.01,
                min=0
            ),
            html.Br(),
            html.Br(),
            html.Label("Reservoir Fill Level Factor"),
            html.Br(),
            dcc.Input(
                id='reservoir-Fill-Level-factor-input',
                type='number',
                value=RESERVOIR_FILL_LEVEL_FACTOR,
                step=0.01,
                min=0
            ),
            html.Br(),
            html.Br(),
            html.Label("Simulation Duration"),
            dcc.RadioItems(
                id='duration-radio',
                options=[
                    {'label': '1 Year', 'value': 365},
                    {'label': '6 Months', 'value': 182},
                    {'label': '3 Months', 'value': 91},
                    {'label': '1 Month', 'value': 30}
                ],
                value=DEFAULT_SIMULATION_DAYS
            ),
            html.Br(),
            html.Label("Phase Settings"),
            dcc.Checklist(
                id='phase-checklist',
                options=[
                    {'label': 'Enable Wind Production', 'value': 'ENABLE_WIND'},
                    {'label': 'Enable First Import Phase', 'value': 'ENABLE_IMPORT_PHASE1'},
                    {'label': 'Enable Local Hydro Production', 'value': 'ENABLE_LOCAL_HYDRO'},
                    {'label': 'Enable Second Import Phase', 'value': 'ENABLE_IMPORT_PHASE2'},
                    {'label': 'Enable Two-Hop Routing', 'value': 'ENABLE_TWO_HOP'}
                ],
                value=['ENABLE_WIND', 'ENABLE_IMPORT_PHASE1',
                       'ENABLE_LOCAL_HYDRO', 'ENABLE_IMPORT_PHASE2',
                       'ENABLE_TWO_HOP']
            ),
            html.Br(),
            html.Label("Progress Resolution"),
            dcc.RadioItems(
                id='resolution-radio',
                options=[
                    {'label': 'Daily', 'value': 'daily'},
                    {'label': 'Weekly', 'value': 'weekly'},
                    {'label': 'Monthly', 'value': 'monthly'}
                ],
                value='daily'
            ),
            html.Br(),
            html.Button("Start Simulation", id="start-simulation-btn", n_clicks=0),
            html.Button("Skip to End", id="skip-simulation-btn", n_clicks=0)
        ], style={'flex': '0 0 25%', 'padding': '10px', 'borderRight': '1px solid #ccc'}),
        
        # Right Simulation View: Split horizontally into Top (2/3) and Bottom (1/3)
        html.Div([
            # Top: Two charts side by side
            html.Div([
                html.Div([
                    dcc.Graph(id='abs-storage-graph')
                ], style={'flex': '1', 'padding': '5px'}),
                html.Div([
                    dcc.Graph(id='daily-components-graph')
                ], style={'flex': '1', 'padding': '5px'})
            ], style={'display': 'flex', 'flexDirection': 'row', 'flex': '2'}),
            
            # Bottom: Zone Metrics Graph (Grouped Bar Chart)
            html.Div([
                dcc.Interval(id='interval-component', interval=1000, n_intervals=0),
                dcc.Graph(id='zone-metrics-graph')
            ], style={'flex': '1', 'padding': '5px'})
        ], style={'flex': '1', 'display': 'flex', 'flexDirection': 'column', 'paddingLeft': '10px', 'height': '85vh'})
    ], style={'display': 'flex', 'height': '5vh'}
    )
    ], style={'flex': 1, 'min-height': '100vh','min-width': '100vh', 'display': 'flex', 'flex-direction': 'column', 'padding': '20px'}),
        
    # Simulation Summary section on "Page 2" (scroll down)
    html.Div([
        html.H2("Simulation Summary"),
        html.Div(id='simulation-summary-div')
    ], style={'flex': 1, 'min-height': '100vh', 'display': 'flex', 'flex-direction': 'column', 'padding': '20px'})
])

# -------------------------
# Global variable for simulation step index
# -------------------------
current_index = 0

# -------------------------
# Callback to update top plots: Absolute Storage Levels and Daily Energy Components
# -------------------------
@app.callback(
    [Output('abs-storage-graph', 'figure'),
     Output('daily-components-graph', 'figure')],
    [Input('interval-component', 'n_intervals')],
     Input('demand-factor-input', 'value'),
     Input('reservoir-Fill-Level-factor-input', 'value')
)
def update_top_plots(n_intervals, demand_factor,refill_factor):
    with simulation_lock:
        if not simulator_instance or not simulator_instance.results:
            return go.Figure(), go.Figure()

        # Use only simulation results generated so far (up to current_index)
        results_so_far = simulator_instance.results[:current_index+1]        
        # Use all simulation results to set the x-axis range.
        all_results = simulator_instance.results
        start_date_sim = all_results[0]['date']
        end_date_sim = all_results[-1]['date']
        
        # Build Absolute Storage Levels Figure (left plot)
        dates = [res["date"] for res in results_so_far]
        zones = list(all_results[0]['metrics'].keys())
        fig_storage = go.Figure()
        for zone in zones:
            levels = [day["metrics"][zone]["current_level"] for day in results_so_far]
            fig_storage.add_trace(go.Scatter(x=dates, y=levels, mode='lines', name=zone))
        max_storage = WEBAPP_GRAPH_STORAGE_LEVEL * refill_factor  # Fixed maximum storage capacity (MWh)
        fig_storage.update_layout(
            title="Daily Hydro Storage Levels",
            xaxis=dict(title="Date", range=[start_date_sim, end_date_sim]),
            yaxis=dict(title="Storage (MWh)", range=[0, max_storage])
        )
        
        # Build Daily Energy Components Figure (right plot)
        summary = [res["summary"] for res in results_so_far]
        total_demand = [s["demand"] for s in summary]
        wind_used = [s["wind"] for s in summary]
        # Assuming 'import' is the sum of phase1 and phase2 in your summary:
        imports = [s.get("import", 0) for s in summary]
        local_hydro = [s["local_hydro"] for s in summary]
        unmet = [s["unmet"] for s in summary]
        fig_components = go.Figure()
        # Create a stacked area chart (using stackgroup)
        fig_components.add_trace(go.Scatter(x=dates, y=wind_used, mode='lines', stackgroup='one', name='Wind'))
        fig_components.add_trace(go.Scatter(x=dates, y=local_hydro, mode='lines', stackgroup='one', name='Local Hydro'))
        fig_components.add_trace(go.Scatter(x=dates, y=imports, mode='lines', stackgroup='one', name='Import'))
        fig_components.add_trace(go.Scatter(x=dates, y=unmet, mode='lines', stackgroup='one', name='Unmet'))
        fig_components.add_trace(go.Scatter(x=dates, y=total_demand, mode='lines', name='Total Demand'))
        max_consumption = WEBAPP_GRAPH_MAX_CONSUMPTION * demand_factor  # Fixed maximum consumption scale (MWh)
        fig_components.update_layout(
            title="Daily Energy Components vs Total Demand",
            xaxis=dict(title="Date", range=[start_date_sim, end_date_sim]),
            yaxis=dict(title="Energy (MWh)", range=[0, max_consumption])
        )
        
        return fig_storage, fig_components


# -------------------------
# Callback to update the zone metrics graph (grouped bar chart)
# -------------------------
@app.callback(
    Output('zone-metrics-graph', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('resolution-radio', 'value')],
     Input('reservoir-Fill-Level-factor-input', 'value')
)
def update_zone_metrics(n_intervals, resolution,reservoid_fill_level_factor):
    global current_index
    with simulation_lock:
        if not simulator_instance or simulation_running or not simulator_instance.results:
            return go.Figure(data=[])
        
        # Determine step size based on selected resolution.
        if resolution == 'daily':
            step = 1
        elif resolution == 'weekly':
            step = 7
        elif resolution == 'monthly':
            step = 30
        else:
            step = 1
        current_index = min(current_index + step, len(simulator_instance.results) - 1)
        
        current_result = simulator_instance.results[current_index]
        date = current_result['date']
        metrics = current_result['metrics']
        
        zones = list(metrics.keys())
        demand_vals   = [metrics[z]['demand'] for z in zones]
        wind_vals     = [metrics[z]['wind'] for z in zones]
        local_vals    = [metrics[z]['local_production'] for z in zones]
        imported_vals = [metrics[z]['imported'] for z in zones]
        exported_vals = [metrics[z]['exported'] for z in zones]
        storage_vals  = [metrics[z]['current_level'] for z in zones]
        
        fig = go.Figure(data=[
            go.Bar(name='Demand', x=zones, y=demand_vals, offsetgroup='demand', marker_color='rgba(55, 128, 191, 0.7)'),
            go.Bar(name='Wind Used', x=zones, y=wind_vals, offsetgroup='wind', marker_color='rgba(26, 118, 255, 0.7)'),
            go.Bar(name='Local Hydro', x=zones, y=local_vals, offsetgroup='local', marker_color='rgba(50,205,50,0.7)'),
            go.Bar(name='Imported', x=zones, y=imported_vals, offsetgroup='imported', marker_color='rgba(255,165,0,0.7)'),
            go.Bar(name='Exported', x=zones, y=exported_vals, offsetgroup='exported', marker_color='rgba(128,0,128,0.7)'),
            go.Bar(name='Storage Level', x=zones, y=storage_vals, offsetgroup='storage', marker_color='rgba(255,99,71,0.7)', yaxis="y2")
        ])
        
        max_production = WEBAPP_GRAPH_MAX_PRODUCTIONN
        max_storage = WEBAPP_GRAPH_STORAGE_LEVEL
        
        fig.update_layout(
            barmode='group',
            title=f"Zone Metrics on {date}",
            xaxis_title="Zone",
            yaxis=dict(
                title="Production / Consumption (MWh)",
                range=[0, max_production]
            ),
            yaxis2=dict(
                title="Hydro Storage (MWh)",
                overlaying='y',
                side='right',
                range=[0, max_storage]
            ),
            legend_title="Metric"
        )
        return fig

@app.callback(
    Output('interval-component', 'interval'),
    [Input('resolution-radio', 'value')]
)
def update_interval(resolution):
    """
    Update the refresh interval based on the simulation resolution.
    
    Parameters:
      resolution (str): The resolution selected by the user ('daily', 'weekly', 'monthly').

    Returns:
      int: Interval in milliseconds.
            - 1000ms for monthly,
            - 500ms for weekly,
            - 250ms for daily.
    """
    if resolution == 'monthly':
        return 1000
    elif resolution == 'weekly':
        return 500
    else:
        return 100

@app.callback(
    Output('simulation-summary-div', 'children'),
    [Input('skip-simulation-btn', 'n_clicks'),
     Input('interval-component', 'n_intervals')]
)
def update_simulation_summary(skip_clicks, n_intervals):
    # Trigger this callback when "Skip to End" is clicked.
    # Ensure that simulation_instance exists and has results.
    if simulator_instance and simulator_instance.results:
        # Generate HTML components for summary based on simulator_instance.
        return generate_simulation_summary_html(simulator_instance)
    return html.P("Simulation summary will appear here once simulation data is available.")

# -------------------------
# Callback to control simulation start and skip-to-end
# -------------------------
@app.callback(
    Output('start-simulation-btn', 'disabled'),
    [Input('start-simulation-btn', 'n_clicks'),
     Input('skip-simulation-btn', 'n_clicks')],
     Input('demand-factor-input', 'value'),
     Input('wind-production-factor-input', 'value'),
     Input('effective-inflow-factor-input', 'value'),
     Input('reservoir-Fill-Level-factor-input', 'value'),
    [State('start-date-picker', 'date'),
     State('duration-radio', 'value'),
     State('phase-checklist', 'value')]
)
def control_simulation(start_clicks, skip_clicks, demand_factor, wind_factor, inflow_factor, fill_level_factor , start_date, duration, phases):
    global simulation_thread, simulation_running, current_index
    ctx = callback_context
    if not ctx.triggered:
        return False
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id == "start-simulation-btn" and not simulation_running:
        start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        current_index = 0  # Reset simulation step
        # Start a fresh simulation: reset global Simulator instance
        # (Your background_simulation will create a new Simulator)
        simulation_thread = threading.Thread(target=background_simulation, args=(start_date_obj, duration, {phase.lower(): phase in phases for phase in ['ENABLE_WIND', 'ENABLE_IMPORT_PHASE1', 'ENABLE_LOCAL_HYDRO', 'ENABLE_IMPORT_PHASE2', 'ENABLE_TWO_HOP']},demand_factor, wind_factor, inflow_factor, fill_level_factor))
        simulation_thread.start()
        simulation_running = True
        return True  # disable start button while simulation runs
    elif button_id == "skip-simulation-btn" and not simulation_running:
        # Wait for the simulation thread to finish quickly
        #if simulation_thread is not None:
        #    simulation_thread.join()
        # Set current_index to the final simulation result index:
        if simulator_instance and simulator_instance.results:
            current_index = len(simulator_instance.results) - 1
        else:
            current_index = 0
        return False  # re-enable start button after simulation
    return False

# -------------------------
# Run the App
# -------------------------
if __name__ == '__main__':
    app.run(debug=(sys.gettrace() is None))
