# Üretim Kalitesi, OEE ve Kestirimci Bakım Kontrol Kulesi

Bu proje; OEE, duruş, güvenilirlik, kalite, SPC, süreç yeterliliği ve
açıklanabilir kestirimci bakımı tek bir karar destek mimarisinde birleştiren
uçtan uca bir üretim analitiği platformudur. Kullanılan bütün veriler
deterministik ve tamamen sentetiktir.

> **Operasyonel sınır:** Sistem yalnızca öneri üretir. Makine durdurmaz, bakım
> emri açmaz ve bakım onayı vermez. Her karar yetkin bir insan tarafından
> incelenmek ve onaylanmak zorundadır.

## Doğrulanmış pipeline sonuçları

| Alan | Gerçek pipeline çıktısı |
|---|---:|
| Üretim hattı / makine / ürün / vardiya | 4 / 12 / 4 / 3 |
| Vardiya kaydı / CTQ ölçümü | 19.692 / 98.460 |
| Toplam sentetik üretim | 19.581.400 adet |
| Availability / Performance / Quality | %98,36 / %90,99 / %95,27 |
| OEE | **%85,27** |
| First-pass yield | %95,27 |
| Fire / yeniden işleme | %1,99 / %2,75 |
| Sentetik Cost of Poor Quality | 12.936.905,5 maliyet birimi |
| MTBF / MTTR | 145,96 saat / 1,73 saat |
| Champion / Challenger | Random Forest / Logistic Regression |
| OOT ROC-AUC / PR-AUC | 0,7489 / 0,3887 |
| OOT Brier / ECE | 0,1137 / 0,0164 |
| OOT precision / recall | %26,30 / %73,51 |
| Seçilen olasılık eşiği | 0,1478 |
| OOT alarm oranı / medyan ön süre | %43,11 / 16 saat |
| Test / kapsam | 35 başarılı / **%95,30** |

OOT pozitif oranı %15,43'tür. Bu nedenle 0,3887 PR-AUC, no-skill tabanının
yaklaşık 2,52 katıdır. OOT alarm oranının validation dönemindeki %40 kapasite
sınırını aşması gizlenmemiş, izleme bulgusu olarak raporlanmıştır.

## Kapsam

- OEE bileşenleri ratio-of-sums yaklaşımıyla hesaplanır.
- Planlı ve plansız duruşlar ayrılır; Pareto ve kayıp maliyeti üretilir.
- MTBF ve MTTR sentetik çalışma ve onarım saatlerinden hesaplanır.
- Fire, yeniden işleme, FPY ve iç başarısızlık maliyeti izlenir.
- Sabit `n=5` CTQ alt gruplarında X-bar/R kullanılır.
- Vardiya başına tek pürüzlülük ölçümünde I-MR kullanılır.
- Değişken lot büyüklüğü için p, değişken birim sayısı için u grafiği seçilir.
- Sabit örnek büyüklüğü varsayımı sağlanmadığı için np ve c seçilmemiştir.
- Kontrol limitleri süreç davranışını; LSL/USL ise mühendislik
  spesifikasyonlarını temsil eder ve birbirinden ayrı tutulur.

Detaylar için [SPC metodolojisi](docs/spc_methodology.md) ve
[veri sözleşmesi](docs/data_contract.md) belgelerine bakın.

## Model yönetişimi

- Hedef: takip eden 24 saatte arıza.
- Ayrım: kronolojik development, validation ve out-of-time test.
- Temporal leakage kontrolü: sınırların her iki yanında 24 saatlik purge gap.
- Sınıf dengesizliği: model bazlı class-weight.
- Kalibrasyon: development döneminin daha geç bir penceresinde sigmoid.
- Threshold: validation döneminde asimetrik maliyet, en az %72 recall ve en
  fazla %40 inceleme kapasitesi kısıtı.
- SHAP: champion temel model için global ve lokal açıklamalar.
- Karar politikası: kalibre risk, makine kritiklik düzeyi, arıza maliyeti,
  bakım maliyeti ve müdahale etkinliği.

[Model card](docs/governance/model_card.md),
[validation report](docs/governance/validation_report.md) ve
[risk register](docs/governance/risk_register.md) bütün sınırlamaları açıklar.

## Çalıştırma

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m manufacturing_ct.pipeline --config configs/base.yaml
pytest --cov=manufacturing_ct --cov-report=term-missing
uvicorn manufacturing_ct.api:app --host 0.0.0.0 --port 8000
```

## Teslimatlar

- Power BI başlangıç projesi: [`powerbi/`](powerbi/)
- Formül tabanlı Excel: [`deliverables/excel/`](deliverables/excel/)
- Yönetici sunumu: [`deliverables/presentation/`](deliverables/presentation/)
- Ayrıntılı PDF yönetişim raporu: [`deliverables/report/`](deliverables/report/)
- LinkedIn, CV ve mülakat metinleri: [`docs/portfolio/`](docs/portfolio/)
- Branch protection rehberi: [`docs/branch_protection_guide.md`](docs/branch_protection_guide.md)

Proje; [ISO 22400-2](https://www.iso.org/standard/54497.html),
[ISO 13374](https://www.iso.org/standard/36645.html),
[NIST SPC](https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc3.htm),
[NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework) ve
[NIST SSDF](https://csrc.nist.gov/pubs/sp/800/218/final) kaynaklarını yalnızca
tasarım referansı olarak kullanır. Sertifikasyon veya mevzuat/standart uyumluluğu
iddiası yoktur.
