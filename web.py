# web.py
# Streamlit ile basit web arayuzu. Tamamen yerelde calisir.
# Kullanim:  streamlit run web.py

import streamlit as st

from teshis import TeshisAsistani, kaynak_etiketi

st.set_page_config(page_title="Yerel Araç Arıza Teşhis Asistanı", page_icon="🔧")


@st.cache_resource(show_spinner="Embedding modeli ve Foundry Local bağlantısı hazırlanıyor...")
def asistan_yukle():
    return TeshisAsistani()


st.title("🔧 Yerel Araç Arıza Teşhis Asistanı")
st.caption("RAG + Microsoft Foundry Local · İnternet bağlantısı gerekmez")

try:
    asistan = asistan_yukle()
except RuntimeError as hata:
    st.error(str(hata))
    st.stop()

with st.sidebar:
    st.subheader("Canlı sensör verisi (isteğe bağlı)")
    sensor_kullan = st.checkbox("Sensör verisini soruya ekle")
    rpm = st.number_input("Motor devri (RPM)", 0, 8000, 820, step=10)
    rpm_dalgali = st.checkbox("Devir dalgalanıyor")
    sicaklik = st.number_input("Soğutma suyu sıcaklığı (°C)", -30, 150, 90)
    voltaj = st.number_input("Akü voltajı (V)", 0.0, 16.0, 14.1, step=0.1)
    hiz = st.number_input("Hız (km/s)", 0, 250, 0)
    st.divider()
    st.caption(f"Model: `{asistan.llm.model}`")
    st.caption(f"Bilgi tabanı: {len(asistan.bilgi.kayitlar)} parça")

ornekler = [
    "P0301 arıza kodu algılandı",
    "Hararet yükseldi, kaputtan buhar geliyor",
    "Kırmızı yağdanlık ışığı yandı",
    "P1234 kodu ne demek?",
]
st.write("Örnek sorular:")
kolonlar = st.columns(len(ornekler))
for kolon, ornek in zip(kolonlar, ornekler):
    if kolon.button(ornek, use_container_width=True):
        st.session_state.soru = ornek

soru = st.text_input("Arıza kodu veya belirtiyi yazın", key="soru")

if st.button("Teşhis et", type="primary") and soru:
    sensor_verisi = None
    if sensor_kullan:
        sensor_verisi = (
            f"RPM: {rpm}{' (dalgalı)' if rpm_dalgali else ''}, "
            f"Soğutma suyu sıcaklığı: {sicaklik}°C, Akü voltajı: {voltaj} V, Hız: {hiz} km/s"
        )

    with st.spinner("Bilgi tabanında aranıyor ve yerel model cevap üretiyor..."):
        cevap = asistan.sor(soru, sensor_verisi)

    if cevap.model_cagrildi:
        st.markdown(cevap.metin)
    else:
        st.warning(cevap.metin)

    if sensor_verisi:
        st.caption(f"Kullanılan sensör verisi: {sensor_verisi}")

    if cevap.parcalar:
        st.subheader("Kaynaklar")
        for n, p in enumerate(cevap.parcalar, start=1):
            etiket = kaynak_etiketi(p)
            with st.expander(f"[{n}] {p.baslik} — {etiket}"):
                st.write(p.metin)
                st.caption(f"Dosya: {p.kaynak}")

    sure = f"Arama: {cevap.arama_suresi * 1000:.0f} ms"
    if cevap.model_cagrildi:
        sure += f" · Üretim: {cevap.uretim_suresi:.1f} sn"
    else:
        sure += " · Model çağrılmadı (yeterli kaynak yok)"
    st.caption(sure)
