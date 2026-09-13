# bilgi_tabani.py
# Bilgi tabanini kurar: belgeleri parcalara boler, embedding uretir, SQLite'a yazar.
# Kullanim:  python bilgi_tabani.py

import json
import re
import sqlite3

import numpy as np

import ayarlar

_embed_model = None


def embed_model():
    """Embedding modelini ilk ihtiyac aninda bir kez yukler."""
    global _embed_model
    if _embed_model is None:
        from sentence_transformers import SentenceTransformer

        try:
            # Model onbellekteyse internete hic cikma (tamamen offline calisma)
            _embed_model = SentenceTransformer(ayarlar.EMBED_MODELI, local_files_only=True)
        except OSError:
            print(f"Embedding modeli ilk kez indiriliyor: {ayarlar.EMBED_MODELI}")
            _embed_model = SentenceTransformer(ayarlar.EMBED_MODELI)
    return _embed_model


def embedding_uret(metinler, tur="belge"):
    """Metin listesini normalize edilmis float32 vektorlere cevirir.
    Normalize oldugu icin cosine benzerlik = basit nokta carpimi.
    E5 ailesi modeller sorgu ve belge icin farkli onek bekler."""
    if "e5" in ayarlar.EMBED_MODELI.lower():
        onek = "query: " if tur == "sorgu" else "passage: "
        metinler = [onek + m for m in metinler]
    vektorler = embed_model().encode(metinler, normalize_embeddings=True)
    return np.asarray(vektorler, dtype=np.float32)


# ---------------------------------------------------------------------------
# Parcalama (chunking)
# ---------------------------------------------------------------------------

def dtc_parcalari():
    """Her arıza kodu kendi basina bir parca olur."""
    with open(ayarlar.DTC_DOSYASI, encoding="utf-8") as f:
        kodlar = json.load(f)

    parcalar = []
    for k in kodlar:
        metin = (
            f"Arıza kodu {k['kod']}: {k['aciklama']}.\n"
            f"Olası sebepler: {k['sebepler']}.\n"
            f"Öneriler: {k['oneriler']}.\n"
            f"Aciliyet: {k['aciliyet']}."
        )
        parcalar.append(
            {
                "kaynak": "dtc_kodlari.json",
                "baslik": f"{k['kod']} - {k['aciklama']}",
                "kod": k["kod"],
                "metin": metin,
            }
        )
    return parcalar


def cumlelere_bol(metin, max_karakter):
    """Metni cumle sinirlarindan, her biri en fazla max_karakter olan gruplara boler.
    Uzun bir bolum tek parca olursa icindeki farkli konular (or. yag, buji, triger)
    tek vektorde karisir ve arama isabeti duser."""
    cumleler = re.split(r"(?<=[.!?])\s+", metin)
    gruplar, mevcut = [], ""
    for cumle in cumleler:
        if mevcut and len(mevcut) + len(cumle) + 1 > max_karakter:
            gruplar.append(mevcut)
            mevcut = cumle
        else:
            mevcut = f"{mevcut} {cumle}".strip()
    if mevcut:
        gruplar.append(mevcut)
    return gruplar


def belge_parcalari(max_karakter=ayarlar.PARCA_MAX_KARAKTER):
    """Markdown belgeleri once '## ' basliklarina, uzun bolumleri de cumle
    gruplarina boler. Her parcaya bolum basligi eklenir ki baglami kaybolmasin."""
    parcalar = []
    for dosya in sorted(ayarlar.BELGE_DIZINI.glob("*.md")):
        icerik = dosya.read_text(encoding="utf-8")
        belge_basligi = icerik.splitlines()[0].lstrip("# ").strip()

        for bolum in re.split(r"^## ", icerik, flags=re.MULTILINE)[1:]:
            satirlar = bolum.strip().splitlines()
            baslik = satirlar[0].strip()
            govde = " ".join(s.strip() for s in satirlar[1:] if s.strip())
            for govde_parcasi in cumlelere_bol(govde, max_karakter):
                parcalar.append(
                    {
                        "kaynak": dosya.name,
                        "baslik": f"{belge_basligi} > {baslik}",
                        "kod": None,
                        # Basligi metne eklemek aramada isabeti artiriyor
                        "metin": f"{baslik}. {govde_parcasi}",
                    }
                )
    return parcalar


# ---------------------------------------------------------------------------
# Veritabani
# ---------------------------------------------------------------------------

def veritabani_kur():
    parcalar = dtc_parcalari() + belge_parcalari()
    print(f"{len(parcalar)} parca icin embedding uretiliyor...")
    vektorler = embedding_uret([p["metin"] for p in parcalar])

    conn = sqlite3.connect(ayarlar.DB_DOSYASI)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS dtc_codes")  # eski surumden kalan tablo
    c.execute("DROP TABLE IF EXISTS parcalar")
    c.execute(
        "CREATE TABLE parcalar ("
        "id INTEGER PRIMARY KEY, kaynak TEXT NOT NULL, baslik TEXT NOT NULL, "
        "kod TEXT, metin TEXT NOT NULL, embedding BLOB NOT NULL)"
    )
    c.execute("CREATE INDEX idx_parcalar_kod ON parcalar(kod)")
    c.executemany(
        "INSERT INTO parcalar (kaynak, baslik, kod, metin, embedding) VALUES (?, ?, ?, ?, ?)",
        [
            (p["kaynak"], p["baslik"], p["kod"], p["metin"], v.tobytes())
            for p, v in zip(parcalar, vektorler)
        ],
    )
    conn.commit()

    ozet = c.execute("SELECT kaynak, COUNT(*) FROM parcalar GROUP BY kaynak").fetchall()
    conn.close()
    for kaynak, adet in ozet:
        print(f"  {kaynak}: {adet} parca")
    print(f"Veritabani hazir: {ayarlar.DB_DOSYASI.name}")


if __name__ == "__main__":
    veritabani_kur()
