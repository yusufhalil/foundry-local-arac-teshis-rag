# sohbet.py
# Komut satirindan asistanla konusma.
# Kullanim:  python sohbet.py            (cikmak icin: q)
# Sensor verisi eklemek icin soruya '|' ile ekleyin:
#   P0301 kodu var | RPM: 820 dalgali, Motor sicakligi: 90C

from teshis import TeshisAsistani, cevabi_yazdir


def main():
    print("Asistan hazırlanıyor...")
    asistan = TeshisAsistani()
    print(f"Hazır. Model: {asistan.llm.model}")
    print("Arıza kodu veya belirti yazın. Sensör verisi için: soru | sensör verisi. Çıkış: q\n")

    while True:
        try:
            girdi = input("Soru> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if girdi.lower() in {"q", "quit", "exit", "çık"}:
            break
        if not girdi:
            continue

        soru, _, sensor = girdi.partition("|")
        cevabi_yazdir(asistan.sor(soru.strip(), sensor.strip() or None))
        print()


if __name__ == "__main__":
    main()
