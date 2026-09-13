# Sunum videosu metni (~2-3 dakika)

Barbaros Bey'in beklentisi: **en fazla ~2-5 dakika**, *"projenin amacı neydi, nasıl yapılandırdım, neleri öğrendim"*. Yüz kamerası şart değil, ekran kaydı ve ses yeterli.

**Kayıt önerisi (macOS):** `Cmd + Shift + 5` → "Tüm ekranı kaydet" → Seçenekler → Mikrofon: Dahili mikrofon.
Kayıttan önce `streamlit run web.py` ile arayüzü açın ve modeli bir kez ısıtın (ilk soru yavaş olur).

---

### 1. Giriş: problem (0:00–0:25) — *ekranda README'nin üst kısmı*
> Merhaba, ben Yusuf Halil. Yaz okulunda Foundry Local ile yerel RAG projesini seçtim ve bir **araç arıza teşhis asistanı** yaptım. Sürücü bir arıza kodu veya belirti yazıyor, asistan internet olmadan, tamamen bilgisayarda çalışarak Türkçe tavsiye veriyor.
>
> İlk olarak modelleri RAG olmadan denedim. Phi-3.5 Türkçede aynı kelimeyi tekrarlayıp durdu. Qwen 1.5B ise P0420 kodunu tamamen yanlış açıkladı. Araç arızasında yanlış tavsiye tehlikeli olabilir. Bu yüzden cevapların doğrulanmış bir bilgi tabanına dayanması gerekiyordu.

### 2. Mimari (0:25–1:05) — *ekranda README'deki mimari diyagramı*
> Bilgi tabanında 37 OBD-II arıza kodu ve gösterge ışıkları, acil durumlar gibi rehber belgeler var. Belgeleri başlıklara ve kısa cümle gruplarına bölüp çok dilli E5 modeliyle vektöre çeviriyorum ve SQLite'a kaydediyorum.
>
> Soru gelince önce içindeki arıza kodlarını birebir arıyorum, çünkü embedding modelleri P0301 ile P0302'yi ayırt edemiyor. Kalan yeri anlamsal aramayla dolduruyorum. En ilgili 3 parçayı numaralı kaynak olarak Foundry Local'da çalışan Qwen 2.5 7B modeline veriyorum. Model de kaynak numarası vererek cevaplıyor.
>
> Önemli bir karar: benzerlik eşiğin altındaysa modeli hiç çağırmıyorum ve "bilgim yok, servise gidin" diyorum. Çünkü küçük modeller "bilmiyorum" demek yerine uyduruyor.

### 3. Demo (1:05–2:05) — *ekranda Streamlit arayüzü*
1. `P0301 arıza kodu algılandı` yazın, soldan sensör verisini açın (RPM 820, dalgalı) → **Teşhis et**
   > Model kaynaklara dayanarak buji ve bobini kontrol etmeyi öneriyor. Aşağıda kullandığı kaynakları görebiliyoruz.
2. `Hararet yükseldi, kaputtan buhar geliyor`
   > Kritik bir durum olduğu için cevap güvenlik uyarısıyla başlıyor: aracı durdurun, sıcakken radyatör kapağını açmayın.
3. `P1234 kodu ne demek?` veya `En iyi pizza tarifi nedir?`
   > Bilgi tabanında olmayan bir şey sorunca model çağrılmıyor ve uydurmak yerine servise yönlendiriyor.

### 4. Test ve öğrendiklerim (2:05–2:50) — *ekranda sonuclar/ tabloları*
> Sistemi 25 etiketli soruyla test ettim, 5 tanesi bilerek cevaplanamaz sorulardı. Doğru kaynak 20 sorunun 19'unda bulundu, konu dışı soruların hepsi reddedildi. Cevapları tek tek de okudum: 7B model 20 cevabın 14'ünde tamamen doğru, tehlikeli cevap yok. 1.5B modelde ise 11 hatalı cevap vardı, tekrar döngülerine giriyordu.
>
> Test ederken bir cevabın, hararet ve kaputtan buhar gelen durumda "bu durum acil değil" dediğini gördüm. Otomatik metrik bunu yakalamadı. Bu yüzden hayati durumlar için modelden bağımsız, sabit bir güvenlik uyarısı katmanı ekledim.
>
> En çok şunları öğrendim:
> - Retrieval kalitesi modelden bile önemli. İlk embedding modeli "kaputtan buhar geliyor" sorusuna "buharlaşma emisyon sistemi" parçasını getiriyordu. E5'e geçince düzeldi.
> - Parçalama ve benzerlik eşiği ölçülerek seçilmeli, tahminle değil.
> - "Uydurma" talimatını prompt'a yazmak yetmiyor, kodla garanti etmek gerekiyor.
> - Yerel çalışmanın donanım maliyeti var. 16 GB RAM'de 7B model çok daha iyi Türkçe üretiyor ama daha yavaş.
>
> Kod ve test sonuçları GitHub'da. Teşekkürler.
