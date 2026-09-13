# OBD-II ve Arıza Kodları Temelleri

## OBD-II nedir
OBD-II (On-Board Diagnostics, ikinci nesil yerleşik teşhis sistemi), aracın motor ve emisyon sistemlerini sürekli izleyen standart bir arıza teşhis sistemidir. Avrupa'da benzinli araçlarda 2001, dizel araçlarda 2004 sonrası üretilen araçların büyük çoğunluğunda bulunur (Avrupa'daki adı EOBD). Bir sensör değeri beklenen aralığın dışına çıktığında kontrol ünitesi bir arıza kodu (DTC) kaydeder ve gerekirse motor arıza lambasını yakar.

## OBD-II soketi nerede bulunur
16 pinli OBD-II soketi genellikle sürücü tarafında, direksiyonun altında, torpido alt panelinde bulunur. Bazı araçlarda sigorta kutusu kapağının arkasında veya orta konsolda olabilir. Ucuz bir ELM327 Bluetooth adaptörü ve bir telefon uygulaması ile arıza kodları okunabilir.

## Arıza kodu (DTC) yapısı
Arıza kodları bir harf ve dört karakterden oluşur, örneğin P0301. İlk harf sistemi belirtir: P (Powertrain) motor ve şanzıman, C (Chassis) şasi, fren ve süspansiyon, B (Body) gövde, hava yastığı ve klima, U (Network) modüller arası iletişim ağıdır. İkinci karakter 0 ise kod tüm üreticilerde ortak (SAE standart), 1 ise üreticiye özeldir. Üçüncü karakter alt sistemi gösterir: 1 ve 2 yakıt ve hava ölçümü, 3 ateşleme sistemi ve ateşleme kaçakları, 4 emisyon kontrol sistemleri, 5 hız ve rölanti kontrolü, 6 bilgisayar ve çıkış devreleri, 7 ve 8 şanzımandır. Son iki karakter belirli arızayı tanımlar.

## Bank ve sensör numaraları
V tipi motorlarda iki silindir sırası bulunur. Bank 1, 1 numaralı silindirin bulunduğu taraftır; Bank 2 karşı taraftır. Sıralı dört silindirli motorlarda yalnızca Bank 1 vardır. Oksijen sensörlerinde Sensör 1 katalitik konvertörden önceki (ön) sensör, Sensör 2 katalitik konvertörden sonraki (arka) sensördür.

## Arıza kodunu silmek sorunu çözer mi
Arıza kodunu OBD-II okuyucu ile silmek motor arıza lambasını geçici olarak söndürür ancak arızanın sebebini ortadan kaldırmaz. Sorun devam ediyorsa kod kısa süre içinde tekrar oluşur. Ayrıca kodların silinmesi, araç muayenesinde emisyon hazırlık testlerinin (readiness monitors) tamamlanmamış görünmesine neden olabilir. Kod silinmeden önce not alınmalı ve sebep giderilmelidir.

## Bekleyen ve kalıcı kodlar
Bekleyen (pending) kodlar, arızanın bir sürüş döngüsünde algılandığını ancak henüz doğrulanmadığını gösterir; lamba yanmayabilir. Arıza art arda sürüş döngülerinde tekrarlanırsa kod onaylanır (confirmed) ve lamba yanar. Kalıcı (permanent) kodlar silme işlemiyle kaldırılamaz, sistem arızanın giderildiğini kendi testleriyle doğrulayınca kaybolur.

## Canlı sensör verileri
OBD-II üzerinden canlı veriler de okunabilir. Önemli değerler şunlardır: motor devri (RPM) sıcak motorda rölantide çoğu benzinli araçta yaklaşık 650-900 devir arasıdır; motor soğutma suyu sıcaklığı normal çalışmada yaklaşık 85-105 °C arasıdır; kısa ve uzun vadeli yakıt düzeltmeleri (fuel trim) normalde yaklaşık ±10 yüzde aralığındadır, +10'un üstü fakir karışıma, -10'un altı zengin karışıma işaret eder; akü voltajı motor kapalıyken yaklaşık 12,4-12,7 V, motor çalışırken yaklaşık 13,5-14,5 V olmalıdır. Rölantide devrin sürekli dalgalanması ateşleme kaçağı veya vakum kaçağı belirtisi olabilir.
