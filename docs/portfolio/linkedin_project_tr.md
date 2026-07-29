# LinkedIn Proje Açıklaması - Türkçe

Deterministik ve tamamen sentetik veriler kullanılarak 4 üretim hattı, 12
makine, 4 ürün ve 3 vardiyayı kapsayan uçtan uca Manufacturing Quality, OEE &
Predictive Maintenance Control Tower geliştirildi.

Platform; OEE bileşenleri, planlı/plansız duruş Pareto analizi, MTBF/MTTR, fire,
yeniden işleme, first-pass yield, Cost of Poor Quality, SPC ve süreç yeterlilik
metriklerini tek mimaride birleştiriyor. Veri tipine uygun X-bar/R, I-MR, p ve u
kontrol grafikleri; dokümante edilmiş alarm kuralları, sabit development
baseline'ı ve kontrol limitleri ile mühendislik spesifikasyon limitlerinin açık
ayrımıyla uygulandı.

24 saat içinde arıza olasılığını tahmin eden leakage kontrollü pipeline;
kronolojik development, validation ve out-of-time test dönemlerinde kalibre
Random Forest ile Logistic Regression modellerini karşılaştırıyor. Seçilen
champion model OOT verisinde 0,7489 ROC-AUC ve 0,3887 PR-AUC üretti; no-skill PR
tabanı 0,1543 iken Brier skoru 0,1137 ve kapasite kısıtlı threshold'da recall
%73,51 olarak ölçüldü.

Global/lokal SHAP açıklamaları bakım neden kodlarına dönüştürüldü. Öneri sistemi;
arıza olasılığı, makine kritiklik seviyesi, tahmini arıza maliyeti, bakım
maliyeti ve müdahale etkinliğini birleştiriyor; insan onayı her zaman zorunlu.

Python, scikit-learn, SHAP, FastAPI, PostgreSQL, Power BI Project, Excel, Docker,
Kubernetes, Prometheus, Grafana ve GitHub Actions kullanıldı. Projede 35 test ve
%95,30 test kapsamı; CodeQL, pip-audit, Trivy, Dependabot, model yönetişimi,
threat model, incident response ve uyumluluk iddiası içermeyen reference
crosswalk bulunuyor.

