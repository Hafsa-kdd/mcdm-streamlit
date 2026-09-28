"""Graphiques Plotly aux couleurs de l'application."""
import numpy as np
import plotly.graph_objects as go

VIOLET, PINK, LAVENDER = "#8B5CF6", "#EC4899", "#D9CCFB"
PALETTE = ["#8B5CF6", "#EC4899", "#A78BFA", "#F472B6", "#6366F1", "#C084FC", "#FB7185", "#818CF8"]


def _layout(fig, height=340):
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Poppins, sans-serif", color="#2E2A47", size=13),
        showlegend=False,
    )
    return fig


def weights_donut(criteria, weights):
    fig = go.Figure(go.Pie(
        labels=criteria, values=weights, hole=0.62, sort=False,
        marker=dict(colors=PALETTE, line=dict(color="white", width=3)),
        textinfo="percent", hovertemplate="%{label} : %{percent}<extra></extra>",
    ))
    return _layout(fig, 320).update_layout(showlegend=True, legend=dict(orientation="h", y=-0.08, x=0.5, xanchor="center"))


def scores_bar(names, scores):
    order = np.argsort(scores)  # du plus faible au meilleur (le meilleur en haut)
    names, scores = [names[i] for i in order], scores[order]
    colors = [LAVENDER] * (len(names) - 1) + [VIOLET]
    fig = go.Figure(go.Bar(
        x=scores, y=names, orientation="h", marker=dict(color=colors, cornerradius=10),
        text=[f"{s:.3f}" for s in scores], textposition="outside",
        hovertemplate="%{y} : %{x:.4f}<extra></extra>",
    ))
    fig.update_xaxes(visible=False, range=[0, max(scores.max() * 1.18, 1e-9)])
    fig.update_yaxes(showgrid=False)
    return _layout(fig, 60 + 48 * len(names))


def radar(criteria, profiles):
    """profiles : dict {nom de l'option: valeurs normalisées entre 0 et 1}."""
    fig = go.Figure()
    for (name, values), color in zip(profiles.items(), PALETTE):
        fig.add_trace(go.Scatterpolar(
            r=list(values) + [values[0]], theta=criteria + [criteria[0]], name=name,
            fill="toself", line=dict(color=color, width=2), opacity=0.55,
        ))
    fig.update_layout(
        polar=dict(bgcolor="rgba(0,0,0,0)",
                   radialaxis=dict(range=[0, 1], showticklabels=False, gridcolor="#E6E0FA"),
                   angularaxis=dict(gridcolor="#E6E0FA")),
        legend=dict(orientation="h", y=-0.12),
    )
    return _layout(fig, 360).update_layout(showlegend=True, margin=dict(l=60, r=60, t=30, b=10))
