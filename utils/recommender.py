import pandas as pd


CHART_TYPES = {
    "histogram": {"ad": "Histogram", "ikon": "📊"},
    "bar": {"ad": "Çubuk Grafik", "ikon": "📊"},
    "line": {"ad": "Çizgi Grafik", "ikon": "📈"},
    "box": {"ad": "Kutu Grafik", "ikon": "📦"},
    "scatter": {"ad": "Saçılım Grafiği", "ikon": "🔵"},
    "heatmap": {"ad": "Korelasyon Isı Haritası", "ikon": "🟥"},
    "pie": {"ad": "Pasta Grafik", "ikon": "🥧"},
    "area": {"ad": "Alan Grafik", "ikon": "📐"},
    "grouped_bar": {"ad": "Gruplu Çubuk Grafik", "ikon": "📊"},
}


def recommend_charts(df: pd.DataFrame, profile: dict) -> list[dict]:
    """Veri profiline göre uygun grafik türlerini önerir."""
    recommendations = []
    numeric = profile["numerik_sutunlar"]
    categorical = profile["kategorik_sutunlar"]
    dates = profile["tarih_sutunlari"]
    cardinality = profile["kardinalite"]

    # Tek numerik sütun -> Histogram
    for col in numeric:
        recommendations.append({
            "tip": "histogram",
            "sutunlar": [col],
            "baslik": f"{col} Dağılımı",
            "aciklama": f"{col} sütununun değer dağılımını gösterir.",
            "oncelik": 1,
        })

    # Tek kategorik sütun -> Çubuk Grafik / Pasta
    for col in categorical:
        info = cardinality.get(col, {})
        if info.get("tip") == "düşük":
            recommendations.append({
                "tip": "pie",
                "sutunlar": [col],
                "baslik": f"{col} Dağılımı",
                "aciklama": f"{col} kategorilerinin oransal dağılımını gösterir.",
                "oncelik": 2,
            })
        recommendations.append({
            "tip": "bar",
            "sutunlar": [col],
            "baslik": f"{col} Frekans Grafiği",
            "aciklama": f"{col} sütunundaki her kategorinin frekansını gösterir.",
            "oncelik": 2 if info.get("tip") != "düşük" else 3,
        })

    # Tarih + Numerik -> Çizgi Grafik
    for d_col in dates:
        for n_col in numeric[:3]:
            recommendations.append({
                "tip": "line",
                "sutunlar": [d_col, n_col],
                "baslik": f"{n_col} Zaman Trendi",
                "aciklama": f"{n_col} değerinin zamana göre değişimini gösterir.",
                "oncelik": 1,
            })
            recommendations.append({
                "tip": "area",
                "sutunlar": [d_col, n_col],
                "baslik": f"{n_col} Alan Grafiği",
                "aciklama": f"{n_col} değerinin zaman içindeki kümülatif görünümü.",
                "oncelik": 3,
            })

    # İki numerik sütun -> Saçılım
    if len(numeric) >= 2:
        for i in range(min(len(numeric), 4)):
            for j in range(i + 1, min(len(numeric), 4)):
                recommendations.append({
                    "tip": "scatter",
                    "sutunlar": [numeric[i], numeric[j]],
                    "baslik": f"{numeric[i]} vs {numeric[j]}",
                    "aciklama": f"İki değişken arasındaki ilişkiyi gösterir.",
                    "oncelik": 2,
                })

    # Çoklu numerik -> Korelasyon haritası
    if len(numeric) >= 3:
        recommendations.append({
            "tip": "heatmap",
            "sutunlar": numeric,
            "baslik": "Korelasyon Isı Haritası",
            "aciklama": "Numerik sütunlar arasındaki korelasyonları gösterir.",
            "oncelik": 1,
        })

    # Numerik aşırı yayılım -> Kutu Grafik
    for col in numeric:
        stats = profile["istatistikler"].get(col, {})
        if stats and abs(stats.get("çarpıklık", 0)) > 1.0:
            recommendations.append({
                "tip": "box",
                "sutunlar": [col],
                "baslik": f"{col} Kutu Grafiği",
                "aciklama": f"{col} sütununun dağılım ve aykırı değerlerini gösterir.",
                "oncelik": 2,
            })

    # Kategorik + Numerik -> Gruplu çubuk
    low_cat = [c for c in categorical if cardinality.get(c, {}).get("tip") in ("düşük", "orta")]
    for cat_col in low_cat[:3]:
        for num_col in numeric[:3]:
            recommendations.append({
                "tip": "grouped_bar",
                "sutunlar": [cat_col, num_col],
                "baslik": f"{cat_col} Bazında {num_col}",
                "aciklama": f"Her {cat_col} kategorisi için {num_col} ortalamasını karşılaştırır.",
                "oncelik": 2,
            })

    # Önceliğe göre sırala
    recommendations.sort(key=lambda x: x["oncelik"])
    return recommendations
