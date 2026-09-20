# -*- coding: utf-8 -*-
"""
TUGU SHIELD-WtE DIGITAL DASHBOARD
==================================
End-to-End Life Cycle Waste-to-Energy (WtE) Comprehensive Insurance Solution
untuk PT Asuransi Tugu Pratama Indonesia Tbk.

Disediakan untuk Peringkat Semifinal IDEANATION 2026. Skop dashboard ini
mencakup keseluruhan rantaian nilai proyek WtE — daripada pengangkutan
sampah, pembangunan fasilitas, operasi harian, pasokan sampah parametrik,
sehingga distribusi listrik & monetisasi karbon — bukan sekadar modul
Feedstock De-risking & Green Rebate asas.

Jalankan dengan:
    streamlit run app.py

Requirements (requirements.txt):
    streamlit>=1.30
    pandas>=2.0
    numpy>=1.24
    plotly>=5.20
"""

import io
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# =====================================================================================
# 1. PAGE CONFIG & CUSTOM THEME (Pastel Enterprise Aesthetic)
# =====================================================================================
st.set_page_config(
    page_title="TUGU SHIELD-WtE Dashboard",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded",
)

PRIMARY_DARK_PURPLE = "#6A0DAD"
SECONDARY_PURPLE = "#A569BD"
PASTEL_PINK = "#F7C6D9"
HIGHLIGHT_PINK = "#F2A7C6"
NEUTRAL_BG = "#FAFAFC"

CUSTOM_CSS = f"""
<style>
:root {{
    --primary-dark-purple: {PRIMARY_DARK_PURPLE};
    --secondary-purple: {SECONDARY_PURPLE};
    --pastel-pink: {PASTEL_PINK};
    --highlight-pink: {HIGHLIGHT_PINK};
    --neutral-bg: {NEUTRAL_BG};
}}

/* App background */
.stApp {{
    background-color: var(--neutral-bg);
}}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background-color: var(--pastel-pink);
    border-right: 2px solid var(--secondary-purple);
}}
section[data-testid="stSidebar"] * {{
    color: #3A0A5C;
}}

/* Headers */
h1, h2, h3 {{
    color: var(--primary-dark-purple) !important;
    font-weight: 700;
}}

/* Top narrative banner */
.hero-banner {{
    background: linear-gradient(90deg, var(--primary-dark-purple), var(--secondary-purple));
    padding: 20px 28px;
    border-radius: 14px;
    color: white;
    font-size: 15px;
    font-style: italic;
    line-height: 1.5;
    margin-bottom: 18px;
    box-shadow: 0 4px 14px rgba(106,13,173,0.25);
}}

/* KPI cards */
.kpi-card {{
    background-color: white;
    border: 1.5px solid var(--secondary-purple);
    border-left: 6px solid var(--primary-dark-purple);
    border-radius: 12px;
    padding: 16px 18px;
    box-shadow: 0 2px 8px rgba(106,13,173,0.08);
    min-height: 96px;
}}
.kpi-label {{
    font-size: 13px;
    color: #6b6b6b;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.4px;
}}
.kpi-value {{
    font-size: 26px;
    color: var(--primary-dark-purple);
    font-weight: 800;
}}
.kpi-sub {{
    font-size: 12px;
    color: #8a8a8a;
}}

/* Badge */
.green-badge {{
    background-color: var(--pastel-pink);
    border: 2px dashed var(--primary-dark-purple);
    border-radius: 16px;
    padding: 18px;
    text-align: center;
}}
.green-badge h2 {{
    margin: 0;
    color: var(--primary-dark-purple) !important;
}}

/* Phase card (Tab 1 lifecycle) */
.phase-card {{
    background-color: white;
    border: 1.5px solid var(--secondary-purple);
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 10px;
}}
.phase-title {{
    color: var(--primary-dark-purple);
    font-weight: 800;
    font-size: 15px;
    margin-bottom: 4px;
}}
.phase-product {{
    display: inline-block;
    background-color: var(--pastel-pink);
    color: #3A0A5C;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 12px;
    font-weight: 700;
    margin-top: 6px;
}}

/* Buttons */
.stButton>button, .stDownloadButton>button {{
    background-color: var(--primary-dark-purple);
    color: white;
    border-radius: 8px;
    border: none;
    font-weight: 600;
}}
.stButton>button:hover, .stDownloadButton>button:hover {{
    background-color: var(--secondary-purple);
    color: white;
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
    gap: 6px;
    flex-wrap: wrap;
}}
.stTabs [data-baseweb="tab"] {{
    background-color: white;
    border: 1px solid var(--secondary-purple);
    border-radius: 8px 8px 0 0;
    padding: 8px 16px;
}}
.stTabs [aria-selected="true"] {{
    background-color: var(--secondary-purple) !important;
    color: white !important;
}}

.footer-note {{
    text-align: center;
    color: #9a9a9a;
    font-size: 12px;
    margin-top: 30px;
}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# =====================================================================================
# 2. KONSTANTA & ASUMSI GLOBAL
# =====================================================================================
# Sasaran & ambang batas tonase mengikuti piawaian minimum Perpres No. 35 Tahun 2018
# tentang Percepatan Pembangunan Instalasi Pengolah Sampah Menjadi Energi Listrik.
TARGET_TON_PER_DAY = 1000.0
THRESHOLD_TON_PER_DAY = 850.0

ASH_RATIO_OF_INPUT = 0.20                 # asumsi: abu (fly+bottom ash) = 20% dari input sampah
EMISSION_FACTOR_TCO2_PER_TON_ASH = 0.45   # asumsi reduksi emisi per ton abu yang diolah sirkular
USD_PER_TCO2E = 10.0                      # asumsi nilai kredit karbon voluntary market
DEFAULT_KURS_USD_IDR = 15_800.0           # asumsi kurs acuan, dapat disesuaikan pengguna

# Asumsi aktuaria/keuangan ilustratif untuk proyeksi 3 tahun (Tab 5)
CESSION_PCT = 70.0     # reasuransi
NWP_PCT = 30.0         # retensi bersih Tugu (100% - cession)
LOSS_RATIO_PCT = 35.0  # rasio klaim terhadap NWP
BASELINE_RBC_PCT = 350.0  # RBC awal Tugu, jauh di atas ambang minimum OJK 120%
RBC_DECAY_PER_PROJECT = 2.0  # asumsi penurunan RBC (poin persentase) per proyek tambahan


# =====================================================================================
# 3. HELPER / DATA GENERATORS
# =====================================================================================
@st.cache_data
def generate_demo_feedstock(days: int = 30, seed: int = 42) -> pd.DataFrame:
    """Menghasilkan data simulasi penimbangan sampah harian di sekitar target 1.000 ton/hari."""
    rng = np.random.default_rng(seed)
    dates = [datetime.today().date() - timedelta(days=days - i) for i in range(days)]
    tonase = np.clip(rng.normal(loc=TARGET_TON_PER_DAY, scale=80, size=days), 600, 1180)
    # sisipkan beberapa hari anomali di bawah ambang batas untuk demo klaim
    dip_idx = rng.choice(days, size=max(2, days // 10), replace=False)
    tonase[dip_idx] = rng.uniform(650, 820, size=len(dip_idx))
    kadar_air = np.clip(rng.normal(loc=45, scale=5, size=days), 30, 60)
    nilai_kalor = np.clip(rng.normal(loc=1800, scale=120, size=days), 1400, 2200)
    return pd.DataFrame(
        {
            "Tanggal": dates,
            "Tonase_Aktual_Ton": tonase.round(2),
            "Kadar_Air_Persen": kadar_air.round(1),
            "Nilai_Kalor_kcal_kg": nilai_kalor.round(0),
        }
    )


def make_template_csv() -> bytes:
    df = pd.DataFrame(
        {
            "Tanggal": [datetime.today().date() - timedelta(days=d) for d in range(5, 0, -1)],
            "Tonase_Aktual_Ton": [1020.5, 960.0, 790.2, 1050.0, 910.0],
            "Kadar_Air_Persen": [44.0, 46.5, 50.1, 42.3, 45.0],
            "Nilai_Kalor_kcal_kg": [1820, 1790, 1650, 1900, 1810],
        }
    )
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


def kpi_card(label: str, value: str, sub: str = "") -> str:
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """


def rp(value: float) -> str:
    """Format angka menjadi mata uang Rupiah ringkas."""
    return f"Rp {value:,.0f}"


def build_lifecycle_matrix() -> pd.DataFrame:
    """
    Menyusun pemetaan risiko sepanjang 5 fasa siklus hidup proyek WtE
    beserta padanan produk asuransi Tugu untuk tiap fasa.
    """
    return pd.DataFrame(
        [
            {
                "No": 1,
                "Fasa Siklus Hidup": "Pengangkutan Sampah",
                "Aktivitas Utama": "Pengumpulan & pengangkutan sampah dari TPS/TPA menuju fasilitas WtE",
                "Risiko Utama": "Kecelakaan armada, kerusakan/tumpahan muatan, keterlambatan pasokan akibat gangguan logistik",
                "Produk Asuransi Tugu": "Asuransi Pengangkutan Barang (Marine/Inland Cargo) & Asuransi Kendaraan Bermotor Armada",
                "Manfaat Utama": "Proteksi nilai muatan & armada, kontinuitas rantai pasok sampah",
            },
            {
                "No": 2,
                "Fasa Siklus Hidup": "Pembangunan Fasilitas (CAR/EAR)",
                "Aktivitas Utama": "Konstruksi sipil & pemasangan mesin insinerator/boiler/turbin",
                "Risiko Utama": "Kerusakan struktur selama konstruksi, kecelakaan kerja, kegagalan pemasangan peralatan berat",
                "Produk Asuransi Tugu": "Contractor's All Risk (CAR) & Erection All Risk (EAR)",
                "Manfaat Utama": "Proteksi investasi modal (capex) sejak hari pertama pembangunan",
            },
            {
                "No": 3,
                "Fasa Siklus Hidup": "Operasi Harian (PAR/MB)",
                "Aktivitas Utama": "Pembakaran sampah, pembangkitan uap & listrik secara berkelanjutan",
                "Risiko Utama": "Kebakaran, ledakan boiler, kerusakan mesin (machinery breakdown), gangguan operasional",
                "Produk Asuransi Tugu": "Property All Risk (PAR) & Machinery Breakdown Insurance (MB)",
                "Manfaat Utama": "Kontinuitas operasi & perlindungan aset fasilitas bernilai tinggi",
            },
            {
                "No": 4,
                "Fasa Siklus Hidup": "Pasokan Sampah Parametrik",
                "Aktivitas Utama": "Pemantauan tonase harian & validasi ambang batas pasokan minimum",
                "Risiko Utama": "Tonase sampah di bawah ambang batas kontrak, menyebabkan idle capacity & kerugian pendapatan",
                "Produk Asuransi Tugu": "TUGU SHIELD-WtE Parametric Feedstock Shortfall Insurance",
                "Manfaat Utama": "Klaim otomatis (parametric trigger) tanpa proses adjuster manual",
            },
            {
                "No": 5,
                "Fasa Siklus Hidup": "Distribusi Listrik & Monetisasi Karbon",
                "Aktivitas Utama": "Penyaluran listrik ke jaringan PLN & penjualan kredit karbon di pasar sukarela",
                "Risiko Utama": "Kegagalan transmisi/interkoneksi, gagal jual kredit karbon, fluktuasi harga karbon",
                "Produk Asuransi Tugu": "Business Interruption (BI) Insurance & Carbon Credit Revenue Protection",
                "Manfaat Utama": "Perlindungan pendapatan ganda: penjualan listrik & monetisasi karbon (tCO2e)",
            },
        ]
    )


# =====================================================================================
# 4. HERO BANNER
# =====================================================================================
st.markdown(
    """
    <div class="hero-banner">
    "TUGU SHIELD-WtE: End-to-End Parametric &amp; Comprehensive Insurance Solution
    guna Mengakselerasi Ekosistem Waste-to-Energy Berkelanjutan."
    </div>
    """,
    unsafe_allow_html=True,
)
st.title("♻️ TUGU SHIELD-WtE Digital Dashboard")
st.caption(
    "End-to-End Life Cycle Waste-to-Energy Insurance Solution — "
    "PT Asuransi Tugu Pratama Indonesia Tbk · IDEANATION 2026 Semifinal"
)

# =====================================================================================
# 5. SIDEBAR — DATA INPUT CENTER
# =====================================================================================
with st.sidebar:
    st.header("⚙️ Panel Kontrol")

    mode = st.radio(
        "Mode Data",
        ["Gunakan Data Simulasi Demo", "Gunakan Data Sendiri"],
        help="Pilih 'Simulasi Demo' untuk langsung melihat grafik contoh saat presentasi, "
        "atau 'Data Sendiri' untuk mengunggah data operasional riil.",
    )

    st.divider()
    st.subheader("📥 Modul Manajemen Data")

    st.download_button(
        label="⬇️ Download Template CSV",
        data=make_template_csv(),
        file_name="Template_Tugu_WtE.csv",
        mime="text/csv",
        help="Unduh contoh format data penimbangan sampah harian (Tonase, Kadar Air, Nilai Kalor).",
    )

    uploaded_file = None
    manual_df = None

    if mode == "Gunakan Data Sendiri":
        uploaded_file = st.file_uploader(
            "Upload data harian (.csv / .xlsx)",
            type=["csv", "xlsx"],
            help="Kolom wajib: Tanggal, Tonase_Aktual_Ton, Kadar_Air_Persen, Nilai_Kalor_kcal_kg",
        )
        with st.expander("✍️ Atau Input Manual (Simulasi Cepat)"):
            n_days = st.slider("Jumlah hari simulasi", 5, 30, 10, help="Berapa hari data yang ingin disimulasikan.")
            avg_ton = st.number_input(
                "Rata-rata tonase harian (ton)", min_value=300.0, max_value=1500.0, value=950.0,
                help="Estimasi rata-rata volume sampah yang masuk per hari.",
            )
            if st.button("Buat Data Manual"):
                manual_df = generate_demo_feedstock(days=n_days, seed=int(avg_ton))
                manual_df["Tonase_Aktual_Ton"] = (
                    manual_df["Tonase_Aktual_Ton"] - manual_df["Tonase_Aktual_Ton"].mean() + avg_ton
                ).round(2)

    st.divider()
    st.subheader("ℹ️ Istilah Kunci")
    with st.expander("Apa itu Parametric Trigger?"):
        st.write(
            "Klaim otomatis cair ketika indikator terukur (mis. tonase sampah) "
            "menembus ambang batas yang telah disepakati — tanpa proses adjuster manual."
        )
    with st.expander("Apa itu Deductible?"):
        st.write("Persentase risiko yang ditanggung sendiri oleh tertanggung sebelum klaim dibayarkan.")
    with st.expander("Apa itu RBC?"):
        st.write(
            "Risk-Based Capital: rasio kesehatan modal asuransi terhadap risiko yang diambil. "
            "OJK mensyaratkan minimum 120%."
        )
    with st.expander("Apa itu Reinsurance Cession & NWP?"):
        st.write(
            "Cession adalah porsi premi yang dialihkan/dibagi ke reasuradur global untuk "
            "menyebar risiko. Net Written Premium (NWP) adalah porsi premi yang tetap "
            "menjadi retensi/tanggungan bersih Tugu setelah cession."
        )
    with st.expander("Apa itu Carbon Credit / tCO2e?"):
        st.write(
            "tCO2e (ton CO2 ekuivalen) adalah satuan pengukuran reduksi emisi gas rumah kaca. "
            "Reduksi ini dapat dijual sebagai kredit karbon di pasar karbon sukarela (voluntary "
            "carbon market), menghasilkan pendapatan tambahan bagi proyek WtE."
        )

# =====================================================================================
# 6. LOAD DATA (Validasi Lapis 1 dimulai di sini)
# =====================================================================================
data_status = "success"
data_message = "Data simulasi demo dimuat dengan baik."

if mode == "Gunakan Data Simulasi Demo":
    df = generate_demo_feedstock()
elif manual_df is not None:
    df = manual_df
    data_message = "Data manual berhasil dibuat."
elif uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        required_cols = {"Tanggal", "Tonase_Aktual_Ton", "Kadar_Air_Persen", "Nilai_Kalor_kcal_kg"}
        if not required_cols.issubset(set(df.columns)):
            data_status = "warning"
            data_message = f"Kolom tidak lengkap. Wajib ada: {', '.join(required_cols)}. Menampilkan data demo sebagai gantinya."
            df = generate_demo_feedstock()
        else:
            df["Tanggal"] = pd.to_datetime(df["Tanggal"]).dt.date
            data_message = "Data berhasil diunggah dan tervalidasi."
    except Exception as e:  # noqa: BLE001
        data_status = "warning"
        data_message = f"Gagal membaca file ({e}). Menampilkan data demo sebagai gantinya."
        df = generate_demo_feedstock()
else:
    data_status = "warning"
    data_message = "Belum ada data diunggah / dibuat. Menampilkan data simulasi demo sementara."
    df = generate_demo_feedstock()

df = df.sort_values("Tanggal").reset_index(drop=True)

total_tonase = df["Tonase_Aktual_Ton"].sum()
avg_tonase = df["Tonase_Aktual_Ton"].mean()
days_below = (df["Tonase_Aktual_Ton"] < THRESHOLD_TON_PER_DAY).sum()
status_pasokan = "Normal" if days_below == 0 else f"Dibawah Ambang Batas ({days_below} hari)"

# =====================================================================================
# 7. TABS UTAMA (5 TAB — END-TO-END LIFE CYCLE)
# =====================================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "🔄 End-to-End Life Cycle",
        "📡 Feedstock Monitor",
        "🧮 Parametric Engine",
        "🌱 ESG & Carbon Credit",
        "📊 Proyeksi Keuangan 3 Thn",
    ]
)

# -------------------------------------------------------------------------------------
# TAB 1 — End-to-End Life Cycle (Pemetaan Risiko 5 Fasa)
# -------------------------------------------------------------------------------------
with tab1:
    st.subheader("End-to-End Life Cycle Risk Mapping")
    st.caption(
        "Pemetaan risiko sepanjang 5 fasa proyek Waste-to-Energy beserta padanan produk "
        "asuransi terintegrasi PT Asuransi Tugu Pratama Indonesia Tbk — dari pengangkutan "
        "sampah hingga monetisasi karbon."
    )

    lifecycle_df = build_lifecycle_matrix()

    st.dataframe(
        lifecycle_df.set_index("No"),
        use_container_width=True,
        height=250,
    )

    st.write("")
    st.markdown("**🔎 Rincian per Fasa**")
    pilih_fasa = st.selectbox("Pilih fasa untuk melihat rincian kartu:", lifecycle_df["Fasa Siklus Hidup"].tolist())
    baris_fasa = lifecycle_df[lifecycle_df["Fasa Siklus Hidup"] == pilih_fasa].iloc[0]

    st.markdown(
        f"""
        <div class="phase-card">
            <div class="phase-title">Fasa {baris_fasa['No']}: {baris_fasa['Fasa Siklus Hidup']}</div>
            <div><b>Aktivitas Utama:</b> {baris_fasa['Aktivitas Utama']}</div>
            <div style="margin-top:6px;"><b>Risiko Utama:</b> {baris_fasa['Risiko Utama']}</div>
            <div style="margin-top:6px;"><b>Manfaat Utama:</b> {baris_fasa['Manfaat Utama']}</div>
            <div class="phase-product">🛡️ {baris_fasa['Produk Asuransi Tugu']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    jumlah_produk_unik = lifecycle_df["Produk Asuransi Tugu"].nunique()
    st.info(
        f"ℹ️ TUGU SHIELD-WtE mengintegrasikan **{jumlah_produk_unik} lini produk asuransi** "
        f"ke dalam **satu payung solusi tunggal**, mencakup seluruh **5 fasa siklus hidup** "
        f"proyek WtE — menjadikannya solusi *comprehensive*, bukan sekadar produk tunggal "
        f"berbasis parametrik semata."
    )

# -------------------------------------------------------------------------------------
# TAB 2 — Feedstock Monitor (Validasi Lapis 1: IoT Data Input)
# -------------------------------------------------------------------------------------
with tab2:
    st.subheader("Feedstock Monitor")
    st.caption(
        "Validasi Lapis 1: IoT Data Input Check — memastikan data penimbangan sampah "
        "valid & tamper-proof sebelum masuk ke mesin klaim parametrik."
    )

    if data_status == "success":
        st.success(f"✅ Validasi Lapis 1 Berhasil — {data_message}")
    else:
        st.warning(f"⚠️ Validasi Lapis 1 — {data_message}")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(kpi_card("Total Tonase Periode Ini", f"{total_tonase:,.0f} Ton"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("Rata-rata Harian", f"{avg_tonase:,.1f} Ton/Hari"), unsafe_allow_html=True)
    with c3:
        st.markdown(
            kpi_card(
                "Status Pasokan",
                status_pasokan,
                f"Ambang batas minimum: {THRESHOLD_TON_PER_DAY:.0f} ton/hari "
                f"(target kontrak: {TARGET_TON_PER_DAY:.0f} ton/hari)",
            ),
            unsafe_allow_html=True,
        )

    st.write("")
    fig1 = go.Figure()
    fig1.add_trace(
        go.Scatter(
            x=df["Tanggal"],
            y=df["Tonase_Aktual_Ton"],
            mode="lines+markers",
            name="Tonase Aktual",
            line=dict(color=PRIMARY_DARK_PURPLE, width=3),
            marker=dict(size=6, color=HIGHLIGHT_PINK),
        )
    )
    fig1.add_hline(
        y=THRESHOLD_TON_PER_DAY,
        line_dash="dash",
        line_color="red",
        annotation_text="Ambang Batas Minimum (850 ton/hari)",
        annotation_position="top left",
    )
    fig1.add_hline(
        y=TARGET_TON_PER_DAY,
        line_dash="dot",
        line_color=SECONDARY_PURPLE,
        annotation_text="Target Kontrak (1.000 ton/hari)",
        annotation_position="bottom left",
    )
    fig1.update_layout(
        title="Tren Tonase Sampah Harian vs Target & Ambang Batas Perpres No. 35/2018",
        xaxis_title="Tanggal",
        yaxis_title="Tonase (Ton)",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_color="#3A0A5C",
    )
    st.plotly_chart(fig1, use_container_width=True)

    with st.expander("📄 Lihat Data Mentah"):
        st.dataframe(df, use_container_width=True)

# -------------------------------------------------------------------------------------
# TAB 3 — Parametric Engine (Validasi Lapis 2: Algoritma Klaim)
# -------------------------------------------------------------------------------------
with tab3:
    st.subheader("Parametric Claim Engine")
    st.caption("Validasi Lapis 2: Algoritma Matematika & Logic — perhitungan klaim transparan & auditable.")

    colA, colB, colC = st.columns(3)
    with colA:
        target_tonase = st.number_input(
            "Target Tonase Harian (ton)", min_value=300.0, max_value=2000.0, value=TARGET_TON_PER_DAY,
            help="Volume sampah yang dikontrak/dijanjikan masuk ke fasilitas WtE per hari "
            "(mengacu minimum Perpres No. 35 Tahun 2018: 1.000 ton/hari).",
        )
    with colB:
        deductible_pct = st.slider(
            "Deductible (%)", min_value=10, max_value=50, value=10,
            help="Persentase risiko yang ditanggung sendiri sebelum klaim dibayarkan.",
        )
    with colC:
        tarif_kompensasi = st.number_input(
            "Tarif Kompensasi / Ton (Rp)", min_value=10_000, max_value=2_000_000, value=250_000, step=10_000,
            help="Nilai kompensasi finansial per ton kekurangan pasokan.",
        )

    claim_df = df.copy()
    claim_df["Selisih_Ton"] = np.maximum(0, target_tonase - claim_df["Tonase_Aktual_Ton"])
    claim_df["Nilai_Klaim_Rp"] = (
        claim_df["Selisih_Ton"] * tarif_kompensasi * (1 - deductible_pct / 100)
    ).round(0)
    triggered = claim_df[claim_df["Nilai_Klaim_Rp"] > 0]

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            kpi_card("Hari Terkena Klaim", f"{len(triggered)} Hari", f"dari {len(claim_df)} hari observasi"),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            kpi_card("Total Estimasi Klaim", rp(triggered["Nilai_Klaim_Rp"].sum())),
            unsafe_allow_html=True,
        )

    st.markdown("**Tabel Rincian Hari Terkena Klaim**")
    if len(triggered) > 0:
        st.dataframe(
            triggered[["Tanggal", "Tonase_Aktual_Ton", "Selisih_Ton", "Nilai_Klaim_Rp"]],
            use_container_width=True,
        )
    else:
        st.info("Tidak ada hari yang memicu klaim pada parameter saat ini.")

    st.markdown("**🔍 Interactive Proof Box — Step-by-Step Breakdown**")
    if len(triggered) > 0:
        pilih_tanggal = st.selectbox("Pilih tanggal untuk melihat rincian kalkulasi:", triggered["Tanggal"].tolist())
        row = triggered[triggered["Tanggal"] == pilih_tanggal].iloc[0]
        st.code(
            f"""Nilai Klaim = max(0, Target Tonase - Tonase Aktual) x Tarif Kompensasi/Ton x (1 - Deductible%)

Langkah 1: Selisih Tonase     = max(0, {target_tonase:.1f} - {row['Tonase_Aktual_Ton']:.1f}) = {row['Selisih_Ton']:.1f} ton
Langkah 2: Sebelum Deductible = {row['Selisih_Ton']:.1f} x Rp {tarif_kompensasi:,.0f} = Rp {row['Selisih_Ton'] * tarif_kompensasi:,.0f}
Langkah 3: Terapkan Deductible ({deductible_pct}%) = Rp {row['Selisih_Ton'] * tarif_kompensasi:,.0f} x (1 - {deductible_pct/100:.2f})
Hasil Akhir (Nilai Klaim)     = Rp {row['Nilai_Klaim_Rp']:,.0f}
""",
            language="text",
        )
    else:
        st.caption("Proof box akan muncul otomatis saat ada hari yang memicu klaim.")

# -------------------------------------------------------------------------------------
# TAB 4 — ESG & Carbon Credit
# -------------------------------------------------------------------------------------
with tab4:
    st.subheader("ESG & Carbon Credit Impact Tracker")
    st.caption(
        "Menghitung dampak sirkularitas pengolahan abu sisa pembakaran (fly ash/bottom ash) "
        "serta simulasi monetisasi kredit karbon dari reduksi emisi proyek WtE."
    )

    st.markdown("#### ♻️ Sirkularitas Abu Sisa Pembakaran")
    total_ash_produced = total_tonase * ASH_RATIO_OF_INPUT
    colX, colY = st.columns(2)
    with colX:
        st.markdown(
            kpi_card("Estimasi Total Abu Dihasilkan", f"{total_ash_produced:,.1f} Ton",
                      f"asumsi {ASH_RATIO_OF_INPUT*100:.0f}% dari total input sampah (fly ash + bottom ash)"),
            unsafe_allow_html=True,
        )
    with colY:
        ash_processed = st.number_input(
            "Tonase Abu Terolah Menjadi Material Sirkular (ton)",
            min_value=0.0, max_value=float(max(total_ash_produced, 1)),
            value=float(round(total_ash_produced * 0.6, 1)),
            help="Jumlah fly ash/bottom ash yang berhasil diolah menjadi material bangunan (paving block, dsb).",
        )

    circularity_pct = (ash_processed / total_ash_produced * 100) if total_ash_produced > 0 else 0
    carbon_reduction = ash_processed * EMISSION_FACTOR_TCO2_PER_TON_ASH

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            kpi_card("Reduksi Emisi Karbon", f"{carbon_reduction:,.1f} tCO₂e",
                      "vs. abu dibuang ke landfill konvensional"),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            kpi_card("Tingkat Sirkularitas Abu", f"{circularity_pct:,.1f}%"),
            unsafe_allow_html=True,
        )

    if circularity_pct >= 80:
        rebate = 10
    elif circularity_pct >= 50:
        rebate = 5
    else:
        rebate = 0

    st.write("")
    st.markdown(
        f"""
        <div class="green-badge">
            <div style="font-size:13px;color:#6b6b6b;font-weight:600;">GREEN REBATE BADGE</div>
            <h2>Diskon Premi {rebate}% untuk Polis Tahun Berikutnya</h2>
            <div style="font-size:12px;color:#8a8a8a;">Berdasarkan sirkularitas abu sebesar {circularity_pct:.1f}% (ambang: 0% / &lt;50%, 5% / 50-79%, 10% / ≥80%)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown("#### 💵 Simulator Monetisasi Kredit Karbon")
    st.caption(
        "Mengonversi reduksi emisi karbon (tCO2e) hasil sirkularitas abu di atas menjadi "
        "estimasi nilai moneter di pasar karbon sukarela (voluntary carbon market)."
    )

    col_kurs, col_harga = st.columns(2)
    with col_kurs:
        kurs_usd_idr = st.number_input(
            "Asumsi Kurs USD/IDR (Rp)", min_value=10_000.0, max_value=20_000.0,
            value=DEFAULT_KURS_USD_IDR, step=100.0,
            help="Kurs acuan untuk konversi nilai kredit karbon dari USD ke Rupiah.",
        )
    with col_harga:
        harga_karbon_usd = st.number_input(
            "Harga Kredit Karbon (USD/tCO2e)", min_value=1.0, max_value=100.0,
            value=USD_PER_TCO2E, step=0.5,
            help="Harga acuan pasar karbon sukarela; nilai default $10/tCO2e sesuai brief kompetisi.",
        )

    nilai_karbon_usd = carbon_reduction * harga_karbon_usd
    nilai_karbon_idr = nilai_karbon_usd * kurs_usd_idr

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(kpi_card("Volume Kredit Karbon", f"{carbon_reduction:,.1f} tCO₂e"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("Estimasi Nilai (USD)", f"$ {nilai_karbon_usd:,.0f}",
                              f"@ $ {harga_karbon_usd:,.1f} / tCO2e"), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card("Estimasi Nilai (IDR)", rp(nilai_karbon_idr),
                              f"kurs Rp {kurs_usd_idr:,.0f} / USD"), unsafe_allow_html=True)

    st.info(
        "ℹ️ Pendapatan monetisasi karbon ini dapat menjadi **sumber pendapatan tambahan** bagi "
        "proyek WtE, sekaligus memperkuat profil risiko yang dilindungi Business Interruption "
        "Insurance & Carbon Credit Revenue Protection pada Fasa 5 (lihat Tab End-to-End Life Cycle)."
    )

# -------------------------------------------------------------------------------------
# TAB 5 — Proyeksi Keuangan 3 Tahun (2026-2028)
# -------------------------------------------------------------------------------------
with tab5:
    st.subheader("Proyeksi Keuangan 3 Tahun (2026-2028)")
    st.caption(
        "Simulator unjuran kewangan portfolio TUGU SHIELD-WtE seiring pertumbuhan jumlah "
        "proyek WtE yang dilindungi — dari fasa awal (first-mover) hingga skala nasional."
    )

    col1, col2 = st.columns(2)
    with col1:
        proyek_2028 = st.slider(
            "Sasaran Jumlah Proyek WtE Tercover pada 2028",
            min_value=5, max_value=50, value=15,
            help="Jumlah proyek WtE (fasilitas) yang ditargetkan telah dilindungi TUGU SHIELD-WtE "
            "pada akhir 2028. Baseline 2026 diasumsikan 3 proyek (fase first-mover).",
        )
    with col2:
        premi_per_proyek = st.number_input(
            "Asumsi Premi Rata-rata / Proyek / Tahun (Rp)",
            min_value=500_000_000.0, max_value=50_000_000_000.0,
            value=5_000_000_000.0, step=500_000_000.0, format="%.0f",
            help="Estimasi premi tahunan gabungan (CAR/EAR + PAR/MB + Parametric + BI) per proyek WtE.",
        )

    proyek_2026 = 3  # baseline first-mover, tetap (tidak disimulasikan pengguna)
    proyek_2027 = round((proyek_2026 + proyek_2028) / 2)
    tahun_list = [2026, 2027, 2028]
    proyek_list = [proyek_2026, proyek_2027, proyek_2028]

    proyeksi_rows = []
    for tahun, n_proyek in zip(tahun_list, proyek_list):
        gwp = n_proyek * premi_per_proyek
        cession = gwp * (CESSION_PCT / 100)
        nwp = gwp * (NWP_PCT / 100)
        klaim = nwp * (LOSS_RATIO_PCT / 100)
        net_uw_profit = nwp - klaim
        rbc = max(150.0, BASELINE_RBC_PCT - (n_proyek - proyek_2026) * RBC_DECAY_PER_PROJECT)
        proyeksi_rows.append(
            {
                "Tahun": tahun,
                "Jumlah Proyek WtE": n_proyek,
                "Gross Written Premium (GWP)": gwp,
                "Reinsurance Cession (70%)": cession,
                "Net Written Premium (NWP, 30%)": nwp,
                "Estimasi Klaim (Loss Ratio 35%)": klaim,
                "Net Underwriting Profit": net_uw_profit,
                "Rasio RBC Tugu (%)": rbc,
            }
        )
    proyeksi_df = pd.DataFrame(proyeksi_rows)

    st.markdown("**Rincian Proyeksi Metrik Keuangan**")
    tabel_tampil = proyeksi_df.copy()
    for kolom_rp in [
        "Gross Written Premium (GWP)", "Reinsurance Cession (70%)",
        "Net Written Premium (NWP, 30%)", "Estimasi Klaim (Loss Ratio 35%)",
        "Net Underwriting Profit",
    ]:
        tabel_tampil[kolom_rp] = tabel_tampil[kolom_rp].apply(rp)
    tabel_tampil["Rasio RBC Tugu (%)"] = tabel_tampil["Rasio RBC Tugu (%)"].apply(lambda x: f"{x:.0f}%")
    st.dataframe(tabel_tampil.set_index("Tahun"), use_container_width=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            kpi_card("GWP 2028", rp(proyeksi_df.iloc[-1]["Gross Written Premium (GWP)"]),
                      f"dari {proyek_2028} proyek WtE"),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            kpi_card("Net UW Profit 2028", rp(proyeksi_df.iloc[-1]["Net Underwriting Profit"])),
            unsafe_allow_html=True,
        )
    with c3:
        rbc_akhir = proyeksi_df.iloc[-1]["Rasio RBC Tugu (%)"]
        status_rbc = "✅ Aman di atas ambang OJK (120%)" if rbc_akhir >= 120 else "⚠️ Mendekati ambang OJK"
        st.markdown(kpi_card("Rasio RBC 2028", f"{rbc_akhir:.0f}%", status_rbc), unsafe_allow_html=True)

    st.write("")
    fig5 = go.Figure()
    fig5.add_trace(
        go.Bar(
            x=proyeksi_df["Tahun"].astype(str),
            y=proyeksi_df["Gross Written Premium (GWP)"],
            name="Gross Written Premium (GWP)",
            marker_color=PRIMARY_DARK_PURPLE,
        )
    )
    fig5.add_trace(
        go.Bar(
            x=proyeksi_df["Tahun"].astype(str),
            y=proyeksi_df["Net Underwriting Profit"],
            name="Net Underwriting Profit",
            marker_color=HIGHLIGHT_PINK,
        )
    )
    fig5.update_layout(
        title="Pertumbuhan GWP vs Net Underwriting Profit (2026-2028)",
        xaxis_title="Tahun",
        yaxis_title="Nilai (Rp)",
        barmode="group",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_color="#3A0A5C",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig5, use_container_width=True)

    with st.expander("📌 Catatan Asumsi Proyeksi"):
        st.write(
            f"""
            - Baseline 2026 diasumsikan **{proyek_2026} proyek WtE** (fase first-mover), dengan
              2027 diinterpolasi linear menuju sasaran 2028 yang Anda tetapkan di atas.
            - Struktur reasuransi **{CESSION_PCT:.0f}% cession / {NWP_PCT:.0f}% retensi bersih (NWP)**
              dan **Loss Ratio {LOSS_RATIO_PCT:.0f}%** merupakan asumsi ilustratif tetap sesuai
              brief kompetisi, bukan hasil pricing aktuaria final.
            - Rasio RBC diproyeksikan turun ilustratif **{RBC_DECAY_PER_PROJECT:.0f} poin per
              proyek tambahan** akibat kenaikan kebutuhan modal risiko seiring pertumbuhan
              portfolio — tetap dijaga pada lantai minimum 150% (jauh di atas ambang OJK 120%)
              dalam simulasi ini. Angka ini bersifat indikatif untuk keperluan presentasi,
              bukan model kecukupan modal aktuaria penuh.
            """
        )

# =====================================================================================
# 8. OUTPUT EXPORTER (Footer) — Ringkasan Penunjuk Utama Kelima-Lima Tab
# =====================================================================================
st.divider()
st.subheader("📤 Ekspor Laporan Ringkasan")
st.caption("Merangkum penunjuk utama daripada kelima-lima tab dashboard ke dalam satu fail CSV.")

summary_df = pd.DataFrame(
    {
        "Tab": [
            "1. End-to-End Life Cycle", "1. End-to-End Life Cycle",
            "2. Feedstock Monitor", "2. Feedstock Monitor", "2. Feedstock Monitor",
            "3. Parametric Engine", "3. Parametric Engine", "3. Parametric Engine",
            "4. ESG & Carbon Credit", "4. ESG & Carbon Credit", "4. ESG & Carbon Credit",
            "4. ESG & Carbon Credit", "4. ESG & Carbon Credit",
            "5. Proyeksi Keuangan", "5. Proyeksi Keuangan", "5. Proyeksi Keuangan",
            "5. Proyeksi Keuangan", "5. Proyeksi Keuangan",
        ],
        "Metrik": [
            "Jumlah Fasa Siklus Hidup Tercover",
            "Jumlah Lini Produk Asuransi Terintegrasi",
            "Total Tonase Periode",
            "Rata-rata Harian (Ton)",
            "Status Pasokan",
            "Hari Terkena Klaim",
            "Total Estimasi Klaim (Rp)",
            "Deductible Terpakai (%)",
            "Tingkat Sirkularitas Abu (%)",
            "Green Rebate (%)",
            "Reduksi Emisi Karbon (tCO2e)",
            "Nilai Monetisasi Karbon (USD)",
            "Nilai Monetisasi Karbon (IDR)",
            "Jumlah Proyek WtE 2028",
            "GWP 2028 (Rp)",
            "Net Written Premium 2028 (Rp)",
            "Net Underwriting Profit 2028 (Rp)",
            "Rasio RBC 2028 (%)",
        ],
        "Nilai": [
            "5",
            f"{jumlah_produk_unik}",
            f"{total_tonase:,.0f}",
            f"{avg_tonase:,.1f}",
            status_pasokan,
            f"{len(triggered)}",
            f"{triggered['Nilai_Klaim_Rp'].sum():,.0f}",
            f"{deductible_pct}",
            f"{circularity_pct:,.1f}",
            f"{rebate}",
            f"{carbon_reduction:,.1f}",
            f"{nilai_karbon_usd:,.0f}",
            f"{nilai_karbon_idr:,.0f}",
            f"{proyek_2028}",
            f"{proyeksi_df.iloc[-1]['Gross Written Premium (GWP)']:,.0f}",
            f"{proyeksi_df.iloc[-1]['Net Written Premium (NWP, 30%)']:,.0f}",
            f"{proyeksi_df.iloc[-1]['Net Underwriting Profit']:,.0f}",
            f"{proyeksi_df.iloc[-1]['Rasio RBC Tugu (%)']:.0f}",
        ],
    }
)
st.dataframe(summary_df, use_container_width=True, hide_index=True)

csv_buf = io.StringIO()
summary_df.to_csv(csv_buf, index=False)
st.download_button(
    "⬇️ Download Ringkasan (CSV)",
    data=csv_buf.getvalue().encode("utf-8"),
    file_name="TUGU_SHIELD_WtE_Ringkasan_5Tab.csv",
    mime="text/csv",
)

st.markdown(
    '<div class="footer-note">TUGU SHIELD-WtE Dashboard — End-to-End Life Cycle WtE Insurance '
    'Solution · Prototype untuk IDEANATION 2026 Semifinal</div>',
    unsafe_allow_html=True,
)
