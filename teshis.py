# teshis.py
# Arac ariza teshis asistani - RAG cekirdegi
#   Retrieve : ariza kodu tam eslesmesi + embedding ile anlamsal arama (SQLite)
#   Augment  : bulunan parcalar numarali kaynaklar olarak prompt'a eklenir
#   Generate : Foundry Local uzerinde calisan yerel LLM cevabi uretir

import re
import sqlite3
import subprocess
import time
from dataclasses import dataclass, field

import numpy as np
from openai import OpenAI

import ayarlar
from bilgi_tabani import embedding_uret

DTC_DESENI = re.compile(r"\b([PCBU][0-9][0-9A-F]{3})\b", re.IGNORECASE)
# Qwen modelleri uzun cevaplarda zaman zaman Cince/Japonca/Korece'ye kayabiliyor
YABANCI_ALFABE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]")

BILGI_YOK_CEVABI = (
    "Bu konuda bilgi tabanımda yeterli bilgi bulamadım. Tahmin yürütmek yerine "
    "aracınızı bir servise veya uzman bir ustaya kontrol ettirmenizi öneririm."
)

# Hayati durumlar icin modelden ve embedding siralamasindan bagimsiz guvenlik katmani.
# Bu durumlarda yanlis/eksik bir cevabin bedeli cok yuksek oldugu icin anahtar kelimeyle
# tetiklenir: (1) sabit uyari cevabin basina her zaman eklenir, (2) ilgili rehber
# bolumleri, embedding siralamasinda geride kalsalar bile kaynaklara zorla eklenir.
# (desen, uyari metni, eklenecek rehber bolumlerinin basliklari)
GUVENLIK_KURALLARI = [
    (
        re.compile(r"hararet|aşırı ısın|asiri isin|kaynatt|kaputtan (buhar|duman)|radyatör.*buhar", re.IGNORECASE),
        "Aracı güvenli bir yere çekip motoru kapatın. Motor sıcakken radyatör veya "
        "genleşme kabı kapağını kesinlikle açmayın; basınçlı sıcak su yanığa neden olabilir.",
        ["Motor aşırı ısındığında yapılacaklar", "Hararet (motor sıcaklığı) uyarı ışığı"],
    ),
    (
        re.compile(r"yağ basınc|yag basinc|yağdanlık|yagdanlik", re.IGNORECASE),
        "Motoru derhal güvenli bir yerde durdurun. Yağ basıncı düşükken çalışan motor kısa sürede ciddi hasar görür.",
        ["Yağ basıncı uyarı ışığı"],
    ),
    (
        re.compile(r"fren.{0,30}(boşa|bosa|tutmuyor|zayıf|zayif|yumuşa|yumusa)|(boşa|bosa).{0,15}fren", re.IGNORECASE),
        "Fren zayıflığı varsa aracı kullanmayın; güvenli şekilde durup yol yardım veya çekici çağırın.",
        ["Fren sistemi uyarı ışığı", "Ne zaman aracı hemen durdurmalı"],
    ),
    (
        re.compile(r"duman|yanık koku|yanik koku", re.IGNORECASE),
        "Duman veya yanık kokusu varsa aracı güvenli bir yerde durdurup motoru kapatın.",
        ["Ne zaman aracı hemen durdurmalı"],
    ),
]

SISTEM_MESAJI = """Sen yerel çalışan bir araç arıza teşhis asistanısın. Kullanıcı sürücüdür, teknisyen değildir.

Kurallar:
1. SADECE "Kaynaklar" bölümündeki bilgileri kullan. Kaynaklarda olmayan bir bilgiyi, parça adını veya sayıyı ASLA uydurma.
2. Kaynakların bir kısmı soruyla ilgisiz olabilir. İlgisiz kaynakları tamamen yok say, onlardan sonuç çıkarma.
3. Kaynaktaki güvenlik uyarılarını yumuşatma veya tersine çevirme; olduğu gibi aktar.
4. Kullandığın her bilginin sonuna kaynağın numarasını köşeli parantezle yaz, örneğin [1].
5. Kaynaklar soruyu cevaplamaya yetmiyorsa bunu açıkça söyle ve servise başvurulmasını öner.
6. Yalnızca kullandığın kaynağın aciliyeti "Kritik" veya "Yüksek" ise ya da kaynak aracı durdurmayı söylüyorsa cevaba güvenlik uyarısıyla başla.
7. Canlı sensör verisi verilmişse, kaynaklardaki normal değerlerle karşılaştırıp yorumla.
8. Cevabı yalnızca Türkçe, kısa (en fazla 6 cümle veya madde) ve adım adım ver."""


@dataclass
class Parca:
    id: int
    kaynak: str
    baslik: str
    kod: str | None
    metin: str
    skor: float
    tam_eslesme: bool = False


@dataclass
class Cevap:
    metin: str
    parcalar: list[Parca] = field(default_factory=list)
    model: str | None = None
    arama_suresi: float = 0.0
    uretim_suresi: float = 0.0
    model_cagrildi: bool = False


# ---------------------------------------------------------------------------
# Foundry Local baglantisi
# ---------------------------------------------------------------------------

def foundry_adresi_bul():
    """Foundry Local servisinin calistigi adresi 'foundry service status' ciktisindan alir."""
    try:
        cikti = subprocess.check_output(
            ["foundry", "service", "status"], text=True, stderr=subprocess.STDOUT, timeout=30
        )
    except (OSError, subprocess.SubprocessError) as e:
        raise RuntimeError("Foundry Local bulunamadi. Kurulu mu? 'foundry --version'") from e

    eslesme = re.search(r"http://(?:127\.0\.0\.1|localhost):\d+", cikti)
    if not eslesme:
        raise RuntimeError(
            "Foundry Local servisi calismiyor. Once su komutu calistirin: foundry service start"
        )
    return eslesme.group(0)


class FoundryIstemci:
    """Foundry Local'in OpenAI-uyumlu API'sine baglanir ve kullanilacak modeli secer."""

    def __init__(self, model_alias=ayarlar.CHAT_MODELI):
        self.adres = foundry_adresi_bul()
        self.client = OpenAI(base_url=self.adres + "/v1", api_key="yerel")
        self.model = self._model_id_bul(model_alias)

    def _model_id_bul(self, alias):
        """'qwen2.5-7b' gibi kisa adi, yuklu modellerden tam id'ye cevirir
        (or. qwen2.5-7b-instruct-generic-gpu:4)."""
        mevcut = [m.id for m in self.client.models.list().data]
        for model_id in mevcut:
            if model_id == alias or model_id.lower().startswith(alias.lower() + "-"):
                return model_id
        raise RuntimeError(
            f"'{alias}' modeli Foundry Local onbelleginde yok. Mevcut modeller: {mevcut}\n"
            f"Indirmek icin: foundry model download {alias}"
        )

    def sohbet(self, mesajlar):
        yanit = self.client.chat.completions.create(
            model=self.model,
            messages=mesajlar,
            max_tokens=ayarlar.MAX_TOKENS,
            temperature=ayarlar.SICAKLIK,
        )
        return yabanci_alfabeyi_kes(yanit.choices[0].message.content.strip())


def yabanci_alfabeyi_kes(metin):
    """Model baska bir dile kaydiysa, kaydigi yerden onceki son tam cumlede keser."""
    eslesme = YABANCI_ALFABE.search(metin)
    if not eslesme:
        return metin
    onceki = metin[: eslesme.start()]
    son_cumle_sonu = max(onceki.rfind("."), onceki.rfind("!"), onceki.rfind("?"), onceki.rfind("\n"))
    return onceki[: son_cumle_sonu + 1].strip() if son_cumle_sonu > 0 else onceki.strip()


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

class BilgiTabani:
    """SQLite'taki parcalari ve embedding'leri bellege alir (kucuk veri icin yeterli)."""

    def __init__(self, db_dosyasi=ayarlar.DB_DOSYASI):
        if not db_dosyasi.exists():
            raise RuntimeError("Veritabani yok. Once calistirin: python bilgi_tabani.py")
        conn = sqlite3.connect(db_dosyasi)
        satirlar = conn.execute(
            "SELECT id, kaynak, baslik, kod, metin, embedding FROM parcalar ORDER BY id"
        ).fetchall()
        conn.close()

        self.kayitlar = [s[:5] for s in satirlar]
        self.vektorler = np.stack([np.frombuffer(s[5], dtype=np.float32) for s in satirlar])
        self.kod_indeksi = {s[3].upper(): i for i, s in enumerate(satirlar) if s[3]}

    def _parca(self, i, skor, tam_eslesme=False):
        return Parca(*self.kayitlar[i], skor=float(skor), tam_eslesme=tam_eslesme)

    def ara(self, sorgu, kac_tane=ayarlar.KAC_PARCA, esik=ayarlar.BENZERLIK_ESIGI):
        """Once sorgudaki ariza kodlarini birebir bulur (embedding'ler 'P0301' gibi
        kodlari iyi ayirt edemez), kalan yeri anlamsal arama sonuclariyla doldurur."""
        sonuc, eklenen = [], set()

        for kod in DTC_DESENI.findall(sorgu):
            i = self.kod_indeksi.get(kod.upper())
            if i is not None and i not in eklenen:
                sonuc.append(self._parca(i, 1.0, tam_eslesme=True))
                eklenen.add(i)

        skorlar = self.vektorler @ embedding_uret([sorgu], tur="sorgu")[0]
        for i in np.argsort(-skorlar):
            if len(sonuc) >= kac_tane or skorlar[i] < esik:
                break
            if i not in eklenen:
                sonuc.append(self._parca(i, skorlar[i]))
                eklenen.add(i)
        return sonuc

    def bolum_parcalari(self, bolum_basligi):
        """Basligi '... > bolum_basligi' olan rehber bolumunun parcalarini dondurur."""
        return [
            self._parca(i, 1.0, tam_eslesme=True)
            for i, kayit in enumerate(self.kayitlar)
            if kayit[2].endswith("> " + bolum_basligi)
        ]

    def cevaplanamaz_mi(self, soru, parcalar):
        """Model cagrilmadan reddedilecek durumlarda red mesajini, degilse None dondurur.
        Kucuk modeller baglam zayifken bile cevap uydurmaya meyilli oldugu icin
        bu karar modele birakilmiyor."""
        bilinmeyen_kodlar = [
            k.upper() for k in DTC_DESENI.findall(soru) if k.upper() not in self.kod_indeksi
        ]
        # Sorulan kod bilgi tabaninda yoksa, benzer ama alakasiz kodlarla cevap uydurmasin
        if bilinmeyen_kodlar and not any(p.tam_eslesme for p in parcalar):
            return f"{', '.join(bilinmeyen_kodlar)} kodu bilgi tabanımda yok. " + BILGI_YOK_CEVABI
        if not parcalar:
            return BILGI_YOK_CEVABI
        return None


# ---------------------------------------------------------------------------
# Asistan
# ---------------------------------------------------------------------------

def tetiklenen_guvenlik_kurallari(soru):
    return [(uyari, bolumler) for desen, uyari, bolumler in GUVENLIK_KURALLARI if desen.search(soru)]


class TeshisAsistani:
    def __init__(self, model_alias=ayarlar.CHAT_MODELI):
        self.bilgi = BilgiTabani()
        self.llm = FoundryIstemci(model_alias)
        embedding_uret(["ısınma"], tur="sorgu")  # embedding modelini simdi yukle, ilk soru yavas olmasin

    @staticmethod
    def _kaynak_metni(parcalar):
        return "\n\n".join(
            f"[{n}] ({p.baslik})\n{p.metin}" for n, p in enumerate(parcalar, start=1)
        )

    def _guvenlik_parcalarini_ekle(self, kurallar, parcalar):
        """Tetiklenen kurallarin rehber bolumlerini en basa koyar, toplam KAC_PARCA'yi asmaz."""
        zorunlu = []
        for _, bolumler in kurallar:
            for bolum in bolumler:
                zorunlu.extend(self.bilgi.bolum_parcalari(bolum))
        if not zorunlu:
            return parcalar

        sonuc, eklenen = [], set()
        for p in zorunlu + parcalar:
            if p.id not in eklenen:
                sonuc.append(p)
                eklenen.add(p.id)
        return sonuc[: max(ayarlar.KAC_PARCA, len(zorunlu))]

    def sor(self, soru, sensor_verisi=None):
        soru = (soru or "").strip()
        if not soru:
            return Cevap(metin="Lütfen bir arıza kodu veya belirti yazın.")

        t0 = time.perf_counter()
        kurallar = tetiklenen_guvenlik_kurallari(soru)
        parcalar = self._guvenlik_parcalarini_ekle(kurallar, self.bilgi.ara(soru))
        arama_suresi = time.perf_counter() - t0

        uyarilar = [uyari for uyari, _ in kurallar]
        uyari_metni = "".join(f"⚠️ **Güvenlik uyarısı:** {u}\n\n" for u in uyarilar)

        red = self.bilgi.cevaplanamaz_mi(soru, parcalar)
        if red:
            return Cevap(metin=uyari_metni + red, parcalar=parcalar, arama_suresi=arama_suresi)

        kullanici_mesaji = f"Kaynaklar:\n{self._kaynak_metni(parcalar)}\n\n"
        if uyarilar:
            # Uyari cevabin basina zaten ekleniyor; modele de verilir ki onunla celisen
            # ("bu durum acil degil" gibi) bir sey yazmasin.
            kullanici_mesaji += (
                "Önemli: Bu durum acildir. Aracı durdurma ve güvenlik adımlarını küçümseyen "
                "veya onlarla çelişen bir şey yazma.\n\n"
            )
        if sensor_verisi:
            kullanici_mesaji += f"Canlı sensör verisi: {sensor_verisi}\n\n"
        kullanici_mesaji += f"Sürücünün sorusu: {soru}"

        t1 = time.perf_counter()
        metin = self.llm.sohbet(
            [
                {"role": "system", "content": SISTEM_MESAJI},
                {"role": "user", "content": kullanici_mesaji},
            ]
        )
        return Cevap(
            metin=uyari_metni + metin,
            parcalar=parcalar,
            model=self.llm.model,
            arama_suresi=arama_suresi,
            uretim_suresi=time.perf_counter() - t1,
            model_cagrildi=True,
        )


def kaynak_etiketi(parca):
    if not parca.tam_eslesme:
        return f"benzerlik {parca.skor:.2f}"
    return "kod eşleşmesi" if parca.kod else "güvenlik kuralı"


def cevabi_yazdir(cevap):
    print("\n" + cevap.metin)
    if cevap.parcalar:
        print("\nKaynaklar:")
        for n, p in enumerate(cevap.parcalar, start=1):
            etiket = kaynak_etiketi(p)
            print(f"  [{n}] {p.baslik}  ({p.kaynak}, {etiket})")
    sure = f"arama {cevap.arama_suresi*1000:.0f} ms"
    if cevap.model_cagrildi:
        sure += f", üretim {cevap.uretim_suresi:.1f} sn, model: {cevap.model}"
    print(f"({sure})")


# ---- Hizli deneme ----
if __name__ == "__main__":
    asistan = TeshisAsistani()
    cevabi_yazdir(
        asistan.sor(
            "P0301 arıza kodu algılandı.",
            sensor_verisi="RPM: 820 (dalgalı), Motor sıcaklığı: 90°C, Hız: 0 km/s",
        )
    )
