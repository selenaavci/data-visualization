import streamlit as st
import pandas as pd
import numpy as np
import io

from utils.profiler import profile_dataset, get_highlights
from utils.recommender import recommend_charts, CHART_TYPES
from utils.charts import create_chart, create_manual_chart
from utils.exporter import create_zip_package, create_summary_df

# ---------------------------------------------------------------------------
# Sayfa Ayarları
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Data Visualization Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Başlık
# ---------------------------------------------------------------------------
st.title("Data Visualization Agent")
st.caption("Veri setinizi yükleyin, otomatik analiz ve görselleştirme önerileri alın.")

# ---------------------------------------------------------------------------
# Kenar Çubuğu - Dosya Yükleme
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Dosya Yükleme")
    uploaded_file = st.file_uploader(
        "CSV veya Excel dosyası yükleyin",
        type=["csv", "xlsx", "xls"],
        help="Maksimum 200 MB boyutunda dosya yükleyebilirsiniz.",
    )

    use_sample = st.checkbox("Örnek veri seti kullan", value=False)

    st.divider()
    st.markdown(
        "**Desteklenen formatlar:** CSV, XLSX\n\n"
        "**Özellikler:**\n"
        "- Otomatik veri profilleme\n"
        "- Akıllı grafik önerisi\n"
        "- Manuel grafik oluşturma\n"
        "- Toplu dışa aktarma"
    )


# ---------------------------------------------------------------------------
# Veri Yükleme
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Veri okunuyor...")
def load_data(file, filename: str) -> pd.DataFrame:
    if filename.endswith(".csv"):
        try:
            return pd.read_csv(file, encoding="utf-8-sig")
        except UnicodeDecodeError:
            file.seek(0)
            return pd.read_csv(file, encoding="latin-1")
    else:
        return pd.read_excel(file)


@st.cache_data(show_spinner="Örnek veri yükleniyor...")
def load_sample() -> pd.DataFrame:
    return pd.read_csv("ornek_veri/demo_DataVis.csv", encoding="utf-8-sig")


df = None
if uploaded_file is not None:
    df = load_data(uploaded_file, uploaded_file.name)
elif use_sample:
    try:
        df = load_sample()
    except FileNotFoundError:
        st.error("Örnek veri seti bulunamadı. Lütfen `sentetik_veri_olustur.py` scriptini çalıştırın.")
        st.stop()

if df is None:
    st.info("Başlamak için kenar çubuğundan bir dosya yükleyin veya örnek veri setini seçin.")
    st.stop()

# ---------------------------------------------------------------------------
# Tarih sütunlarını dönüştür
# ---------------------------------------------------------------------------
for col in df.columns:
    if df[col].dtype == "object":
        sample = df[col].dropna().head(30)
        try:
            parsed = pd.to_datetime(sample, format="mixed", dayfirst=True)
            if parsed.notna().sum() > len(sample) * 0.8:
                df[col] = pd.to_datetime(df[col], format="mixed", dayfirst=True, errors="coerce")
        except (ValueError, TypeError):
            pass

# ---------------------------------------------------------------------------
# Profilleme
# ---------------------------------------------------------------------------
profile = profile_dataset(df)

# ---------------------------------------------------------------------------
# Sekmeler
# ---------------------------------------------------------------------------
tab_preview, tab_profile, tab_auto, tab_manual, tab_export = st.tabs([
    "Veri Önizleme",
    "Veri Profili",
    "Otomatik Grafikler",
    "Manuel Grafik",
    "Dışa Aktarma",
])

# ===================== Sekme 1: Veri Önizleme =============================
with tab_preview:
    st.subheader("Veri Seti Önizleme")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Satır Sayısı", f"{profile['satir_sayisi']:,}")
    col2.metric("Sütun Sayısı", profile["sutun_sayisi"])
    col3.metric("Numerik Sütun", len(profile["numerik_sutunlar"]))
    col4.metric("Kategorik Sütun", len(profile["kategorik_sutunlar"]))

    st.dataframe(df.head(100), use_container_width=True, height=400)

    with st.expander("Sütun Bilgileri"):
        col_info = []
        for col in df.columns:
            col_info.append({
                "Sütun": col,
                "Veri Tipi": str(df[col].dtype),
                "Benzersiz Değer": df[col].nunique(),
                "Eksik Değer": df[col].isna().sum(),
                "Örnek Değer": str(df[col].dropna().iloc[0]) if len(df[col].dropna()) > 0 else "-",
            })
        st.dataframe(pd.DataFrame(col_info), use_container_width=True, hide_index=True)

# ===================== Sekme 2: Veri Profili ==============================
with tab_profile:
    st.subheader("Otomatik Veri Profili")

    # Öne çıkan bulgular
    highlights = get_highlights(df, profile)
    st.markdown("#### Öne Çıkan Bulgular")
    for h in highlights:
        st.markdown(f"- {h}")

    # İstatistikler
    if profile["istatistikler"]:
        st.markdown("#### Numerik Sütun İstatistikleri")
        stats_df = pd.DataFrame(profile["istatistikler"]).T
        stats_df.index.name = "Sütun"
        st.dataframe(stats_df, use_container_width=True)

    # Eksik değerler
    if profile["eksik_degerler"]:
        st.markdown("#### Eksik Değerler")
        miss_df = pd.DataFrame(profile["eksik_degerler"]).T
        miss_df.index.name = "Sütun"
        miss_df.columns = ["Adet", "Oran (%)"]
        st.dataframe(miss_df, use_container_width=True)

    # Kardinalite
    if profile["kardinalite"]:
        st.markdown("#### Kategorik Sütun Kardinalitesi")
        card_rows = []
        for col, info in profile["kardinalite"].items():
            card_rows.append({
                "Sütun": col,
                "Benzersiz Değer": info["benzersiz_deger"],
                "Kardinalite": info["tip"].capitalize(),
            })
        st.dataframe(pd.DataFrame(card_rows), use_container_width=True, hide_index=True)

# ===================== Sekme 3: Otomatik Grafikler ========================
with tab_auto:
    st.subheader("Otomatik Grafik Önerileri")

    recommendations = recommend_charts(df, profile)

    if not recommendations:
        st.warning("Bu veri seti için otomatik grafik önerisi oluşturulamadı.")
    else:
        # Filtre
        available_types = sorted(set(r["tip"] for r in recommendations))
        type_labels = {t: f"{CHART_TYPES[t]['ikon']} {CHART_TYPES[t]['ad']}" for t in available_types}

        with st.sidebar:
            st.divider()
            st.subheader("Grafik Filtreleri")
            selected_types = st.multiselect(
                "Grafik türü seçin",
                options=available_types,
                format_func=lambda t: type_labels[t],
                default=available_types,
            )
            max_charts = st.slider("Maksimum grafik sayısı", 1, 30, 10)

        filtered = [r for r in recommendations if r["tip"] in selected_types][:max_charts]

        st.info(f"Toplam **{len(recommendations)}** grafik önerisi oluşturuldu. Gösterilen: **{len(filtered)}**")

        # Grafik özetleri tablosu
        with st.expander("Grafik Önerileri Tablosu"):
            summary = create_summary_df(filtered)
            st.dataframe(summary, use_container_width=True, hide_index=True)

        # Grafikleri oluştur
        generated_figures = []
        for i, rec in enumerate(filtered):
            fig = create_chart(df, rec, profile)
            if fig is not None:
                generated_figures.append((rec["baslik"], fig))
                type_info = CHART_TYPES.get(rec["tip"], {})
                st.markdown(f"**{type_info.get('ikon', '')} {rec['baslik']}** — _{rec['aciklama']}_")
                st.plotly_chart(fig, use_container_width=True, key=f"auto_{i}")
                st.divider()

        # Session state'e kaydet (export için)
        st.session_state["generated_figures"] = generated_figures

# ===================== Sekme 4: Manuel Grafik =============================
with tab_manual:
    st.subheader("Manuel Grafik Oluşturma")
    st.markdown("Kendi grafik ayarlarınızı seçerek özel bir görselleştirme oluşturun.")

    mc1, mc2 = st.columns(2)

    with mc1:
        chart_type = st.selectbox(
            "Grafik Türü",
            ["Çubuk Grafik", "Çizgi Grafik", "Histogram", "Saçılım Grafiği",
             "Alan Grafik", "Kutu Grafik", "Pasta Grafik"],
        )
        x_col = st.selectbox("X Ekseni / Ana Sütun", df.columns.tolist())

    with mc2:
        y_options = ["(Yok)"] + df.columns.tolist()
        y_col = st.selectbox("Y Ekseni (isteğe bağlı)", y_options)
        if y_col == "(Yok)":
            y_col = None

        color_options = ["(Yok)"] + profile["kategorik_sutunlar"]
        color_col = st.selectbox("Renk Grubu (isteğe bağlı)", color_options)
        if color_col == "(Yok)":
            color_col = None

    agg_method = st.selectbox(
        "Toplama Yöntemi",
        ["Toplam", "Ortalama", "Medyan", "Minimum", "Maksimum", "Sayım"],
    )

    if st.button("Grafik Oluştur", type="primary", use_container_width=True):
        fig = create_manual_chart(df, chart_type, x_col, y_col, color_col, agg_method)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Bu ayarlarla grafik oluşturulamadı. Lütfen sütun seçimlerinizi kontrol edin.")

# ===================== Sekme 5: Dışa Aktarma ==============================
with tab_export:
    st.subheader("Grafikleri Dışa Aktar")

    figures = st.session_state.get("generated_figures", [])

    if not figures:
        st.info("Önce **Otomatik Grafikler** sekmesinden grafik oluşturun.")
    else:
        st.success(f"**{len(figures)}** grafik dışa aktarılmaya hazır.")

        # ZIP paketi
        if st.button("ZIP Paketi Oluştur (HTML)", type="primary", use_container_width=True):
            with st.spinner("Paket hazırlanıyor..."):
                zip_bytes = create_zip_package(figures)
            st.download_button(
                label="ZIP Dosyasını İndir",
                data=zip_bytes,
                file_name="grafikler_paketi.zip",
                mime="application/zip",
                use_container_width=True,
            )

        # Özet tablosu
        st.markdown("#### Grafik Özet Tablosu")
        summary_rows = [{"No": i + 1, "Grafik Adı": t} for i, (t, _) in enumerate(figures)]
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

        # CSV olarak özeti indir
        summary_csv = pd.DataFrame(summary_rows).to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="Özet Tablosunu İndir (CSV)",
            data=summary_csv,
            file_name="grafik_ozeti.csv",
            mime="text/csv",
            use_container_width=True,
        )
