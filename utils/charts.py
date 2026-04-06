import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


COLOR_PALETTE = px.colors.qualitative.Set2
TEMPLATE = "plotly_white"


def create_chart(df: pd.DataFrame, rec: dict, profile: dict) -> go.Figure | None:
    """Öneriye göre Plotly grafiği oluşturur."""
    tip = rec["tip"]
    cols = rec["sutunlar"]
    baslik = rec["baslik"]

    try:
        if tip == "histogram":
            return _histogram(df, cols[0], baslik)
        elif tip == "bar":
            return _bar(df, cols[0], baslik)
        elif tip == "line":
            return _line(df, cols[0], cols[1], baslik, profile)
        elif tip == "area":
            return _area(df, cols[0], cols[1], baslik, profile)
        elif tip == "box":
            return _box(df, cols[0], baslik)
        elif tip == "scatter":
            return _scatter(df, cols[0], cols[1], baslik)
        elif tip == "heatmap":
            return _heatmap(df, cols, baslik)
        elif tip == "pie":
            return _pie(df, cols[0], baslik)
        elif tip == "grouped_bar":
            return _grouped_bar(df, cols[0], cols[1], baslik)
    except Exception:
        return None
    return None


def _base_layout(fig: go.Figure, baslik: str) -> go.Figure:
    fig.update_layout(
        title=dict(text=baslik, font=dict(size=16)),
        template=TEMPLATE,
        height=450,
        margin=dict(t=60, b=40, l=40, r=20),
        font=dict(size=12),
    )
    return fig


def _histogram(df, col, baslik):
    fig = px.histogram(df, x=col, nbins=40, color_discrete_sequence=COLOR_PALETTE)
    fig.update_layout(xaxis_title=col, yaxis_title="Frekans")
    return _base_layout(fig, baslik)


def _bar(df, col, baslik):
    counts = df[col].value_counts().head(20).reset_index()
    counts.columns = [col, "Adet"]
    fig = px.bar(counts, x=col, y="Adet", color_discrete_sequence=COLOR_PALETTE)
    fig.update_layout(xaxis_title=col, yaxis_title="Adet")
    return _base_layout(fig, baslik)


def _line(df, date_col, num_col, baslik, profile):
    tmp = df[[date_col, num_col]].copy()
    if not pd.api.types.is_datetime64_any_dtype(tmp[date_col]):
        tmp[date_col] = pd.to_datetime(tmp[date_col], format="mixed", dayfirst=True, errors="coerce")
    tmp = tmp.dropna(subset=[date_col])
    agg = tmp.groupby(date_col)[num_col].mean().reset_index().sort_values(date_col)
    fig = px.line(agg, x=date_col, y=num_col, color_discrete_sequence=COLOR_PALETTE)
    fig.update_layout(xaxis_title="Tarih", yaxis_title=num_col)
    return _base_layout(fig, baslik)


def _area(df, date_col, num_col, baslik, profile):
    tmp = df[[date_col, num_col]].copy()
    if not pd.api.types.is_datetime64_any_dtype(tmp[date_col]):
        tmp[date_col] = pd.to_datetime(tmp[date_col], format="mixed", dayfirst=True, errors="coerce")
    tmp = tmp.dropna(subset=[date_col])
    agg = tmp.groupby(date_col)[num_col].sum().reset_index().sort_values(date_col)
    fig = px.area(agg, x=date_col, y=num_col, color_discrete_sequence=COLOR_PALETTE)
    fig.update_layout(xaxis_title="Tarih", yaxis_title=num_col)
    return _base_layout(fig, baslik)


def _box(df, col, baslik):
    fig = px.box(df, y=col, color_discrete_sequence=COLOR_PALETTE)
    fig.update_layout(yaxis_title=col)
    return _base_layout(fig, baslik)


def _scatter(df, col1, col2, baslik):
    sample = df if len(df) <= 2000 else df.sample(2000, random_state=42)
    fig = px.scatter(sample, x=col1, y=col2, opacity=0.6, color_discrete_sequence=COLOR_PALETTE)
    fig.update_layout(xaxis_title=col1, yaxis_title=col2)
    return _base_layout(fig, baslik)


def _heatmap(df, cols, baslik):
    corr = df[cols].corr()
    fig = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=corr.columns.tolist(),
        y=corr.index.tolist(),
        colorscale="RdBu_r",
        zmin=-1,
        zmax=1,
        text=np.round(corr.values, 2),
        texttemplate="%{text}",
        textfont=dict(size=11),
    ))
    return _base_layout(fig, baslik)


def _pie(df, col, baslik):
    counts = df[col].value_counts().head(10)
    fig = px.pie(values=counts.values, names=counts.index, color_discrete_sequence=COLOR_PALETTE)
    return _base_layout(fig, baslik)


def _grouped_bar(df, cat_col, num_col, baslik):
    agg = df.groupby(cat_col)[num_col].mean().reset_index().sort_values(num_col, ascending=False).head(20)
    fig = px.bar(agg, x=cat_col, y=num_col, color_discrete_sequence=COLOR_PALETTE)
    fig.update_layout(xaxis_title=cat_col, yaxis_title=f"Ortalama {num_col}")
    return _base_layout(fig, baslik)


def create_manual_chart(df: pd.DataFrame, chart_type: str, x_col: str,
                        y_col: str | None, color_col: str | None, agg: str) -> go.Figure | None:
    """Kullanıcı seçimlerine göre manuel grafik oluşturur."""
    try:
        if chart_type == "Histogram":
            fig = px.histogram(df, x=x_col, color=color_col, nbins=40,
                               color_discrete_sequence=COLOR_PALETTE)
            return _base_layout(fig, f"{x_col} Histogram")

        if chart_type == "Kutu Grafik":
            fig = px.box(df, x=color_col, y=x_col, color=color_col,
                         color_discrete_sequence=COLOR_PALETTE)
            return _base_layout(fig, f"{x_col} Kutu Grafiği")

        if chart_type == "Pasta Grafik":
            counts = df[x_col].value_counts().head(10)
            fig = px.pie(values=counts.values, names=counts.index,
                         color_discrete_sequence=COLOR_PALETTE)
            return _base_layout(fig, f"{x_col} Pasta Grafiği")

        if not y_col:
            return None

        agg_map = {"Toplam": "sum", "Ortalama": "mean", "Medyan": "median",
                   "Minimum": "min", "Maksimum": "max", "Sayım": "count"}
        agg_func = agg_map.get(agg, "mean")
        grouped = df.groupby(x_col)[y_col].agg(agg_func).reset_index()

        if chart_type == "Çubuk Grafik":
            fig = px.bar(grouped, x=x_col, y=y_col, color_discrete_sequence=COLOR_PALETTE)
        elif chart_type == "Çizgi Grafik":
            grouped = grouped.sort_values(x_col)
            fig = px.line(grouped, x=x_col, y=y_col, color_discrete_sequence=COLOR_PALETTE)
        elif chart_type == "Alan Grafik":
            grouped = grouped.sort_values(x_col)
            fig = px.area(grouped, x=x_col, y=y_col, color_discrete_sequence=COLOR_PALETTE)
        elif chart_type == "Saçılım Grafiği":
            sample = df if len(df) <= 2000 else df.sample(2000, random_state=42)
            fig = px.scatter(sample, x=x_col, y=y_col, color=color_col,
                             opacity=0.6, color_discrete_sequence=COLOR_PALETTE)
        else:
            return None

        return _base_layout(fig, f"{x_col} - {y_col} ({agg})")
    except Exception:
        return None
