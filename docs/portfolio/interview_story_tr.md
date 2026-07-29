# Mülakat Anlatımı - Türkçe

## 90 saniyelik anlatım

Üretim analitiğinin yalnızca OEE dashboard'undan ibaret olmadığını göstermek
istedim. Bu yüzden üretim kaybı, süreç kararlılığı ve arıza riskini insan
onaylı bakım kararına bağlayan bir kontrol kulesi tasarladım.

İlk zorluk veriydi. Dört hat ve on iki makine için vardiya üretimi,
planlı/plansız duruş, CTQ alt grupları, sensör koşulları ve arıza olayları
üreten deterministik bir simülatör kurdum. Yayınlanan her sayı tek seed ile
yeniden üretilebiliyor.

İkinci zorluk metodolojik doğruluktu. OEE ratio-of-sums ile hesaplanıyor,
kontrol limitleri spesifikasyonlardan ayrılıyor; X-bar/R, I-MR, p ve u grafikleri
veri yapısına göre seçiliyor. Kestirimci bakımda model-fit, calibration,
validation ve out-of-time dönemlerini kronolojik ayırdım ve 24 saatlik purge gap
kullandım. Random Forest champion OOT verisinde 0,7489 ROC-AUC ve 0,3887 PR-AUC
üretti. Trade-off'u gizlemedim: %73,51 recall düzeyinde OOT alarm oranı %43,11
oldu; bu nedenle inceleme kapasitesi monitoring runbook'ta operasyonel kısıt.

Son olarak SHAP nedenleri maliyet-risk politikasına giriyor; ancak servis sadece
öneri veriyor ve insan onayını zorunlu tutuyor. Platform FastAPI, PostgreSQL,
Power BI, Excel, container, monitoring ve %95,30 kapsamlı 35 testi içeriyor.

## Neden accuracy optimize edilmedi?

Olay oranı %15,43. Accuracy, çok az alarm üreten bir modeli ödüllendirebilir.
Bu nedenle PR-AUC, kalibrasyon, recall, alarm yükü ve asimetrik operasyon
maliyeti birlikte değerlendirildi.

## Gerçek tesiste ne değişirdi?

Kaynak sistem ve MSA incelemesi, proses mühendisleriyle rational subgroup
tasarımı, shadow deployment, makine ailesi bazında validation, gerçek sonuçlarla
kalibrasyon, bakım ekibi kapasitesine göre threshold, kurumsal kimlik/secrets
entegrasyonu ve ayrı güvenlik onayı olmadan otomasyona geçmeme yaklaşımı
uygulanırdı.

