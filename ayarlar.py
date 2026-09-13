# ayarlar.py
# Projedeki tum ayarlar tek yerde. Ortam degiskenleriyle degistirilebilir.

import os
from pathlib import Path

PROJE_DIZINI = Path(__file__).resolve().parent

# ---- Veri ----
DB_DOSYASI = PROJE_DIZINI / "dtc.db"
DTC_DOSYASI = PROJE_DIZINI / "veri" / "dtc_kodlari.json"
BELGE_DIZINI = PROJE_DIZINI / "veri" / "belgeler"

# ---- Modeller ----
# Embedding: Turkce destekli, ilk indirmeden sonra tamamen offline calisir
EMBED_MODELI = os.getenv("EMBED_MODELI", "intfloat/multilingual-e5-base")
PARCA_MAX_KARAKTER = int(os.getenv("PARCA_MAX_KARAKTER", "400"))
# Sohbet modeli: Foundry Local katalog adi (alias). Tam model id'si otomatik bulunur.
CHAT_MODELI = os.getenv("CHAT_MODELI", "qwen2.5-7b")

# ---- Arama (retrieval) ----
KAC_PARCA = int(os.getenv("KAC_PARCA", "3"))  # modele verilecek en fazla parca
# Bu benzerligin altindaki parcalar "ilgisiz" sayilir. En iyi parca bile
# altinda kalirsa model hic cagrilmaz, "bilgim yok" cevabi verilir.
# E5 skorlari dar bir aralikta (~0.7-0.9) toplanir; esik embedding modeline gore
# ayarlanmalidir (bkz. sonuclar/embedding_karsilastirmasi.md).
BENZERLIK_ESIGI = float(os.getenv("BENZERLIK_ESIGI", "0.82"))

# ---- Uretim ----
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "350"))
SICAKLIK = float(os.getenv("SICAKLIK", "0.2"))  # dusuk = daha tutarli, daha az uydurma
