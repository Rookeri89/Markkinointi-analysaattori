import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO

# ──────────────────────────────────────────────────────────────────────────────
# SIVUN ASETUKSET
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Markkinointi-Analysaattori Pro", layout="wide", page_icon="📈")

st.markdown("""
<style>
.main { background-color: #f9f9f9; }
.stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #ddd; }
.vinkki-box { padding: 10px 14px; border-radius: 6px; margin-bottom: 8px; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# MITTARIKATALOGI
# Jokainen mittari sisältää:
#   nimi         – näytettävä otsikko
#   kategoria    – ryhmittely multiselect-näkymässä
#   kuvaus       – lyhyt selite (näkyy checkboxin tooltip-tekstinä)
#   lisasyotteet – lista ylimääräisistä syöttökentistä joita tarvitaan
#   laske        – laskufunktio, saa dict d (kaikki syötteet)
#   muoto        – formaattifunktio arvolle
#   parempi      – "korkea" | "matala" | "tasapaino"
#   kynnys_hyvä / kynnys_heikko – benchmarkarvot (tai min/max tasapainossa)
#   vinkki_hyvä / vinkki_heikko – näytettävät tekstit
# ──────────────────────────────────────────────────────────────────────────────
KATALOGI = {
    # ── KUSTANNUS ─────────────────────────────────────────────────────────────
    "CPC": {
        "nimi": "CPC – Hinta per klikkaus",
        "kategoria": "💰 Kustannus",
        "kuvaus": "Yksittäisen klikkauksen keskihinta. Kertoo mainonnan hintatehokkuudesta.",
        "lisasyotteet": [],
        "laske": lambda d: d["kulut"] / d["klikit"] if d["klikit"] > 0 else 0,
        "muoto": lambda v: f"{v:.2f} €",
        "parempi": "matala",
        "kynnys_hyvä": 1.0, "kynnys_heikko": 3.0,
        "vinkki_hyvä":  "✅ **CPC kilpailukykyinen** – klikkaukset ovat edullisia suhteessa markkinaan.",
        "vinkki_heikko": "🔴 **Korkea CPC** – tarkenna kohdennusta tai kokeile uusia mainosmuotoja.",
    },
    "CPM": {
        "nimi": "CPM – Hinta per 1 000 näyttöä",
        "kategoria": "💰 Kustannus",
        "kuvaus": "Tuhannen mainoksen näyttämisen kustannus. Vertailtavuus eri kanavien välillä.",
        "lisasyotteet": [],
        "laske": lambda d: (d["kulut"] / d["naytot"]) * 1000 if d["naytot"] > 0 else 0,
        "muoto": lambda v: f"{v:.2f} €",
        "parempi": "matala",
        "kynnys_hyvä": 5.0, "kynnys_heikko": 20.0,
        "vinkki_hyvä":  "✅ **CPM tehokas** – näkyvyys on edullista.",
        "vinkki_heikko": "🔴 **Korkea CPM** – yleisö on liian kapea tai kilpailu alustalla kovaa.",
    },
    "CPA": {
        "nimi": "CPA – Hinta per konversio",
        "kategoria": "💰 Kustannus",
        "kuvaus": "Yhden halutun toimenpiteen (osto, rekisteröityminen, lataus) hinta.",
        "lisasyotteet": [],
        "laske": lambda d: d["kulut"] / d["konversiot"] if d["konversiot"] > 0 else 0,
        "muoto": lambda v: f"{v:.2f} €",
        "parempi": "matala",
        "kynnys_hyvä": 10.0, "kynnys_heikko": 50.0,
        "vinkki_hyvä":  "✅ **CPA hallinnassa** – konversioiden hankintakustannus on kestävällä tasolla.",
        "vinkki_heikko": "🔴 **Korkea CPA** – optimoi laskeutumissivu tai kohderyhmä.",
    },
    "CPL": {
        "nimi": "CPL – Hinta per liidi",
        "kategoria": "💰 Kustannus",
        "kuvaus": "Yhden potentiaalisen asiakkaan (liidin) hankintakustannus. Tärkeä B2B-mittari.",
        "lisasyotteet": ["liidit"],
        "laske": lambda d: d["kulut"] / d["liidit"] if d.get("liidit", 0) > 0 else 0,
        "muoto": lambda v: f"{v:.2f} €",
        "parempi": "matala",
        "kynnys_hyvä": 15.0, "kynnys_heikko": 60.0,
        "vinkki_hyvä":  "✅ **CPL kilpailukykyinen** – liidit kertyvät kustannustehokkaasti.",
        "vinkki_heikko": "🔴 **Korkea CPL** – testaa eri liidimagneettiä tai tarjousta.",
    },
    # ── TEHOKKUUS ─────────────────────────────────────────────────────────────
    "CTR": {
        "nimi": "CTR – Klikkausprosentti",
        "kategoria": "⚡ Tehokkuus",
        "kuvaus": "Mainoksen nähneistä klikanneiden osuus. Mittaa mainoksen vetovoiman.",
        "lisasyotteet": [],
        "laske": lambda d: (d["klikit"] / d["naytot"]) * 100 if d["naytot"] > 0 else 0,
        "muoto": lambda v: f"{v:.2f} %",
        "parempi": "korkea",
        "kynnys_hyvä": 2.0, "kynnys_heikko": 0.8,
        "vinkki_hyvä":  "✅ **CTR hyvä** – mainos herättää huomion ja saa klikkaukseen.",
        "vinkki_heikko": "🔴 **Matala CTR** – kokeile uusia visuaaleja tai vahvempaa Call-to-Actionia.",
    },
    "CR": {
        "nimi": "CR – Konversioprosentti",
        "kategoria": "⚡ Tehokkuus",
        "kuvaus": "Klikkaajista toiminnon suorittaneiden osuus. Mittaa laskeutumissivun toimivuuden.",
        "lisasyotteet": [],
        "laske": lambda d: (d["konversiot"] / d["klikit"]) * 100 if d["klikit"] > 0 else 0,
        "muoto": lambda v: f"{v:.2f} %",
        "parempi": "korkea",
        "kynnys_hyvä": 3.0, "kynnys_heikko": 1.0,
        "vinkki_hyvä":  "✅ **CR vahva** – laskeutumissivu vakuuttaa kävijän.",
        "vinkki_heikko": "🟡 **Matala CR** – tarkista sivun nopeus, luottamussignaalit ja CTA:n selkeys.",
    },
    # ── TUOTTO ────────────────────────────────────────────────────────────────
    "ROAS": {
        "nimi": "ROAS – Mainostuoton suhde",
        "kategoria": "📈 Tuotto",
        "kuvaus": "Mainoseuron tuottama liikevaihto. ROAS 4x = 1 € mainontaa → 4 € myyntiä.",
        "lisasyotteet": ["tuotto"],
        "laske": lambda d: d["tuotto"] / d["kulut"] if d["kulut"] > 0 else 0,
        "muoto": lambda v: f"{v:.2f}x",
        "parempi": "korkea",
        "kynnys_hyvä": 4.0, "kynnys_heikko": 2.0,
        "vinkki_hyvä":  "✅ **ROAS ylittää tavoitekynnyksen** – kampanja on selkeästi kannattava.",
        "vinkki_heikko": "🔴 **Matala ROAS** – kampanja voi tuottaa tappiota. Priorisoi parhaiten myyvät tuotteet.",
    },
    "ROI": {
        "nimi": "ROI – Sijoitetun pääoman tuotto",
        "kategoria": "📈 Tuotto",
        "kuvaus": "Nettotuoton prosenttiosuus kuluista. ROI 100 % = kaksinkertaisit panostuksesi.",
        "lisasyotteet": ["tuotto"],
        "laske": lambda d: ((d["tuotto"] - d["kulut"]) / d["kulut"]) * 100 if d["kulut"] > 0 else 0,
        "muoto": lambda v: f"{v:.1f} %",
        "parempi": "korkea",
        "kynnys_hyvä": 100.0, "kynnys_heikko": 0.0,
        "vinkki_hyvä":  "✅ **Positiivinen ROI** – kampanja tuottaa enemmän kuin maksaa.",
        "vinkki_heikko": "🔴 **Negatiivinen tai nolla-ROI** – kampanja ei tällä hetkellä kata kulujaan.",
    },
    "RPC": {
        "nimi": "RPC – Tuotto per klikkaus",
        "kategoria": "📈 Tuotto",
        "kuvaus": "Yksittäisen klikkauksen tuottama liikevaihto. Vertaa CPC:hen kannattavuuden arvioimiseksi.",
        "lisasyotteet": ["tuotto"],
        "laske": lambda d: d["tuotto"] / d["klikit"] if d["klikit"] > 0 else 0,
        "muoto": lambda v: f"{v:.2f} €",
        "parempi": "korkea",
        "kynnys_hyvä": 5.0, "kynnys_heikko": 1.0,
        "vinkki_hyvä":  "✅ **RPC yli CPC:n** – jokainen klikkaus tuottaa positiivisen marginaalin.",
        "vinkki_heikko": "🟡 **Matala RPC** – varmista, että RPC ylittää CPC:n, muuten kampanja on tappiollinen.",
    },
    # ── SITOUTUMINEN ──────────────────────────────────────────────────────────
    "ER": {
        "nimi": "ER – Sitoutumisaste",
        "kategoria": "❤️ Sitoutuminen",
        "kuvaus": "Tykkäysten, kommenttien ja jakojen osuus näytöistä. Mittaa sisällön resonanssin.",
        "lisasyotteet": ["sitoutumiset"],
        "laske": lambda d: (d.get("sitoutumiset", 0) / d["naytot"]) * 100 if d["naytot"] > 0 else 0,
        "muoto": lambda v: f"{v:.2f} %",
        "parempi": "korkea",
        "kynnys_hyvä": 3.0, "kynnys_heikko": 0.5,
        "vinkki_hyvä":  "✅ **Hyvä sitoutumisaste** – sisältö resonoi yleisön kanssa.",
        "vinkki_heikko": "🟡 **Matala sitoutumisaste** – kokeile interaktiivisempaa tai tunteisiin vetoavaa sisältöä.",
    },
    "VVR": {
        "nimi": "VVR – Videokatsomisprosentti",
        "kategoria": "❤️ Sitoutuminen",
        "kuvaus": "Mainoksen nähneistä videon loppuun katsonneiden osuus. Toimii video-kampanjoissa.",
        "lisasyotteet": ["videokatselut"],
        "laske": lambda d: (d.get("videokatselut", 0) / d["naytot"]) * 100 if d["naytot"] > 0 else 0,
        "muoto": lambda v: f"{v:.2f} %",
        "parempi": "korkea",
        "kynnys_hyvä": 25.0, "kynnys_heikko": 10.0,
        "vinkki_hyvä":  "✅ **Vahva videokatseluaste** – video koukuttaa katsojan alusta loppuun.",
        "vinkki_heikko": "🟡 **Matala VVR** – siirrä tärkein viesti ensimmäisiin 3 sekuntiin.",
    },
    # ── YLEISÖ ────────────────────────────────────────────────────────────────
    "Taajuus": {
        "nimi": "Taajuus – Frequency",
        "kategoria": "👥 Yleisö",
        "kuvaus": "Kuinka monta kertaa sama henkilö on nähnyt mainoksen. Optimaali 1,5–4x.",
        "lisasyotteet": ["tavoitettu"],
        "laske": lambda d: d["naytot"] / d.get("tavoitettu", 1) if d.get("tavoitettu", 0) > 0 else 0,
        "muoto": lambda v: f"{v:.1f}x",
        "parempi": "tasapaino",
        "kynnys_hyvä": 4.0, "kynnys_heikko": 1.5,
        "vinkki_hyvä":  "✅ **Taajuus optimaalinen** – riittävä muistijälki ilman mainoskyllästymistä.",
        "vinkki_heikko": "🟡 **Taajuus epätasapainossa** – liian alhainen = heikko muistijälki; liian korkea = mainoskyllästyminen.",
    },
}

# Lisäsyöttöjen nimet käyttöliittymää varten
LISASYOTTO_NIMET = {
    "tuotto":        "Tuotto / Liikevaihto (€)",
    "liidit":        "Liidit (kpl)",
    "sitoutumiset":  "Sitoutumiset (tykkäykset + kommentit + jaot)",
    "videokatselut": "Täydet videokatselut (kpl)",
    "tavoitettu":    "Tavoitettu yleisö / Reach (henkilöä)",
}

# ──────────────────────────────────────────────────────────────────────────────
# APUFUNKTIOT
# ──────────────────────────────────────────────────────────────────────────────

def laske_kpi(kulut, naytot, klikit, konversiot, tuotto=0):
    """Peruslaskelma kiinteille kampanjatyypeille."""
    ctr  = (klikit / naytot)      * 100  if naytot > 0      else 0
    cpc  = kulut   / klikit               if klikit > 0      else 0
    cpa  = kulut   / konversiot           if konversiot > 0  else 0
    cr   = (konversiot / klikit)  * 100  if klikit > 0       else 0
    roas = tuotto  / kulut                if kulut > 0        else 0
    cpm  = (kulut  / naytot)      * 1000 if naytot > 0       else 0
    return {"CTR": ctr, "CPC": cpc, "CPA": cpa, "CR": cr, "ROAS": roas, "CPM": cpm}


def laske_raataloity(valitut_avaimet, data):
    """Laske kaikki valitut mittarit dynaamisen datan perusteella."""
    tulokset = {}
    for avain in valitut_avaimet:
        m = KATALOGI[avain]
        try:
            tulokset[avain] = m["laske"](data)
        except Exception:
            tulokset[avain] = 0
    return tulokset


def arvioi_mittari(avain, arvo):
    """Palauttaa (vinkki_teksti, taustaväri, tekstiväri) mittarin arvon perusteella."""
    m = KATALOGI[avain]
    if m["parempi"] == "korkea":
        ok = arvo >= m["kynnys_hyvä"]
    elif m["parempi"] == "matala":
        ok = arvo <= m["kynnys_hyvä"]
    else:  # tasapaino
        ok = m["kynnys_heikko"] <= arvo <= m["kynnys_hyvä"]

    if ok:
        return m["vinkki_hyvä"],  "#d4edda", "#155724"
    else:
        return m["vinkki_heikko"], "#fff3cd", "#856404"


def vinkki_html(teksti, bg, fg):
    return (
        f'<div class="vinkki-box" style="background:{bg};border-left:4px solid {fg};color:{fg}">'
        f'{teksti}</div>'
    )


def anna_vinkit_kiinteat(kpi):
    """Vinkit kiinteille kampanjatyypeille (Kaupallinen / Yleishyödyllinen)."""
    vinkit = []
    if kpi["CTR"] < 1.0:
        vinkit.append(("🔴 **Matala CTR:** Mainoksesi ei pysäytä. Kokeile uusia visuaaleja tai vahvempaa CTA:ta.",
                        "#fff3cd", "#856404"))
    if kpi["CR"] < 2.0:
        vinkit.append(("🟡 **Matala CR:** Käyttäjät klikkaavat, mutta eivät toimi. Tarkista laskeutumissivu.",
                        "#fff3cd", "#856404"))
    if kpi["CPC"] > 2.0:
        vinkit.append(("🔘 **Kallis klikki:** Kilpailu on kovaa. Kokeile tarkentaa kohderyhmää.",
                        "#e8f4fd", "#1a5276"))
    if not vinkit:
        vinkit.append(("✅ **Erinomainen tasapaino:** Kampanja suoriutuu hyvin kaikilla osa-alueilla.",
                        "#d4edda", "#155724"))
    return vinkit


def luo_excel(kpi, kpi_a, kpi_b, raataloity_tulokset=None):
    """Vie kaikki KPI-tiedot Exceliin omille välilehdilleen."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        pd.DataFrame([kpi]).to_excel(writer, index=False, sheet_name="Yksittäinen analyysi")
        df_v = pd.DataFrame([kpi_a, kpi_b], index=["Kampanja A", "Kampanja B"])
        df_v.to_excel(writer, sheet_name="Kampanjavertailu")
        if raataloity_tulokset:
            pd.DataFrame([raataloity_tulokset]).to_excel(writer, index=False, sheet_name="Räätälöity")
    return output.getvalue()


# ──────────────────────────────────────────────────────────────────────────────
# PÄÄVALIKKO
# ──────────────────────────────────────────────────────────────────────────────
st.title("📊 Markkinointi-Analysaattori Pro")
tab1, tab2, tab3 = st.tabs(["Yksittäinen Analyysi", "Kampanjavertailu", "Budjettiennuste"])

raataloity_tulokset = {}   # täytetään Tab 1:ssä, käytetään Excel-exportissa

# ──────────────────────────────────────────────────────────────────────────────
# TAB 1 – YKSITTÄINEN ANALYYSI
# ──────────────────────────────────────────────────────────────────────────────
with tab1:
    st.header("Yksittäisen kampanjan diagnostiikka")
    c1, c2 = st.columns([1, 2])

    with c1:
        tyyppi  = st.selectbox("Kampanjatyyppi:", ["Kaupallinen", "Yleishyödyllinen", "Räätälöity"])
        nimi    = st.text_input("Kampanjan nimi", "Kampanja 1")

        # ── Perussyötteet (kaikille tyypeille) ────────────────────────────
        kulu     = st.number_input("Kulut (€)",   value=1000.0, min_value=0.0)
        n_kerrat = st.number_input("Näytöt",      value=50000,  min_value=0)
        k_klikit = st.number_input("Klikit",      value=1200,   min_value=0)
        n_konv   = st.number_input("Konversiot",  value=40,     min_value=0)

        # ── Kaupallinen: tuottokenttä ──────────────────────────────────────
        n_tuotto = 0.0
        if tyyppi == "Kaupallinen":
            n_tuotto = st.number_input("Tuotto (€)", value=4000.0, min_value=0.0)

        # ── RÄÄTÄLÖITY: mittarivalinta & dynaamiset lisäsyötteet ───────────
        valitut  = []
        lisadata = {}

        if tyyppi == "Räätälöity":
            st.divider()
            st.markdown("**Valitse mitattavat KPI:t:**")

            kategoriat = {}
            for avain, m in KATALOGI.items():
                kategoriat.setdefault(m["kategoria"], []).append(avain)

            for kat, avaimet in kategoriat.items():
                st.markdown(f"*{kat}*")
                for avain in avaimet:
                    m = KATALOGI[avain]
                    if st.checkbox(
                        m["nimi"],
                        value=avain in ["CTR", "CPC", "CPA", "CR"],
                        help=m["kuvaus"],
                        key=f"cb_{avain}",
                    ):
                        valitut.append(avain)

            # Kerää tarvittavat lisäsyötteet valittujen mittareiden perusteella
            tarvitut = set()
            for avain in valitut:
                for ls in KATALOGI[avain]["lisasyotteet"]:
                    tarvitut.add(ls)

            if tarvitut:
                st.divider()
                st.markdown("**Lisätiedot valituille mittareille:**")
                for ls in sorted(tarvitut):
                    lisadata[ls] = st.number_input(
                        LISASYOTTO_NIMET[ls],
                        value=0.0 if ls == "tuotto" else 0,
                        min_value=0.0 if ls == "tuotto" else 0,
                        key=f"ls_{ls}",
                    )

    # ── Laskenta ──────────────────────────────────────────────────────────────
    kpi = laske_kpi(kulu, n_kerrat, k_klikit, n_konv, n_tuotto)

    with c2:
        # ── KIINTEÄT TYYPIT ────────────────────────────────────────────────
        if tyyppi != "Räätälöity":
            cols = st.columns(3)
            cols[0].metric("CTR", f"{kpi['CTR']:.2f} %")
            cols[1].metric("CPA", f"{kpi['CPA']:.2f} €")
            if tyyppi == "Kaupallinen":
                cols[2].metric("ROAS", f"{kpi['ROAS']:.2f}x")
            else:
                cols[2].metric("CR %", f"{kpi['CR']:.2f} %")

            st.subheader("💡 Konsultin suositukset")
            for teksti, bg, fg in anna_vinkit_kiinteat(kpi):
                st.markdown(vinkki_html(teksti, bg, fg), unsafe_allow_html=True)

        # ── RÄÄTÄLÖITY ─────────────────────────────────────────────────────
        else:
            if not valitut:
                st.info("Valitse vähintään yksi mittari vasemmalta.")
            else:
                data = {
                    "kulut":      kulu,
                    "naytot":     n_kerrat,
                    "klikit":     k_klikit,
                    "konversiot": n_konv,
                    **lisadata,
                }
                raataloity_tulokset = laske_raataloity(valitut, data)

                # ── Metriikaruudukko (max 4 per rivi) ─────────────────────
                for i in range(0, len(valitut), 4):
                    era   = valitut[i : i + 4]
                    cols  = st.columns(len(era))
                    for col, avain in zip(cols, era):
                        arvo  = raataloity_tulokset[avain]
                        otsikko = KATALOGI[avain]["nimi"].split("–")[0].strip()
                        col.metric(otsikko, KATALOGI[avain]["muoto"](arvo))

                st.divider()

                # ── Tutkakaavio (vähintään 3 mittaria) ────────────────────
                if len(valitut) >= 3:
                    theta = [KATALOGI[a]["nimi"].split("–")[0].strip() for a in valitut]
                    normit = []
                    for avain in valitut:
                        m    = KATALOGI[avain]
                        arvo = raataloity_tulokset[avain]
                        lo, hi = m["kynnys_heikko"], m["kynnys_hyvä"]
                        if hi == lo:
                            n = 0.5
                        elif m["parempi"] == "matala":
                            # matala on parempi: käännetään asteikko
                            n = 1.0 - min(max((arvo - lo) / (hi - lo), 0.0), 1.0)
                        else:
                            n = min(max((arvo - lo) / (hi - lo), 0.0), 1.0)
                        normit.append(n)

                    fig_radar = go.Figure()
                    fig_radar.add_trace(go.Scatterpolar(
                        r=normit + [normit[0]],
                        theta=theta + [theta[0]],
                        fill="toself",
                        name=nimi,
                        line_color="#3a9ad9",
                        fillcolor="rgba(58,154,217,0.2)",
                    ))
                    fig_radar.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                        title="Kampanjan suoritusprofiili (normalisoitu 0–1)",
                        showlegend=False,
                        height=380,
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)

                # ── Mittarikohtaiset vinkit ────────────────────────────────
                st.subheader("💡 Mittarikohtaiset suositukset")
                for avain in valitut:
                    arvo = raataloity_tulokset[avain]
                    teksti, bg, fg = arvioi_mittari(avain, arvo)
                    st.markdown(vinkki_html(teksti, bg, fg), unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# TAB 2 – KAMPANJAVERTAILU
# ──────────────────────────────────────────────────────────────────────────────
with tab2:
    st.header("A/B-testaus ja kanavavertailu")
    v_col1, v_col2 = st.columns(2)

    with v_col1:
        st.subheader("Kampanja A")
        ka_kulu   = st.number_input("A: Kulut (€)",  value=500.0, min_value=0.0)
        ka_naytot = st.number_input("A: Näytöt",     value=10000, min_value=0)
        ka_klikit = st.number_input("A: Klikit",     value=200,   min_value=0)
        ka_konv   = st.number_input("A: Konversiot", value=10,    min_value=0)

    with v_col2:
        st.subheader("Kampanja B")
        kb_kulu   = st.number_input("B: Kulut (€)",  value=500.0, min_value=0.0)
        kb_naytot = st.number_input("B: Näytöt",     value=10000, min_value=0)
        kb_klikit = st.number_input("B: Klikit",     value=250,   min_value=0)
        kb_konv   = st.number_input("B: Konversiot", value=8,     min_value=0)

    kpi_a = laske_kpi(ka_kulu, ka_naytot, ka_klikit, ka_konv)
    kpi_b = laske_kpi(kb_kulu, kb_naytot, kb_klikit, kb_konv)

    m1, m2, m3 = st.columns(3)
    m1.metric("A – CPC", f"{kpi_a['CPC']:.2f} €",
              delta=f"{kpi_a['CPC']-kpi_b['CPC']:+.2f} vs B", delta_color="inverse")
    m2.metric("A – CPA", f"{kpi_a['CPA']:.2f} €",
              delta=f"{kpi_a['CPA']-kpi_b['CPA']:+.2f} vs B", delta_color="inverse")
    m3.metric("A – CR%", f"{kpi_a['CR']:.2f} %",
              delta=f"{kpi_a['CR']-kpi_b['CR']:+.2f} vs B")

    fig = go.Figure()
    mittarit = ["CTR (%)", "CPC (€)", "CPA (€)", "CR (%)"]
    fig.add_trace(go.Bar(name="Kampanja A", x=mittarit,
                         y=[kpi_a["CTR"], kpi_a["CPC"], kpi_a["CPA"], kpi_a["CR"]]))
    fig.add_trace(go.Bar(name="Kampanja B", x=mittarit,
                         y=[kpi_b["CTR"], kpi_b["CPC"], kpi_b["CPA"], kpi_b["CR"]]))
    fig.update_layout(barmode="group", title="Kampanjavertailu – kaikki mittarit")
    st.plotly_chart(fig, use_container_width=True)


# ──────────────────────────────────────────────────────────────────────────────
# TAB 3 – BUDJETTIENNUSTE
# ──────────────────────────────────────────────────────────────────────────────
with tab3:
    st.header("Skaalaus- ja budjettilaskuri")
    st.info("ℹ️ Ennuste perustuu **Yksittäinen Analyysi** -välilehden CPA-arvoon.")

    if kpi["CPA"] == 0:
        st.warning("CPA on nolla – tarkista konversiomäärä Yksittäinen Analyysi -välilehdellä.")
    else:
        tavoite_n = st.slider("Tavoiteltu konversiomäärä (kpl)", 1, 500, 100)
        tarve     = tavoite_n * kpi["CPA"]
        st.success(
            f"Tavoitteen saavuttaminen vaatii nykyisellä teholla "
            f"**{tarve:,.2f} €** budjetin  (CPA = {kpi['CPA']:.2f} €)."
        )

        x_range    = list(range(1, tavoite_n + 21))
        y_range    = [x * kpi["CPA"] for x in x_range]
        fig_ennuste = px.line(
            x=x_range, y=y_range,
            labels={"x": "Konversiot (kpl)", "y": "Budjetti (€)"},
            title="Kustannusten kasvu konversiomäärän mukaan",
        )
        fig_ennuste.add_vline(
            x=tavoite_n, line_dash="dash", line_color="red",
            annotation_text="Tavoite", annotation_position="top right",
        )
        st.plotly_chart(fig_ennuste, use_container_width=True)


# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR – EXCEL EXPORT
# ──────────────────────────────────────────────────────────────────────────────
st.sidebar.divider()
st.sidebar.header("Lataa Raportti")
st.sidebar.download_button(
    "📥 Lataa kaikki tiedot (Excel)",
    luo_excel(kpi, kpi_a, kpi_b, raataloity_tulokset or None),
    "markkinointi_raportti.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
st.sidebar.caption("Versio 5.0 – Räätälöity mittarivalinta.")
