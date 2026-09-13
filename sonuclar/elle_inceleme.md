# Cevapların elle incelenmesi

Otomatik test yalnızca **doğru kaynağın bulunup bulunmadığını** ölçüyor. Cevap metninin doğruluğunu ölçemiyor. Bu yüzden 20 cevaplanabilir sorudaki cevapları tek tek okuyup puanladım (13 Eylül 2026, son sürüm).

- **Doğru:** Kaynağa sadık, eksiksiz ve güvenli.
- **Kısmen:** Özünde doğru ama gereksiz/abartılı ifade, eksik atıf veya küçük hata içeriyor.
- **Hatalı:** Yanlış bilgi, ilgisiz kaynaktan çıkarım veya anlamsız metin.
- **Tehlikeli:** Sürücüyü güvensiz davranışa yönlendirebilir.

| | qwen2.5-7b | qwen2.5-1.5b |
|---|---|---|
| Doğru | **14** | 4 |
| Kısmen | 4 | 4 |
| Hatalı | 1 | 11 |
| Model çağrılmadı (kaynak bulunamadı, servise yönlendirdi) | 1 | 1 |
| Tehlikeli (Hatalı'nın içinde) | **0** | 3 |
| Cevapta kaynak numarası | 13/19 | 0/19 |
| Soru başına ortalama süre | 17.2 sn | 7.6 sn |

## qwen2.5-7b notları
- **Hatalı (#10, gevşek yakıt kapağı):** "Hızınızı azaltın" önerisini yanıp sönen motor lambası bölümünden yanlış yere taşıdı ve kapağı sıkmak için teknisyen gerektiğini söyledi.
- **Kısmen:**
  - #3 anlamsız dolgu cümle ("simultaneously").
  - #6 ve #17 kaynakta olmayan "Kritik" ifadesi.
  - #11 DPF için yanlış aciliyet seviyesi.
- **#19:** Doğru kaynak eşiği geçemedi. Model çağrılmadı, servise yönlendirdi (güvenli ama faydasız).

## qwen2.5-1.5b notları
- **Tehlikeli:**
  - #1 "katalizör zarar göremedikçe sürüşe devam edin" dedi.
  - #7 yağ basıncı düşükken motorun "ciddi hasar göremeyeceğini" söyleyerek kaynağın tersini yazdı. Başa eklenen sabit güvenlik uyarısı doğru olduğu için sürücü yine de doğru ilk adımı görüyor.
  - #16 ABS sorusunda "EVEM, fren tutarlıdır" deyip "kodlu kodlu kodlu…" diye tekrara girdi.
- **Tekrar döngüsü:** #9, #11, #14 ve #17'de aynı cümleyi max token sınırına kadar tekrarladı.
- **Talimat sızıntısı (#8):** İçerik doğru olsa da prompt'taki iç talimatı cevaba kopyaladı.

## Geliştirme sürecinde yakalanan ve düzeltilen sorunlar (qwen2.5-7b)
| Sorun | İlk sürümdeki cevap | Çözüm |
|---|---|---|
| Güvenlik uyarısını tersine çevirme | ABS: "acil durumlarda tehlike oluşturmadan kullanabilirsiniz" | Prompt: "güvenlik uyarılarını yumuşatma veya tersine çevirme" |
| İlgisiz kaynaktan çıkarım | "Kod silme" sorusunda "kodunuz P0741 veya P0300 ise acil" | Prompt: "ilgisiz kaynakları tamamen yok say" |
| Dile kayma | Cevabın ortasında Çince metin | Çince/Japonca/Korece karakterden önceki son cümlede kesme |
| Hayati durumda yanlış yönlendirme | Hararet + buhar: "Bu durum acil değil" | Anahtar kelimeyle tetiklenen sabit güvenlik uyarısı + modele "bu durum acildir" bilgisi |
| Hayati durumda yanlış kaynak | "Hararet yükseldi, kaputtan buhar geliyor" (web arayüzünde denerken): arama sadece "Buharlaşma emisyonu (P0455)" parçasını getirdi, model yakıt kapağını anlattı | Güvenlik kuralı tetiklenince ilgili rehber bölümü ("Motor aşırı ısındığında yapılacaklar") kaynaklara zorla ekleniyor |

İlk sürümün tam çıktısı: [deneyler/uctan_uca_qwen2.5-7b_prompt_v1.md](../deneyler/uctan_uca_qwen2.5-7b_prompt_v1.md)
