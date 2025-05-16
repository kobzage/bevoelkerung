import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import re

# --- Layout konfigurieren ---
st.set_page_config(layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans&display=swap');
html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif !important;
}
div[data-baseweb="tag"] {
    background-color: #dbeafe !important;
    color: #1e3a8a !important;
    border-radius: 8px !important;
    padding: 4px 8px !important;
    font-weight: bold;
}
.block-container {
    padding: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# --- Kopfbereich mit Radiobuttons und Info ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("## Wähle eine Visualisierung:")

col1, col2 = st.columns([4, 1])
with col1:
    seite = st.radio(
        label="",
        options=[
            "📊 Bevölkerung nach Alter und Geschlecht", 
            "🧀 Familienstand – Verteilung nach Geschlecht", 
            "📈 Familienstand nach Alter, Geschlecht und Nationalität",
            "👶 Kohortenanalyse"
        ]
    )
with col2:
    st.markdown("<div style='text-align: right; padding-top: 10px;'>ℹ️ Weitere Infos</div>", unsafe_allow_html=True)

# --- Seite 1 ---

if seite == "📊 Bevölkerung nach Alter und Geschlecht":
    st.title("📊 Bevölkerung nach Alter und Geschlecht in Deutschland")

    @st.cache_data
    def load_population():
        df = pd.read_csv("population_1.csv", encoding="latin1")
        df = df.replace("-", 0)
        df['d_m'] = pd.to_numeric(df['d_m'], errors="coerce")
        df['d_f'] = pd.to_numeric(df['d_f'], errors="coerce")

        def extract_age(age_str):
            if "unter 1 Jahr" in age_str:
                return 0
            elif "mehr" in age_str:
                return 85
            else:
                match = re.match(r"(\d+)", age_str)
                return int(match.group(1)) if match else float('inf')

        df['age_num'] = df['alt'].apply(extract_age)
        df = df.sort_values(['jahr', 'age_num']).drop(columns='age_num')
        return df

    df = load_population()
    jahre = sorted(df['jahr'].unique())
    jahr = st.selectbox("Wähle ein Jahr", jahre)

    df_jahr = df[df['jahr'] == jahr][['alt', 'd_m', 'd_f']]
    df_melted = df_jahr.melt(id_vars='alt', value_vars=['d_m', 'd_f'],
                             var_name='Geschlecht', value_name='Bevölkerung')
    df_melted['Geschlecht'] = df_melted['Geschlecht'].map({'d_m': 'Männer', 'd_f': 'Frauen'})

    chart = alt.Chart(df_melted).mark_bar().encode(
        x=alt.X('alt:N', title='Altersgruppe', sort=None),
        y=alt.Y('Bevölkerung:Q', title='Anzahl'),
        color=alt.Color('Geschlecht:N', title='Geschlecht'),
        tooltip=['alt', 'Geschlecht', 'Bevölkerung']
    ).properties(
        width=1000,
        height=500,
        title=f"Bevölkerung nach Alter und Geschlecht ({jahr})"
    )

    st.altair_chart(chart, use_container_width=True)

    # --- Zusätzliches Käsediagramm + Balkendiagramm ---
    @st.cache_data
    def load_kaese_summe():
        df = pd.read_csv("population_2.csv", encoding="latin1")
        return df

    df_kaese = load_kaese_summe()
    df_kaese_jahre = sorted(df_kaese["jahr"].unique())
    jahr_kaese = st.selectbox("Jahr für Gesamtverteilung ", df_kaese_jahre)

    df_jahr_k = df_kaese[df_kaese["jahr"] == jahr_kaese]
    maenner_cols = ["ledige Männer", "verheiratete Männer", "verwitwete Männer", "geschiedene Männer"]
    frauen_cols = ["ledige Frauen", "verheiratete Frauen", "verwitwete Frauen", "geschiedene Frauen"]

    gesamt_m = df_jahr_k[maenner_cols].sum(axis=1).values[0]
    gesamt_f = df_jahr_k[frauen_cols].sum(axis=1).values[0]
    gesamt_summe = gesamt_m + gesamt_f

    df_kreis = pd.DataFrame({
        "Geschlecht": ["Männer", "Frauen"],
        "Anzahl": [gesamt_m, gesamt_f]
    })

   # st.subheader("🧀 Gesamtbevölkerung nach Geschlecht ")
    st.markdown(f"**👥 Gesamtbevölkerung ({jahr_kaese}): {int(gesamt_summe):,} Personen**".replace(",", "."))

    col1, col2 = st.columns([1, 1.2])  # Balkendiagramm-Spalte etwas breiter

    with col1:
        fig = px.pie(
            df_kreis,
            names="Geschlecht",
            values="Anzahl",
            title=f"Verteilung nach Geschlecht ({jahr_kaese})",
            hole=0.4
        )
        fig.update_traces(textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("<div style='margin-left: -60px'>", unsafe_allow_html=True)  # kleine optische Verschiebung
        df_kaese["gesamt"] = df_kaese[maenner_cols + frauen_cols].sum(axis=1)
        fig_bar = px.bar(
            df_kaese,
            x="jahr",
            y="gesamt",
            title="📈 Gesamtbevölkerung über die Jahre",
            labels={"jahr": "Jahr", "gesamt": "Bevölkerung"},
            height=400
        )
        fig_bar.update_layout(
            yaxis=dict(range=[80_000_000, 85_000_000]),
            xaxis=dict(tickmode='linear'),
            margin=dict(t=40, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)



    st.caption("*Quelle: Statistisches Bundesamt (Destatis)*")

# --- Seite 2 ---

elif seite == "🧀 Familienstand – Verteilung nach Geschlecht":
    st.title("🧀 Familienstand – Verteilung nach Geschlecht ")

    @st.cache_data
    def load_kaese_plotly():
        df = pd.read_csv("population_2.csv", encoding="latin1")
        return df

    df = load_kaese_plotly()
    jahre = sorted(df["jahr"].unique())
    jahr = st.selectbox(" Wähle ein Jahr", jahre)

    df_jahr = df[df["jahr"] == jahr]

    maenner_cols = ["ledige Männer", "verheiratete Männer", "verwitwete Männer", "geschiedene Männer"]
    frauen_cols = ["ledige Frauen", "verheiratete Frauen", "verwitwete Frauen", "geschiedene Frauen"]
    labels = ["Ledig", "Verheiratet", "Verwitwet", "Geschieden"]

    df_m = pd.DataFrame({
        "Familienstand": labels,
        "Anzahl": df_jahr[maenner_cols].values.flatten()
    })

    df_f = pd.DataFrame({
        "Familienstand": labels,
        "Anzahl": df_jahr[frauen_cols].values.flatten()
    })

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"👨 Männer – {jahr}")
        fig_m = px.pie(df_m, names="Familienstand", values="Anzahl", hole=0.4)
        fig_m.update_layout(width=700, height=700, margin=dict(t=40, b=20, l=20, r=20))
        fig_m.update_traces(textinfo="percent+label", pull=[0.03]*4)
        st.plotly_chart(fig_m, use_container_width=True)

    with col2:
        st.subheader(f"👩 Frauen – {jahr}")
        fig_f = px.pie(df_f, names="Familienstand", values="Anzahl", hole=0.4)
        fig_f.update_layout(width=700, height=700, margin=dict(t=40, b=20, l=20, r=20))
        fig_f.update_traces(textinfo="percent+label", pull=[0.03]*4)
        st.plotly_chart(fig_f, use_container_width=True)

    st.caption("*Quelle: Statistisches Bundesamt (Destatis)*")


# --- Seite 3 ---


elif seite == "📈 Familienstand nach Alter, Geschlecht und Nationalität":
    st.title("📈 Entwicklung des Familienstands nach Altersgruppe, Geschlecht und Staatsangehörigkeit")

    @st.cache_data
    def load_familienstand():
        df = pd.read_csv("population_3.csv", encoding="latin1")
        df.replace("-", 0, inplace=True)
        df = df.apply(pd.to_numeric, errors="ignore")
        return df

    df = load_familienstand()

    col1, col2 = st.columns([2, 5])
    with col1:
        st.header("Altersgruppe auswählen")
        altersgruppen = sorted(df['alt'].unique())
        altersgruppe = st.selectbox("", altersgruppen, key="altersgruppe")

        st.subheader("Geschlecht auswählen")
        geschlecht_auswahl = st.multiselect("", ["Männer", "Frauen"], default=["Männer", "Frauen"], key="geschlecht")

        st.subheader("Familienstand auswählen")
        familienstand_auswahl = st.multiselect(
            "", ["Ledig", "Verheiratet", "Verwitwet", "Geschieden"],
            default=["Ledig", "Verheiratet", "Verwitwet", "Geschieden"],
            key="familienstand"
        )
        st.subheader("Staatsangehörigkeitsstatus")
        nationalitaet_auswahl = st.multiselect("", ["Deutsch", "Ausländer"], default=["Deutsch", "Ausländer"], key="nationalitaet")

    with col2:
        prefix_map = {
            ("Deutsch", "Männer"): "d_m_",
            ("Deutsch", "Frauen"): "d_f_",
            ("Ausländer", "Männer"): "a_m_",
            ("Ausländer", "Frauen"): "a_f_"
        }

        status_code = {
            "Ledig": "le",
            "Verheiratet": "vht",
            "Verwitwet": "vwt",
            "Geschieden": "ge"
        }

        aktive_kombis = []
        for nat in nationalitaet_auswahl:
            for g in geschlecht_auswahl:
                prefix = prefix_map[(nat, g)]
                for fs in familienstand_auswahl:
                    short = status_code[fs]
                    colname = f"{prefix}{short}"
                    kombiname = f"{nat} {g} – {fs}"
                    aktive_kombis.append((colname, kombiname))

        aktive_cols = [col for col, _ in aktive_kombis]

        if not aktive_cols:
            st.warning("Bitte wähle mindestens eine Kombination aus.")
        else:
            df_vgl = df[df['alt'] == altersgruppe][['jahr'] + aktive_cols].copy()
            df_vgl = df_vgl.melt(id_vars='jahr', var_name='Kombi', value_name='Anzahl')
            name_map = dict(aktive_kombis)
            df_vgl['Kombi'] = df_vgl['Kombi'].map(name_map)

            chart = alt.Chart(df_vgl).mark_line(point=True).encode(
                x=alt.X('jahr:O', title='Jahr'),
                y=alt.Y('Anzahl:Q', title='Bevölkerung'),
                color=alt.Color('Kombi:N', title='Gruppe – Familienstand'),
                tooltip=['jahr', 'Kombi', 'Anzahl']
            ).properties(
                height=800,
                title=f"Vergleich – Altersgruppe {altersgruppe}"
            )

            st.altair_chart(chart, use_container_width=True)
         st.caption("*Quelle: Statistisches Bundesamt (Destatis)*")

# --- Seite 4 ---


elif seite == "👶 Kohortenanalyse":
    st.title("👶 Kohortenanalyse: Entwicklung nach Geburtsjahrgang")

    @st.cache_data
    def load_kohorte():
        df = pd.read_csv("population_4.csv", encoding="latin1")
        df["alter_num"] = df["alt"].str.extract(r"(\d+)").astype(int)
        df_long = df.melt(
            id_vars=["jahr", "geburtsjahr", "alt", "alter_num"],
            var_name="Gruppe",
            value_name="Anzahl"
        )
        df_long = df_long.dropna(subset=["Anzahl"])
        return df_long

    df_kohorte = load_kohorte()

    gruppen = sorted(df_kohorte["Gruppe"].unique())
    gewaehlte_gruppen = st.multiselect(
        "Gruppe auswählen (z. B. 'verheiratete Männer')",
        options=gruppen,
        default=["verheiratete Männer"]
    )

    jahr_min, jahr_max = int(df_kohorte["geburtsjahr"].min()), int(df_kohorte["geburtsjahr"].max())
    bereich = st.slider("Geburtsjahrgänge auswählen", jahr_min, jahr_max, (1960, 1980))

    df_filtered = df_kohorte[
        (df_kohorte["Gruppe"].isin(gewaehlte_gruppen)) &
        (df_kohorte["geburtsjahr"].between(bereich[0], bereich[1]))
    ]

    if df_filtered.empty:
        st.warning("Keine Daten für die aktuelle Auswahl vorhanden.")
    else:
        chart = alt.Chart(df_filtered).mark_line(point=True).encode(
            x=alt.X("alter_num:O", title="Alter"),
            y=alt.Y("Anzahl:Q", title="Bevölkerung"),
            color=alt.Color("geburtsjahr:N", title="Geburtsjahr"),
            tooltip=["geburtsjahr", "jahr", "alt", "Anzahl"]
        ).properties(
            height=600,
            title=f"Kohortenverlauf – {', '.join(gewaehlte_gruppen)}"
        )

        st.altair_chart(chart, use_container_width=True)
       st.caption("*Quelle: Statistisches Bundesamt (Destatis)*")

