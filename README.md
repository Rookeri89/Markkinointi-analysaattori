# 📈 Markkinointi-Analysaattori Pro

Streamlit-pohjainen markkinoinnin KPI-analyysityökalu, joka auttaa arvioimaan kampanjoiden tehokkuutta, vertailemaan tuloksia ja ennustamaan budjettitarpeita.

## Ominaisuudet

- **Yksittäinen analyysi** – Syötä kampanjan luvut ja saat automaattisesti lasketut mittarit sekä konsultin suositukset
- **Räätälöity mittarivalinta** – Valitse juuri sinulle tärkeät KPI:t yli 10 mittarin katalogista
- **A/B-vertailu** – Vertaile kahta kampanjaa rinnakkain selkeällä kaavionäkymällä
- **Budjettiennuste** – Laske kuinka paljon budjettia tarvitaan tavoiteltuun konversiomäärään
- **Excel-vienti** – Lataa kaikki tulokset yhdellä klikkauksella raportointia varten

## Tuetut mittarit

| Kategoria | Mittarit |
|-----------|----------|
| 💰 Kustannus | CPC, CPM, CPA, CPL |
| ⚡ Tehokkuus | CTR, CR |
| 📈 Tuotto | ROAS, ROI, RPC |
| ❤️ Sitoutuminen | ER, VVR |

## Asennus ja käynnistys paikallisesti

**Vaatimukset:** Python 3.9+

```bash
# 1. Kloonaa repositorio
git clone https://github.com/sinunnimesi/markkinointi-analysaattori.git
cd markkinointi-analysaattori

# 2. Asenna riippuvuudet
pip install -r requirements.txt

# 3. Käynnistä sovellus
streamlit run markkinointi_ultra.py
```

Sovellus avautuu automaattisesti osoitteeseen `http://localhost:8501`.

## Julkaisu Streamlit Community Cloudissa

1. Lisää tiedostot GitHubiin
2. Kirjaudu osoitteessa [share.streamlit.io](https://share.streamlit.io)
3. Valitse **New app** → valitse reposi ja `markkinointi_ultra.py`
4. Klikkaa **Deploy** – sovellus on julkinen muutamassa minuutissa

## Versiohistoria

- **v5.0** – Räätälöity mittarivalinta lisätty
