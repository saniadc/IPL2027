"""Plotly chart builders. Each takes a DataFrame already filtered by the caller and returns a figure.
Styling is applied in one place (apply_theme) so every chart looks the same."""
import plotly.express as px
import plotly.graph_objects as go

PALETTE = {"pressure": "#8b1a4a", "non_pressure": "#1f4e79", "accent": "#c9a227", "muted": "#7f8c8d",
           "ink": "#0b2545", "good": "#1e7b4f"}
SERIES = ["#8b1a4a", "#1f4e79", "#c9a227", "#2e8b57", "#7f8c8d", "#6a3d9a"]


def apply_theme(fig, title="", xlabel=None, ylabel=None):
    fig.update_layout(
        title=dict(text=title, x=0.0, xanchor="left", font=dict(size=16, color=PALETTE["ink"])),
        template="plotly_white", font=dict(family="Segoe UI, Arial, sans-serif", size=13, color="#222"),
        height=380, margin=dict(l=20, r=20, t=60, b=40), legend=dict(orientation="h", yanchor="bottom", y=-0.25, title_text=""),
        colorway=SERIES, hoverlabel=dict(font_size=12),
    )
    if xlabel is not None:
        fig.update_xaxes(title_text=xlabel)
    if ylabel is not None:
        fig.update_yaxes(title_text=ylabel)
    return fig


def hist(df, col, color=None, title="", xlabel=""):
    """Share of each group's states per bin, so the small pressure group is readable next to the large one."""
    fig = px.histogram(df, x=col, color=color, nbins=40, barmode="overlay", opacity=0.6, histnorm="percent",
                       color_discrete_sequence=[PALETTE["pressure"], PALETTE["non_pressure"]])
    return apply_theme(fig, title, xlabel, "% of each group")


def bar(df, x, y, title="", ylabel="", color=None):
    fig = px.bar(df, x=x, y=y, color=color)
    return apply_theme(fig, title, None, ylabel)


def line(df, x, y, color=None, title="", ylabel=""):
    fig = px.line(df, x=x, y=y, color=color, markers=True)
    return apply_theme(fig, title, None, ylabel)


def scatter_ci(df, x, y, err, text, title, xlabel, ylabel):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[x], y=df[y], mode="markers", text=df[text],
        error_y=dict(type="data", array=df[err], visible=True, color="#999"),
        marker=dict(size=10, color=PALETTE["pressure"]),
        hovertemplate="%{text}<br>" + xlabel + "=%{x:.3f}<br>" + ylabel + "=%{y:.3f}<extra></extra>"))
    fig.add_hline(y=0, line_dash="dot", line_color=PALETTE["muted"])
    fig.update_layout(showlegend=False)
    return apply_theme(fig, title, xlabel, ylabel)


def grouped_bars(df, categories, values, title, ylabel):
    fig = go.Figure()
    for cat in values:
        fig.add_trace(go.Bar(name=cat, x=df[categories], y=df[cat]))
    fig.update_layout(barmode="group")
    return apply_theme(fig, title, None, ylabel)


def calibration(bins):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=bins.predicted, y=bins.observed, mode="markers", name="bins",
        marker=dict(size=bins.n / bins.n.max() * 30 + 5, color=PALETTE["pressure"]), text=bins.n,
        hovertemplate="predicted=%{x:.3f}<br>observed=%{y:.3f}<br>n=%{text}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", line=dict(dash="dot", color=PALETTE["muted"]),
                             name="perfect calibration"))
    return apply_theme(fig, "Out-of-fold calibration, second innings (marker size = bin count)",
                       "predicted win probability", "observed win rate")


def heatmap(mat, title, colorbar_title="share"):
    """Rows = players, columns = categories, values in 0-1 shares."""
    import plotly.graph_objects as go
    fig = go.Figure(go.Heatmap(z=mat.values, x=list(mat.columns), y=list(mat.index), zmin=0,
                               colorscale=[[0, "#f7f4ee"], [0.5, "#c9a227"], [1, "#8b1a4a"]],
                               colorbar=dict(title=colorbar_title, tickformat=".0%"),
                               hovertemplate="%{y}<br>%{x}: %{z:.1%}<extra></extra>"))
    fig.update_xaxes(tickangle=-35)
    return apply_theme(fig, title)


def scatter_xy(df, x, y, text, title, xlabel, ylabel):
    """Labelled scatter of two rates per player. Points are raw descriptive values, not estimates."""
    fig = go.Figure(go.Scatter(
        x=df[x], y=df[y], mode="markers", text=df[text],
        marker=dict(size=10, color=PALETTE["pressure"], line=dict(width=1, color="white")),
        hovertemplate="%{text}<br>" + xlabel + ": %{x:.1f}<br>" + ylabel + ": %{y:.1f}<extra></extra>"))
    return apply_theme(fig, title, xlabel, ylabel)
