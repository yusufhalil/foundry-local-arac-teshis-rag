# degerlendirme.py
# Sistemi veri/test_sorulari.json'daki etiketli sorularla test eder.
#
#   python degerlendirme.py arama            -> sadece retrieval (hizli, LLM gerekmez)
#   python degerlendirme.py uctan-uca        -> retrieval + Foundry Local cevaplari
#   python degerlendirme.py uctan-uca --model qwen2.5-1.5b
#
# Sonuclar sonuclar/ klasorune markdown ve json olarak yazilir.

import argparse
import json
import re
import statistics
import time
from datetime import datetime

import ayarlar
from teshis import BilgiTabani, TeshisAsistani

SONUC_DIZINI = ayarlar.PROJE_DIZINI / "sonuclar"
KAYNAK_ATIF_DESENI = re.compile(r"\[\d+\]")


def test_sorulari():
    with open(ayarlar.PROJE_DIZINI / "veri" / "test_sorulari.json", encoding="utf-8") as f:
        return json.load(f)


def isabet_var_mi(beklenen, parcalar):
    """Beklenen ifadelerden biri, getirilen parcalardan birinin basliginda geciyor mu?"""
    return any(b.lower() in p.baslik.lower() for b in beklenen for p in parcalar)


def dogru_mu(test, parcalar, reddedildi):
    if test["tur"] == "cevaplanamaz":
        return reddedildi
    return not reddedildi and isabet_var_mi(test["beklenen"], parcalar)


def arama_degerlendir(bilgi):
    satirlar = []
    for t in test_sorulari():
        parcalar = bilgi.ara(t["soru"])
        reddedildi = bilgi.cevaplanamaz_mi(t["soru"], parcalar) is not None
        satirlar.append(
            {
                **t,
                "dogru": dogru_mu(t, parcalar, reddedildi),
                "reddedildi": reddedildi,
                "getirilen": [f"{p.baslik} ({p.skor:.2f})" for p in parcalar],
            }
        )
    return satirlar


def ozet(satirlar):
    cevaplanabilir = [s for s in satirlar if s["tur"] != "cevaplanamaz"]
    cevaplanamaz = [s for s in satirlar if s["tur"] == "cevaplanamaz"]
    return {
        "toplam_dogru": sum(s["dogru"] for s in satirlar),
        "toplam": len(satirlar),
        "cevaplanabilir_isabet": sum(s["dogru"] for s in cevaplanabilir),
        "cevaplanabilir": len(cevaplanabilir),
        "dogru_red": sum(s["dogru"] for s in cevaplanamaz),
        "cevaplanamaz": len(cevaplanamaz),
    }


def ozet_satiri(o):
    return (
        f"Toplam: {o['toplam_dogru']}/{o['toplam']} | "
        f"Cevaplanabilir sorularda doğru kaynak: {o['cevaplanabilir_isabet']}/{o['cevaplanabilir']} | "
        f"Cevaplanamaz sorularda doğru red: {o['dogru_red']}/{o['cevaplanamaz']}"
    )


def md_hucre(metin):
    return metin.replace("|", "\\|").replace("\n", "<br>")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mod", choices=["arama", "uctan-uca"])
    parser.add_argument("--model", default=ayarlar.CHAT_MODELI)
    args = parser.parse_args()

    SONUC_DIZINI.mkdir(exist_ok=True)
    zaman = datetime.now().strftime("%Y-%m-%d %H:%M")
    ayar_ozeti = (
        f"Embedding: `{ayarlar.EMBED_MODELI}`, parça sayısı (k): {ayarlar.KAC_PARCA}, "
        f"benzerlik eşiği: {ayarlar.BENZERLIK_ESIGI}"
    )

    if args.mod == "arama":
        satirlar = arama_degerlendir(BilgiTabani())
        o = ozet(satirlar)
        print(ozet_satiri(o))
        for s in satirlar:
            if not s["dogru"]:
                print(f"  HATALI: {s['soru']} -> {s['getirilen']}")

        md = [f"# Arama (retrieval) değerlendirmesi\n", f"{zaman} — {ayar_ozeti}\n", f"**{ozet_satiri(o)}**\n",
              "| Soru | Tür | Sonuç | Getirilen parçalar |", "|---|---|---|---|"]
        for s in satirlar:
            md.append(
                f"| {md_hucre(s['soru'])} | {s['tur']} | {'✅' if s['dogru'] else '❌'} "
                f"| {md_hucre('<br>'.join(s['getirilen']) or '— (reddedildi)')} |"
            )
        (SONUC_DIZINI / "arama_degerlendirmesi.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        return

    asistan = TeshisAsistani(args.model)
    print(f"Model: {asistan.llm.model}")
    satirlar = []
    sorular = test_sorulari()
    for n, t in enumerate(sorular, start=1):
        t0 = time.perf_counter()
        cevap = asistan.sor(t["soru"])
        toplam_sure = time.perf_counter() - t0
        reddedildi = not cevap.model_cagrildi
        satir = {
            **t,
            "dogru_kaynak": dogru_mu(t, cevap.parcalar, reddedildi),
            "reddedildi": reddedildi,
            "kaynak_atfi": bool(KAYNAK_ATIF_DESENI.search(cevap.metin)),
            "sure_sn": round(toplam_sure, 2),
            "getirilen": [p.baslik for p in cevap.parcalar],
            "cevap": cevap.metin,
        }
        satirlar.append(satir)
        print(f"[{n}/{len(sorular)}] {toplam_sure:5.1f} sn  {t['soru']}")

    model_cagrilanlar = [s for s in satirlar if not s["reddedildi"]]
    sureler = [s["sure_sn"] for s in model_cagrilanlar]
    o = ozet([{**s, "dogru": s["dogru_kaynak"]} for s in satirlar])
    atif = sum(s["kaynak_atfi"] for s in model_cagrilanlar)

    kisa_model = args.model.replace("/", "_")
    md = [
        f"# Uçtan uca değerlendirme — {asistan.llm.model}\n",
        f"{zaman} — {ayar_ozeti}\n",
        f"- **{ozet_satiri(o)}**",
        f"- Model çağrılan cevaplarda kaynak numarası ([1] gibi) kullanımı: {atif}/{len(model_cagrilanlar)}",
        f"- Model çağrılan soru başına süre: ortalama {statistics.mean(sureler):.1f} sn, "
        f"medyan {statistics.median(sureler):.1f} sn, en uzun {max(sureler):.1f} sn\n",
        "> Kaynak doğruluğu otomatik ölçülür. Cevap metninin doğruluğu aşağıdaki tablodan elle kontrol edilmelidir.\n",
        "| # | Soru | Tür | Doğru kaynak | Süre | Cevap |",
        "|---|---|---|---|---|---|",
    ]
    for n, s in enumerate(satirlar, start=1):
        md.append(
            f"| {n} | {md_hucre(s['soru'])} | {s['tur']} | {'✅' if s['dogru_kaynak'] else '❌'} "
            f"| {s['sure_sn']} sn | {md_hucre(s['cevap'])} |"
        )
    (SONUC_DIZINI / f"uctan_uca_{kisa_model}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (SONUC_DIZINI / f"uctan_uca_{kisa_model}.json").write_text(
        json.dumps({"model": asistan.llm.model, "zaman": zaman, "ozet": o, "sonuclar": satirlar},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(ozet_satiri(o))
    print(f"Kaynak atfı: {atif}/{len(model_cagrilanlar)}, ortalama süre {statistics.mean(sureler):.1f} sn")


if __name__ == "__main__":
    main()
