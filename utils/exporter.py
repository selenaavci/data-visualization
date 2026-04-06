import io
import zipfile
import pandas as pd
import plotly.graph_objects as go


def fig_to_png_bytes(fig: go.Figure) -> bytes:
    """Plotly figürünü PNG byte'larına dönüştürür."""
    return fig.to_image(format="png", width=1000, height=500, scale=2)


def fig_to_html(fig: go.Figure) -> str:
    """Plotly figürünü HTML string olarak döndürür."""
    return fig.to_html(include_plotlyjs="cdn", full_html=False)


def create_zip_package(figures: list[tuple[str, go.Figure]]) -> bytes:
    """Grafikleri HTML olarak ZIP paketine dönüştürür."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, (title, fig) in enumerate(figures, 1):
            safe_name = title.replace(" ", "_").replace("/", "_")[:50]
            html = fig.to_html(include_plotlyjs="cdn", full_html=True)
            zf.writestr(f"{i:02d}_{safe_name}.html", html)

        # Özet tablosu
        summary_rows = []
        for i, (title, _) in enumerate(figures, 1):
            summary_rows.append({"No": i, "Grafik Adı": title})
        summary_df = pd.DataFrame(summary_rows)
        csv_bytes = summary_df.to_csv(index=False).encode("utf-8-sig")
        zf.writestr("grafik_ozeti.csv", csv_bytes)

    return buf.getvalue()


def create_summary_df(recommendations: list[dict]) -> pd.DataFrame:
    """Önerilerin özet tablosunu oluşturur."""
    rows = []
    for i, rec in enumerate(recommendations, 1):
        rows.append({
            "No": i,
            "Grafik Türü": rec["tip"],
            "Başlık": rec["baslik"],
            "Sütunlar": ", ".join(rec["sutunlar"]),
            "Açıklama": rec["aciklama"],
        })
    return pd.DataFrame(rows)
