import pandas as pd
import numpy as np


def profile_dataset(df: pd.DataFrame) -> dict:
    """Veri setini analiz eder ve profil bilgisi döndürür."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # Tarih sütunlarını tespit et
    date_cols = []
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date_cols.append(col)
        elif col in categorical_cols:
            sample = df[col].dropna().head(50)
            try:
                parsed = pd.to_datetime(sample, format="mixed", dayfirst=True)
                if parsed.notna().sum() > len(sample) * 0.8:
                    date_cols.append(col)
                    categorical_cols.remove(col)
            except (ValueError, TypeError):
                pass

    # Kardinalite bilgisi
    cardinality = {}
    for col in categorical_cols:
        nunique = df[col].nunique()
        cardinality[col] = {
            "benzersiz_deger": nunique,
            "tip": "düşük" if nunique <= 10 else ("orta" if nunique <= 50 else "yüksek"),
        }

    # Eksik değer bilgisi
    missing = {}
    for col in df.columns:
        count = df[col].isna().sum()
        if count > 0:
            missing[col] = {
                "adet": int(count),
                "oran": round(count / len(df) * 100, 2),
            }

    # Temel istatistikler
    stats = {}
    for col in numeric_cols:
        s = df[col].describe()
        skew = df[col].skew()
        stats[col] = {
            "ortalama": round(s["mean"], 2),
            "medyan": round(s["50%"], 2),
            "std": round(s["std"], 2),
            "min": round(s["min"], 2),
            "max": round(s["max"], 2),
            "çarpıklık": round(skew, 2),
        }

    return {
        "satir_sayisi": len(df),
        "sutun_sayisi": len(df.columns),
        "numerik_sutunlar": numeric_cols,
        "kategorik_sutunlar": categorical_cols,
        "tarih_sutunlari": date_cols,
        "kardinalite": cardinality,
        "eksik_degerler": missing,
        "istatistikler": stats,
    }


def get_highlights(df: pd.DataFrame, profile: dict) -> list[str]:
    """Veri setindeki öne çıkan bulguları listeler."""
    highlights = []

    highlights.append(f"Veri seti **{profile['satir_sayisi']:,}** satır ve **{profile['sutun_sayisi']}** sütundan oluşuyor.")

    if profile["eksik_degerler"]:
        total_missing = sum(v["adet"] for v in profile["eksik_degerler"].values())
        highlights.append(f"Toplam **{total_missing:,}** eksik değer tespit edildi.")
    else:
        highlights.append("Eksik değer bulunmuyor.")

    for col, s in profile["istatistikler"].items():
        if abs(s["çarpıklık"]) > 1.5:
            yön = "sağa" if s["çarpıklık"] > 0 else "sola"
            highlights.append(f"**{col}** sütunu belirgin şekilde {yön} çarpık (çarpıklık: {s['çarpıklık']}).")

    for col, info in profile["kardinalite"].items():
        if info["tip"] == "düşük":
            top_val = df[col].value_counts().index[0]
            top_pct = round(df[col].value_counts(normalize=True).iloc[0] * 100, 1)
            highlights.append(f"**{col}** sütununda en sık değer: **{top_val}** (%{top_pct}).")

    for col in profile["numerik_sutunlar"][:3]:
        min_val = df[col].min()
        max_val = df[col].max()
        highlights.append(f"**{col}**: min={min_val:,.2f}, maks={max_val:,.2f}")

    return highlights
