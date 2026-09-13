# Embedding modeli ve benzerlik eşiği karşılaştırması

25 etiketli test sorusu (`veri/test_sorulari.json`): 20 cevaplanabilir (kod, belirti, genel bilgi) ve 5 cevaplanamaz (bilgi tabanında olmayan kod, konu dışı sorular). k = 3 parça.

- **Doğru kaynak:** Cevaplanabilir sorularda beklenen parçalardan en az biri getirildi mi?
- **Doğru red:** Cevaplanamaz sorularda hiç parça eşiği geçmedi mi (yani model hiç çağrılmadan "bilgim yok" denildi mi)?

| Embedding modeli | En iyi eşik | Doğru kaynak | Doğru red | Toplam |
|---|---|---|---|---|
| paraphrase-multilingual-MiniLM-L12-v2 (ilk sürüm) | 0.35–0.40 | 18/20 | 4/5 | 22/25 |
| paraphrase-multilingual-MiniLM-L12-v2 | 0.50 | 17/20 | 5/5 | 22/25 |
| intfloat/multilingual-e5-small | 0.84 | 18/20 | 5/5 | 23/25 |
| **intfloat/multilingual-e5-base (seçilen)** | **0.82** | **19/20** | **5/5** | **24/25** |

## Gözlemler
- MiniLM, Türkçe'de yüzeysel kelime benzerliğine takıldı. Örneğin "kaputtan **buhar** geliyor" sorusu için "**Buhar**laşma emisyon sistemi (P0455)" parçasını getirdi, "Triger kayışı" sorusunda ise bakım bölümünü bulamadı.
- E5 modelleri 20 cevaplanabilir sorunun tamamında doğru parçayı buldu. Ancak benzerlik skorları dar bir aralıkta (yaklaşık 0.75–0.90) toplandığı için konu dışı sorular da düşük eşiklerde geçiyordu. Eşik 0.82'ye çıkınca 5 konu dışı sorunun hepsi reddedildi.
- Eşik penceresi dar: 0.80'de 2 konu dışı soru geçiyor, 0.86'da 4 cevaplanabilir soru kaçıyor. 25 soruluk küçük bir sette seçildiği için, bilgi tabanı büyüdükçe eşik yeniden ayarlanmalı.
- Uzun belge bölümlerini cümle gruplarına (en fazla 400 karakter) bölmek, tek bir bölümde birden fazla konu olan "Periyodik bakım" gibi yerlerde isabeti artırdı.
- Arıza kodları (P0301 gibi) embedding ile güvenilir ayırt edilemediği için sorgudaki kodlar önce SQLite'ta birebir aranıyor (hibrit arama).
