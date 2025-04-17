from dash import Dash, dcc, html, Input, Output, State
import numpy as np
import dash

services = [
    ("Timber", "#8B4513"),
    ("Climate Control", "#8A2BE2"),
    ("Habitat Maintenance", "#228B22"),
    ("Water Control", "#1E90FF"),
    ("Recreation", "#FFA500")
]

clearcut_matrix = np.array([
    [1.0, -0.7, -0.8, -0.5, -0.6],
    [-0.7, 1.0, 0.6, 0.7, 0.5],
    [-0.8, 0.6, 1.0, 0.5, -0.3],
    [-0.5, 0.7, 0.5, 1.0, 0.6],
    [-0.6, 0.5, -0.3, 0.6, 1.0]
])

matrices = {
    "Clearcut": clearcut_matrix,
    "Small Opening": clearcut_matrix * 0.65,
    "Selective Cut": clearcut_matrix * 0.50
}

regime_weights = {
    "Clearcut": 1.0,
    "Small Opening": 0.6,
    "Selective Cut": 0.45
}

GAMMA = 0.6

app = Dash(__name__, external_stylesheets=["/assets/styles.css"])

app.layout = html.Div([
    html.H3("Ecosystem Service Equalizer", style={"textAlign": "center"}),

    html.Div([
        html.Label("Assessment area (ha):"),
        dcc.Input(id="input-total-area", type="number", value=100, min=1, step=1),
        html.Label("Managed area (ha):", style={"marginLeft": "20px"}),
        dcc.Input(id="input-managed-area", type="number", value=100, min=0, step=1)
    ], style={"display": "flex", "justifyContent": "center", "gap": "10px", "marginBottom": "20px"}),

    html.Div([
        dcc.RadioItems(
            id="regime-selector",
            options=[{"label": k, "value": k} for k in matrices.keys()],
            value="Clearcut",
            inline=True,
            style={"display": "flex", "justifyContent": "center", "gap": "30px", "fontSize": "18px"}
        )
    ], style={"display": "flex", "justifyContent": "center", "marginBottom": "20px"}),

    html.Div([
        html.Div("Ecosystem Integrity", style={"textAlign": "center", "fontWeight": "bold", "marginBottom": "5px", "fontSize": "16px"}),
        dcc.Slider(
            id="ecosystem-integrity",
            min=-5,
            max=5,
            step=1,
            value=0,
            marks={i: {'label': str(i), 'style': {'color': 'black'}} for i in range(-5, 6)},
            tooltip={"always_visible": False},
            included=False
        ),
        html.Div([
            html.Span("Fragile", style={"color": "black", "marginRight": "auto"}),
            html.Span("Resilient", style={"color": "black", "marginLeft": "auto"})
        ], style={"display": "flex", "justifyContent": "space-between", "width": "100%", "marginTop": "4px"})
    ], style={"width": "60%", "margin": "0 auto 30px auto"}),

    html.Div([
        html.Div([
            html.Div(name, style={"textAlign": "center", "width": "100%", "marginBottom": "10px", "whiteSpace": "nowrap"}),
            dcc.Slider(
                min=(0 if i == 0 else -5),
                max=5,
                step=0.1,
                value=0,
                id=f"slider-{i}",
                vertical=True,
                updatemode='drag',
                marks={j: str(j) for j in range((0 if i == 0 else -5), 6)},
                tooltip={"always_visible": False},
                included=False,
                className=f"es-slider-{i}",
                disabled=(i != 0)
            )
        ], style={"display": "flex", "flexDirection": "column", "alignItems": "center", "justifyContent": "flex-start", "width": "100px", "margin": "0 20px"})
        for i, (name, _) in enumerate(services)
    ], style={"display": "flex", "justifyContent": "center", "gap": "20px", "marginBottom": "40px"}),

    html.Div([
        html.Button("Reset", id="reset-button", n_clicks=0)
    ], style={"display": "flex", "justifyContent": "flex-end", "marginRight": "60px", "marginTop": "30px"})

], style={"fontFamily": "sans-serif", "height": "100vh", "overflowY": "visible"})

@app.callback(
    [Output(f"slider-{i}", "value") for i in range(5)],
    [Input("slider-0", "value"), Input("reset-button", "n_clicks")],
    [State("regime-selector", "value"), State("input-total-area", "value"), State("input-managed-area", "value"), State("ecosystem-integrity", "value")]
)
def update_from_timber(timber_value, reset_clicks, regime, total_area, managed_area, integrity):
    ctx = dash.callback_context
    if not ctx.triggered or total_area is None or total_area <= 0:
        return [0] * 5

    if ctx.triggered[0]['prop_id'] == "reset-button.n_clicks":
        return [0] * 5

    fraction = managed_area / total_area if managed_area and total_area else 0
    regime_weight = regime_weights[regime]
    raw_factor = fraction * regime_weight
    impact_factor = raw_factor ** GAMMA

    condition_multiplier = np.interp(integrity, [-5, 0, 5], [2.0, 1.0, 0.5])

    matrix_row = matrices[regime][0]
    result = matrix_row * timber_value * impact_factor * condition_multiplier
    result[0] = timber_value
    result = np.clip(result, -5, 5)
    return result.tolist()

import os
port = int(os.environ.get("PORT", 8050))
app.run(host="0.0.0.0", port=port)
