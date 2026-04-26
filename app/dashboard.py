import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="Airbnb Dublin - Dashboard",
    layout="wide",
)

CSV_PATH = Path(__file__).resolve().parent.parent / "listings.csv"


@st.cache_data
def cargar_datos() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["last_review"] = pd.to_datetime(df["last_review"], errors="coerce")
    df["name"] = df["name"].fillna("Sin nombre")
    df["host_name"] = df["host_name"].fillna("Desconocido")
    df["neighbourhood"] = df["neighbourhood"].fillna("No especificado")
    df["reviews_per_month"] = df["reviews_per_month"].fillna(0)
    return df


df = cargar_datos()

# ── Sidebar: filtros ─────────────────────────────────────────────────────────
st.sidebar.header("Filtros")

tipos = st.sidebar.multiselect(
    "Tipo de Habitación",
    options=sorted(df["room_type"].unique()),
    default=sorted(df["room_type"].unique()),
)

barrios = st.sidebar.multiselect(
    "Barrio",
    options=sorted(df["neighbourhood"].unique()),
    default=sorted(df["neighbourhood"].unique()),
)

precio_min, precio_max = st.sidebar.slider(
    "Rango de Precio por Noche ($)",
    min_value=0,
    max_value=int(df["price"].max()) if df["price"].notna().any() else 1000,
    value=(0, 500),
)

noches_min = st.sidebar.number_input("Mínimo de noches (máximo)", min_value=0, value=365)

df_filtrado = df[
    (df["room_type"].isin(tipos))
    & (df["neighbourhood"].isin(barrios))
    & (df["price"].between(precio_min, precio_max))
    & (df["minimum_nights"] <= noches_min)
].copy()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Airbnb Dublin - Dashboard")
st.markdown("Análisis interactivo de alojamientos de Airbnb en Dublín, Irlanda.")

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_listings = len(df_filtrado)
precio_mediana = df_filtrado["price"].median() if total_listings > 0 else 0
total_hosts = df_filtrado["host_id"].nunique() if total_listings > 0 else 0
reviews_promedio = df_filtrado["number_of_reviews"].mean() if total_listings > 0 else 0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Alojamientos", f"{total_listings:,}")
kpi2.metric("Precio Mediana/Noche", f"${precio_mediana:,.0f}")
kpi3.metric("Anfitriones Únicos", f"{total_hosts:,}")
kpi4.metric("Reviews Promedio", f"{reviews_promedio:,.1f}")

st.divider()

# ── Mapa de ubicaciones ──────────────────────────────────────────────────────
st.subheader("Mapa de Alojamientos")

df_mapa = df_filtrado.dropna(subset=["latitude", "longitude", "price"])
df_mapa = df_mapa[df_mapa["price"] > 0]

if len(df_mapa) > 0:
    fig_mapa = px.scatter_map(
        df_mapa,
        lat="latitude",
        lon="longitude",
        color="room_type",
        size="price",
        size_max=12,
        hover_name="name",
        hover_data={
            "price": ":$.0f",
            "neighbourhood": True,
            "room_type": True,
            "host_name": True,
            "latitude": False,
            "longitude": False,
        },
        map_style="open-street-map",
        zoom=10,
        height=600,
        opacity=0.7,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_mapa.update_layout(margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_mapa, width='stretch')
else:
    st.warning("No hay datos para mostrar en el mapa con los filtros seleccionados.")

st.divider()

# ── Gráficas principales ─────────────────────────────────────────────────────
col_izq, col_der = st.columns(2)

with col_izq:
    st.subheader("Listings por Tipo de Habitación")
    conteo_tipo = df_filtrado["room_type"].value_counts().reset_index()
    conteo_tipo.columns = ["room_type", "cantidad"]
    fig_tipo = px.bar(
        conteo_tipo,
        x="room_type",
        y="cantidad",
        color="room_type",
        color_discrete_sequence=px.colors.qualitative.Set2,
        labels={"room_type": "Tipo", "cantidad": "Cantidad"},
    )
    fig_tipo.update_layout(showlegend=False)
    st.plotly_chart(fig_tipo, width='stretch')

with col_der:
    st.subheader("Proporción por Tipo")
    fig_pie = px.pie(
        conteo_tipo,
        values="cantidad",
        names="room_type",
        color_discrete_sequence=px.colors.qualitative.Set2,
        hole=0.4,
    )
    st.plotly_chart(fig_pie, width='stretch')

# ── Distribución de precios ──────────────────────────────────────────────────
st.subheader("Distribución de Precios por Tipo de Habitación")
df_precio_valido = df_filtrado[df_filtrado["price"].notna() & (df_filtrado["price"] > 0)]

if len(df_precio_valido) > 0:
    fig_box = px.box(
        df_precio_valido,
        x="room_type",
        y="price",
        color="room_type",
        color_discrete_sequence=px.colors.qualitative.Set2,
        labels={"room_type": "Tipo", "price": "Precio ($)"},
    )
    fig_box.update_layout(showlegend=False)
    st.plotly_chart(fig_box, width='stretch')

# ── Top barrios ───────────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Top 10 Barrios (más listings)")
    top_barrios = (
        df_filtrado["neighbourhood"]
        .value_counts()
        .head(10)
        .reset_index()
    )
    top_barrios.columns = ["neighbourhood", "cantidad"]
    fig_barrios = px.bar(
        top_barrios,
        x="cantidad",
        y="neighbourhood",
        orientation="h",
        color="cantidad",
        color_continuous_scale="Viridis",
        labels={"neighbourhood": "Barrio", "cantidad": "Listings"},
    )
    fig_barrios.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
    st.plotly_chart(fig_barrios, width='stretch')

with col_b:
    st.subheader("Top 10 Barrios más Caros (mediana)")
    precio_barrio = (
        df_filtrado.groupby("neighbourhood")["price"]
        .median()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    precio_barrio.columns = ["neighbourhood", "precio_mediana"]
    fig_precio_barrio = px.bar(
        precio_barrio,
        x="precio_mediana",
        y="neighbourhood",
        orientation="h",
        color="precio_mediana",
        color_continuous_scale="YlOrRd",
        labels={"neighbourhood": "Barrio", "precio_mediana": "Precio Mediana ($)"},
    )
    fig_precio_barrio.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
    st.plotly_chart(fig_precio_barrio, width='stretch')

# ── Mapa de calor ─────────────────────────────────────────────────────────────
st.subheader("Precio Mediana: Tipo de Habitación vs Barrio (Top 8)")
top8 = df_filtrado["neighbourhood"].value_counts().head(8).index
pivot = df_filtrado[df_filtrado["neighbourhood"].isin(top8)].pivot_table(
    values="price", index="room_type", columns="neighbourhood", aggfunc="median", fill_value=0
)

if not pivot.empty:
    fig_heatmap = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            colorscale="YlOrRd",
            text=[[f"${v:,.0f}" for v in row] for row in pivot.values],
            texttemplate="%{text}",
        )
    )
    fig_heatmap.update_layout(height=350)
    st.plotly_chart(fig_heatmap, width='stretch')

# ── Tabla de datos ────────────────────────────────────────────────────────────
st.subheader("Datos Detallados")
columnas_mostrar = [
    "name", "neighbourhood", "room_type", "price",
    "minimum_nights", "number_of_reviews", "host_name", "availability_365",
]
st.dataframe(
    df_filtrado[columnas_mostrar]
    .sort_values("number_of_reviews", ascending=False)
    .reset_index(drop=True),
    width='stretch',
    height=400,
)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("Dashboard generado con Streamlit + Plotly | Dataset: Airbnb Dublin Listings")
