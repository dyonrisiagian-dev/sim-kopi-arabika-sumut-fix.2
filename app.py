import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, inspect, text
from pathlib import Path
import os, re

st.set_page_config(page_title="SIKASU | Kopi Arabika Sumatera Utara", page_icon="☕", layout="wide")

st.markdown("""
<style>
.stApp{background:#F6F7F1;color:#26352C}
.block-container{max-width:1450px;padding-top:1.2rem}
[data-testid="stSidebar"]{background:#EDF1E7}
.hero{background:linear-gradient(115deg,#183F32,#2D6448 62%,#A66B3F);padding:24px 28px;border-radius:20px;color:#fff;margin:4px 0 20px}
.hero h1{font-size:2rem;color:#fff;margin:0;font-weight:800}
.hero p{color:#F0E8D9;margin:5px 0 0}
[data-testid="stMetric"]{background:white;border:1px solid #E5E9DE;border-radius:15px;padding:14px}
div[data-testid="stPlotlyChart"]{background:white;border:1px solid #E5E9DE;border-radius:15px;padding:8px}
h2,h3{color:#294B37}
</style>
""", unsafe_allow_html=True)

BASE = Path(__file__).parent
logo = BASE / "assets" / "sikasu_logo.svg"
left, right = st.columns([1, 9], vertical_alignment="center")
with left:
    st.image(str(logo), width=86)
with right:
    st.markdown('<div class="hero"><h1>SIKASU</h1><p>Sistem Informasi Kopi Arabika Sumatera Utara</p></div>', unsafe_allow_html=True)

st.sidebar.image(str(logo), width=95)
st.sidebar.title("SIKASU")
st.sidebar.caption("Dashboard komoditas kopi Arabika Sumatera Utara")
source = st.sidebar.radio("Sumber data", ["Database Neon", "Unggah CSV", "Data contoh"])

def normalize(x):
    return re.sub(r"[^a-z0-9]+", "_", str(x).strip().lower()).strip("_")

def find_col(cols, aliases):
    norm = {normalize(c): c for c in cols}
    for a in aliases:
        if a in norm: return norm[a]
    for n,c in norm.items():
        if any(a in n for a in aliases): return c
    return None

raw = None
source_name = ""
if source == "Data contoh":
    raw = pd.read_csv(BASE / "sample_data.csv")
    source_name = "Data contoh (simulasi)"
    st.warning("Mode contoh: angka di bawah adalah data simulasi untuk menguji tampilan, bukan statistik resmi.")
elif source == "Unggah CSV":
    upload = st.file_uploader("Unggah file CSV data kopi Arabika", type=["csv"])
    if upload:
        raw = pd.read_csv(upload)
        source_name = f"CSV: {upload.name}"
    else:
        st.info("Pilih file CSV untuk melanjutkan.")
        st.stop()
else:
    db_url = None
    try:
        db_url = st.secrets.get("NEON_DATABASE_URL") or os.getenv("NEON_DATABASE_URL")
    except Exception:
        db_url = os.getenv("NEON_DATABASE_URL")
    if not db_url:
        st.info("Koneksi Neon belum diatur. Tambahkan NEON_DATABASE_URL di Streamlit Secrets. Untuk mencoba tampilan sekarang, pilih 'Data contoh' di sidebar.")
        st.stop()
    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        tables = inspect(engine).get_table_names(schema="public") + inspect(engine).get_view_names(schema="public")
        if not tables:
            st.error("Tidak ada tabel/view di schema public.")
            st.stop()
        method = st.sidebar.radio("Cara membaca data", ["Pilih tabel atau view", "Query SQL"])
        if method == "Pilih tabel atau view":
            table = st.sidebar.selectbox("Pilih tabel", sorted(set(tables)))
            if st.sidebar.button("Muat data dari Neon", type="primary"):
                with engine.connect() as conn:
                    raw = pd.read_sql(text(f'SELECT * FROM public."{table}" LIMIT 250000'), conn)
                st.session_state["sikasu_neon_data"] = raw
                st.session_state["sikasu_neon_table"] = table
            if st.session_state.get("sikasu_neon_table") == table:
                raw = st.session_state["sikasu_neon_data"]
        else:
            sql = st.sidebar.text_area("Query SELECT", height=180, placeholder="SELECT ...")
            if st.sidebar.button("Jalankan query"):
                cleaned = sql.strip().rstrip(";")
                if not re.match(r"^(select|with)\b", cleaned, flags=re.I) or ";" in cleaned:
                    st.sidebar.error("Masukkan satu query SELECT/WITH saja.")
                else:
                    with engine.connect() as conn:
                        conn.exec_driver_sql("SET TRANSACTION READ ONLY")
                        st.session_state["sikasu_sql_data"] = pd.read_sql_query(text(cleaned), conn).head(250000)
                    st.session_state["sikasu_sql_query"] = cleaned
            if st.session_state.get("sikasu_sql_query") == sql.strip().rstrip(";"):
                raw = st.session_state["sikasu_sql_data"]
        source_name = "Database Neon"
    except Exception as e:
        st.error("Koneksi atau pembacaan Neon gagal. Periksa Secrets dan struktur tabel.")
        with st.expander("Detail error"): st.code(str(e))
        st.stop()

if raw is None:
    st.info("Pilih tabel dan klik tombol muat data, atau gunakan mode contoh.")
    st.stop()
if raw.empty:
    st.warning("Data kosong.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.subheader("Pemetaan kolom")
cols = list(raw.columns)
kab_guess = find_col(cols, ["kabupaten", "nama_kabupaten", "kab_kota"])
kec_guess = find_col(cols, ["kecamatan", "nama_kecamatan"])
prod_guess = find_col(cols, ["produksi_ton", "produksi", "jumlah_produksi", "volume", "tonase"])
year_guess = find_col(cols, ["tahun", "year"])
name_guess = find_col(cols, ["jenis_kopi", "komoditas", "varietas", "jenis"])

def select_col(label, guess, optional=False):
    opts = ["-- Tidak digunakan --"] + cols
    idx = opts.index(guess) if guess in opts else (0 if optional else 0)
    val = st.sidebar.selectbox(label, opts, index=idx)
    return None if val.startswith("--") else val

kab = select_col("Kolom kabupaten", kab_guess)
kec = select_col("Kolom kecamatan/desa", kec_guess, True)
prod = select_col("Kolom produksi", prod_guess)
year = select_col("Kolom tahun", year_guess, True)
kind = select_col("Kolom jenis/varietas kopi", name_guess, True)
unit = st.sidebar.selectbox("Satuan produksi di file", ["Ton", "Kilogram (kg)", "Kuintal"])

if not kab or not prod:
    st.error("Pilih minimal kolom kabupaten dan produksi pada sidebar.")
    st.caption("Nama kolom yang tersedia: " + ", ".join(map(str, cols)))
    st.stop()

def to_num(v):
    if pd.isna(v): return None
    if isinstance(v, (int,float)): return float(v)
    s = str(v).strip().replace(" ","")
    if "," in s and "." in s:
        s = s.replace(".","").replace(",",".") if s.rfind(",") > s.rfind(".") else s.replace(",","")
    elif "," in s:
        s = s.replace(",",".") if len(s.split(",")[-1]) <= 2 else s.replace(",","")
    try: return float(s)
    except: return None

df = pd.DataFrame()
df["Kabupaten"] = raw[kab].astype(str).str.strip()
df["Kecamatan"] = raw[kec].astype(str).str.strip() if kec else "Tidak tersedia"
df["Produksi_asli"] = raw[prod].map(to_num)
df["Tahun"] = raw[year].astype(str) if year else "Tidak tersedia"
df["Jenis kopi"] = raw[kind].astype(str) if kind else "Arabika / tidak dirinci"
factor = {"Ton":1, "Kilogram (kg)":0.001, "Kuintal":0.1}[unit]
df["Produksi (ton)"] = df["Produksi_asli"] * factor
df = df.dropna(subset=["Produksi (ton)", "Kabupaten"])
df = df[df["Produksi (ton)"] >= 0]

years = sorted(df["Tahun"].unique().tolist())
if year:
    selected_year = st.sidebar.selectbox("Filter tahun", ["Semua tahun"] + years)
    if selected_year != "Semua tahun": df = df[df["Tahun"] == selected_year]
districts = sorted(df["Kabupaten"].unique().tolist())
selected_districts = st.sidebar.multiselect("Filter kabupaten", districts, default=districts)
df = df[df["Kabupaten"].isin(selected_districts)]
if df.empty:
    st.warning("Tidak ada data pada filter terpilih.")
    st.stop()

by_kab = df.groupby("Kabupaten", as_index=False)["Produksi (ton)"].sum().sort_values("Produksi (ton)", ascending=False)
by_kec = df.groupby(["Kabupaten","Kecamatan"], as_index=False)["Produksi (ton)"].sum().sort_values("Produksi (ton)", ascending=False)
total = df["Produksi (ton)"].sum()
top = by_kab.iloc[0]
top3_share = by_kab.head(3)["Produksi (ton)"].sum()/total*100 if total else 0

st.subheader("Ringkasan produksi kopi Arabika")
m1,m2,m3,m4 = st.columns(4)
m1.metric("Total produksi", f"{total:,.2f} ton")
m2.metric("Kabupaten", f"{df['Kabupaten'].nunique()}")
m3.metric("Kecamatan/desa", f"{df['Kecamatan'].nunique()}")
m4.metric("Rata-rata per kabupaten", f"{by_kab['Produksi (ton)'].mean():,.2f} ton")

tab1,tab2,tab3 = st.tabs(["📊 Analisis wilayah","📋 Tabel data","💡 Temuan utama"])
with tab1:
    a,b = st.columns(2)
    with a:
        fig = px.pie(by_kab, names="Kabupaten", values="Produksi (ton)", hole=.55, title="Kontribusi produksi per kabupaten", color_discrete_sequence=["#244F3A","#6E9B65","#B67B4D","#D5B77A","#9B5143"])
        st.plotly_chart(fig, use_container_width=True)
    with b:
        fig = px.bar(by_kab.sort_values("Produksi (ton)"), x="Produksi (ton)", y="Kabupaten", orientation="h", title="Perbandingan produksi kabupaten", color="Produksi (ton)", color_continuous_scale=["#D7E5D0","#28563D"])
        st.plotly_chart(fig, use_container_width=True)
    if kec:
        top10 = by_kec.head(10).sort_values("Produksi (ton)")
        fig = px.bar(top10, x="Produksi (ton)", y="Kecamatan", color="Kabupaten", orientation="h", title="10 kecamatan/desa dengan produksi tertinggi")
        st.plotly_chart(fig, use_container_width=True)
    if year and df["Tahun"].nunique() > 1:
        trend = df.groupby("Tahun", as_index=False)["Produksi (ton)"].sum()
        fig = px.line(trend, x="Tahun", y="Produksi (ton)", markers=True, title="Tren produksi menurut tahun")
        st.plotly_chart(fig, use_container_width=True)
with tab2:
    st.markdown("#### Peringkat kabupaten")
    ranking = by_kab.copy()
    ranking.insert(0,"Peringkat",range(1,len(ranking)+1))
    ranking["Kontribusi (%)"] = ranking["Produksi (ton)"]/total*100
    st.dataframe(ranking.round(2), use_container_width=True, hide_index=True)
    st.markdown("#### Rincian kecamatan/desa")
    st.dataframe(by_kec.round(2), use_container_width=True, hide_index=True)
    st.markdown("#### Data yang dianalisis")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("Unduh data hasil filter (CSV)", df.to_csv(index=False).encode("utf-8-sig"), "sikasu_data.csv", "text/csv")
with tab3:
    low = by_kab.iloc[-1]
    st.markdown(f"**1. Kabupaten dengan produksi tertinggi:** {top['Kabupaten']} dengan {top['Produksi (ton)']:,.2f} ton.")
    st.markdown(f"**2. Kabupaten dengan produksi terendah:** {low['Kabupaten']} dengan {low['Produksi (ton)']:,.2f} ton.")
    st.markdown(f"**3. Konsentrasi produksi:** tiga kabupaten teratas menyumbang {top3_share:.1f}% dari total produksi pada filter terpilih.")
    if len(by_kab) > 1:
        st.markdown(f"**4. Selisih tertinggi dan kedua:** {top['Produksi (ton)']-by_kab.iloc[1]['Produksi (ton)']:,.2f} ton.")
    st.caption("Analisis ini bersifat deskriptif sesuai data yang dimasukkan. Hasil tidak menjelaskan penyebab perbedaan produksi.")
st.caption(f"Sumber data: {source_name}. Satuan ditampilkan dalam ton. Periksa kelengkapan, duplikasi, dan satuan data sebelum digunakan dalam laporan.")
