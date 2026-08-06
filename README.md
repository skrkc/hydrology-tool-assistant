# 🌀 Akarsu Gözlem ve Debi Uyarı Asistanı

Bu proje, iki ödevi tek bir repo altında sunmaktadır:

1. **Custom Chat Template (Jinja2)**
2. **Tool-Calling Assistant**

Projenin senaryosu, Kocaeli bölgesindeki sentetik akarsu gözlem istasyonları üzerinden hidrolojik ölçümlerin sorgulanması ve debi eşik uyarılarının oluşturulmasıdır.

---

## 1. Custom Chat Template (Jinja2)

Bu bölümde Hafta 1'de geliştirdiğim kendi ByteLevel BPE tokenizer'ım kullanılmıştır:

```text
srhskrkc/odysseia-bpe-tokenizer
```

Tokenizer reposu:

```text
https://huggingface.co/srhskrkc/odysseia-bpe-tokenizer
```

Hafta 3.2 kapsamında bu tokenizer sohbet kullanımına uygun şekilde genişletilmiştir. BPE modeli
yeniden eğitilmemiş; yalnızca aşağıdaki sohbet rol tokenları eklenmiştir:

- `<|system|>`
- `<|user|>`
- `<|assistant|>`

Mevcut `<|endoftext|>` tokenı BOS/EOS olarak korunmuştur.

`chat_template.jinja`, yalnızca metin tabanlı `system`, `user` ve `assistant` mesajlarını işler.
Şablon özellikle sade tutulmuştur; tool-calling uygulamasının karmaşık tool formatı bu ödevdeki
tokenizer şablonuna karıştırılmamıştır.

### Chat Template Testi

```bash
python test_chat_template.py
```

`test_chat_template.py`, başka bir modelin tokenizer'ını kullanmaz. Doğrudan
`srhskrkc/odysseia-bpe-tokenizer` reposunu yükler ve tokenizer içinde kayıtlı olan
`chat_template` ile `apply_chat_template()` çalıştırır.

Örnek çıktı yapısı:

```text
<|endoftext|>
<|system|>
Sen yardımcı bir Türkçe asistansın.
<|endoftext|>
<|user|>
Odysseus kimdir?
<|endoftext|>
<|assistant|>
```

> Tool-Calling Assistant ayrı bir ödev bölümüdür. Uygulamada kullanılan
> `openai/gpt-oss-20b` modeli, Hugging Face Inference Providers tarafındaki kendi chat/tool
> formatını kullanır. Odysseia tokenizer'ındaki bu Jinja şablonu Ödev 1'i göstermek içindir.

---

## 2. Tool-Calling Assistant

Tool-Calling Assistant, doğal dilde ilerleyen **çok turlu bir hidroloji senaryosunu** yürütür. Konuşma geçmişini korur, gerekli araçları LLM seçer ve SQLite veritabanı üzerinde gerçek okuma/yazma işlemleri gerçekleştirir.

### Kullanılan Model

```text
openai/gpt-oss-20b
```

Model, Hugging Face Inference Providers üzerinden çağrılmaktadır.

Tool seçiminde:

```text
tool_choice="auto"
```

kullanılmaktadır.

---

## 🏗️ Mimari

Genel işlem akışı:

```text
Kullanıcı Mesajı + Konuşma Geçmişi
   ↓
Gradio Arayüzü + gr.State
   ↓
LLM Agent
   ↓
Tool Calling
   ↓
Python Tool Dispatcher
   ↓
SQLite Veritabanı
   ↓
Tool Response
   ↓
LLM
   ↓
Nihai Yanıt + Güncellenmiş Konuşma Geçmişi
```

Ana bileşenler:

```text
app.py
    ↓
agent.py
    ↓
tool_schemas.py
    ↓
tools.py
    ↓
database.py
    ↓
data/hydrology.db
```

### Dosyaların Görevleri

- `app.py`: Gradio kullanıcı arayüzünü oluşturur.
- `agent.py`: LLM ile iletişimi ve çok adımlı tool-calling döngüsünü yönetir.
- `tool_schemas.py`: Modele sunulan tool şemalarını içerir.
- `tools.py`: Modelden gelen tool çağrılarını ilgili Python fonksiyonlarına yönlendirir.
- `database.py`: SQLite okuma ve yazma işlemlerini gerçekleştirir.
- `init_database.py`: Veritabanı tablolarını ve örnek başlangıç verilerini oluşturur.
- `chat_template.jinja`: Custom Chat Template ödevini içerir.
- `test_chat_template.py`: Chat Template'i tokenizer üzerinde test eder.

---

## 🎛️ Araçlar

Projede dört küçük ve birbirini tamamlayan tool bulunmaktadır.

### `list_stations`

Aktif akarsu gözlem istasyonlarını listeler.

**Tür:** Okuma

Örnek istek:

```text
Kocaeli'deki aktif istasyonları listele.
```

---

### `get_latest_measurement`

Belirtilen istasyonun en güncel:

- Debi (`m³/s`)
- Su seviyesi (`m`)
- Ölçüm zamanı

bilgilerini SQLite veritabanından getirir.

**Tür:** Okuma

Örnek istek:

```text
Kirazdere istasyonunun en güncel debi ve su seviyesi nedir?
```

---

### `create_flow_alert`

Bir istasyon için yeni debi eşik uyarısı oluşturur.

Veritabanındaki `alerts` tablosuna gerçek kayıt ekler.

**Tür:** Yazma

Temel parametreler:

- `station_name`
- `threshold_m3s`
- `note`

---

### `list_flow_alerts`

Daha önce oluşturulmuş debi uyarılarını SQLite veritabanından tekrar okur. İstenirse belirli bir istasyona göre filtreler.

**Tür:** Okuma

Örnek istek:

```text
Kirazdere için oluşturduğum uyarıları göster.
```

Bu araç sayesinde bir önceki turda veritabanına yazılan uyarının sonraki turda gerçekten okunabildiği gösterilir.

---

## 🗄️ SQLite Veritabanı

Proje gerçek bir SQLite veritabanı kullanmaktadır:

```text
data/hydrology.db
```

Temel tablolar:

- `stations`
- `measurements`
- `alerts`

Örnek istasyonlar:

- Kirazdere
- Kullar
- Yuvacık

Kirazdere için örnek ölçüm:

```text
Debi: 61.2 m³/s
Su seviyesi: 2.25 m
```

> Projedeki hidrolojik veriler eğitim ve demonstrasyon amacıyla oluşturulmuş sentetik verilerdir.

---

## 🔮 Hallüsinasyon Önleme

Agent'ın veritabanında bulunmayan hidrolojik değerleri üretmemesi için sistem promptunda kısıtlamalar bulunmaktadır.

Modelden:

- Veritabanından veya tool sonucundan gelmeyen hidrolojik değerleri uydurmaması
- Tool başarısız olduğunda bunu kullanıcıya açıkça belirtmesi
- Veritabanında bulunmayan bir istasyon için ölçüm üretmemesi
- Bir uyarının başarıyla oluşturulduğunu yalnızca `create_flow_alert` aracı başarı döndürürse söylemesi

istenmektedir.

Örneğin kullanıcı:

```text
Atlantis istasyonunun en güncel debi ve su seviyesi nedir?
```

diye sorduğunda sistem `get_latest_measurement` aracını çağırır.

Tool sonucu:

```json
{
  "found": false,
  "message": "'Atlantis' adlı aktif istasyon için ölçüm kaydı bulunamadı."
}
```

şeklinde döndüğünde model herhangi bir debi veya su seviyesi uydurmaz.

Örnek nihai cevap:

```text
“Atlantis” adlı istasyon için ölçüm kaydı bulunamadı.
Bu nedenle en güncel debi ve su seviyesi bilgisi verilememektedir.
```

---

## 🔁 Çok Turlu Senaryo ve Tool Calling Örneği

Ödevdeki "küçük bir hikâye" yaklaşımı için uygulama tek bir uzun komut yerine birkaç doğal konuşma turuyla kullanılabilir:

### Tur 1 — Sistemi keşfetme

**Kullanıcı:**

```text
Kocaeli'deki aktif akarsu gözlem istasyonları hangileri?
```

Agent `list_stations` aracını çağırır ve SQLite'taki gerçek istasyon listesini kullanıcıya verir.

### Tur 2 — Bir istasyonu inceleme

**Kullanıcı:**

```text
Kirazdere'nin son ölçümüne bakalım.
```

Agent konuşma bağlamını korur ve `get_latest_measurement("Kirazdere")` aracını çağırır. Örnek veritabanında son debi `61.2 m³/s`, su seviyesi `2.25 m` olarak döner.

### Tur 3 — Gerçek yazma işlemi

**Kullanıcı:**

```text
Onun için 65 m³/s eşikli bir uyarı oluştur. Not: Vardiya kontrolü.
```

"Onun" ifadesi önceki turdaki Kirazdere bağlamından çözülür. Agent `create_flow_alert` aracını çağırır ve `alerts` tablosuna gerçek kayıt eklenir.

### Tur 4 — Yazılan veriyi tekrar okuma

**Kullanıcı:**

```text
Kirazdere için oluşturduğum uyarıları göster.
```

Agent `list_flow_alerts` aracını çağırır. Böylece önceki turda oluşturulan uyarının veritabanında gerçekten bulunduğu ve durumunun `ACTIVE` olduğu tekrar okunur.

Bu senaryoda kullanıcı → LLM → tool → SQLite → tool response → LLM döngüsü birden fazla konuşma turu boyunca devam eder. Uygulamadaki `gr.State`, konuşma geçmişini sonraki kullanıcı mesajına taşır.

---

## 💻 Yerel Kurulum

### 1. Projeyi indirin

```bash
git clone https://github.com/skrkc/hydrology-tool-assistant
cd hydrology-tool-assistant
```

### 2. Gerekli paketleri kurun

```bash
python -m pip install -r requirements.txt
```

### 3. Hugging Face hesabına giriş yapın

Hugging Face Inference erişimine sahip bir Access Token gereklidir.

```bash
hf auth login
```

Token değeri kaynak koduna yazılmamalı ve GitHub deposuna yüklenmemelidir.

### 4. Veritabanını hazırlayın

```bash
python init_database.py
```

Bu komut gerekli tabloları ve örnek başlangıç verilerini oluşturur.

### 5. Uygulamayı çalıştırın

```bash
python app.py
```

Ardından tarayıcıdan:

```text
http://127.0.0.1:7860
```

adresine erişilebilir.

---

## 📦 Gereksinimler

Test edilen temel paket sürümleri:

```text
gradio==5.49.1
huggingface_hub==1.23.0
transformers==5.14.1
spaces==0.51.1
```

Gerekli paketler `requirements.txt` dosyasında bulunmaktadır.

---

## 🧪 Testler

### Test 1 — Custom Chat Template

```bash
python test_chat_template.py
```

> Bu test doğrudan `srhskrkc/odysseia-bpe-tokenizer` reposundaki kayıtlı Chat Template'i kullanır.

### Test 2 — Veritabanından Ölçüm Okuma

```text
Kirazdere'nin son ölçümüne bakalım.
```

Beklenen tool: `get_latest_measurement`

### Test 3 — Çok Turlu Bağlam

İlk turda Kirazdere konuşulduktan sonra:

```text
Onun için 65 m³/s eşikli bir uyarı oluştur.
```

ifadesindeki "onun" önceki konuşma bağlamından Kirazdere olarak yorumlanabilmelidir.

### Test 4 — Gerçek Yazma ve Sonraki Turda Okuma

Önce `create_flow_alert` ile uyarı oluşturulur. Sonraki kullanıcı mesajında:

```text
Kirazdere için oluşturduğum uyarıları göster.
```

`list_flow_alerts` çağrılır ve aynı kayıt SQLite'tan geri okunur.

### Test 5 — Hallüsinasyon Kontrolü

```text
Atlantis istasyonunun en güncel debi ve su seviyesi nedir?
```

Veritabanında böyle bir istasyon bulunmadığından agent herhangi bir hidrolojik değer üretmemelidir.

---

## 🌐 Hugging Face Space

Hugging Face Space bağlantısı:

```text
https://huggingface.co/spaces/srhskrkc/hydrology-tool-assistant
```


---

## 📸 Tool-Call Örneği

Gradio arayüzünde tool çağrıları ve tool sonuçları JSON formatında görüntülenmektedir.

Örnek çok adımlı akış:

```text
Adım 1
get_latest_measurement
        ↓
SQLite
        ↓
61.2 m³/s

Adım 2
create_flow_alert
        ↓
SQLite alerts tablosuna kayıt
```

### Çok Adımlı Tool-Call

![Çok adımlı tool call - Adım 1](screenshots/multi_step_tool_call_1.png)

![Çok adımlı tool call - Adım 2](screenshots/multi_step_tool_call_2.png)

### Ölçüm Okuma Örneği

![Ölçüm okuma tool call](screenshots/measurement_read.png)

---

## 🕸️ Proje Yapısı

```text
hydrology-tool-assistant/
│
├── app.py
├── agent.py
├── database.py
├── init_database.py
├── tools.py
├── tool_schemas.py
│
├── chat_template.jinja
├── test_chat_template.py
├── requirements.txt
├── README.md
│
└── data/
    └── hydrology.db
```

---

## 🔖 Özet

Bu projede:

- Hafta 1'de geliştirilen Odysseia BPE tokenizer'a özel bir Jinja2 Chat Template eklenmiştir.
- Chat Template `system`, `user` ve `assistant` rollerini sade bir metin formatında işler.
- Chat Template testi başka bir tokenizer yerine doğrudan kendi Odysseia tokenizer reposuyla yapılır.
- Gerçek structured tool calling kullanılmaktadır.
- SQLite üzerinden veri okunmaktadır.
- SQLite'a veri yazılmaktadır.
- Birden fazla tool ardışık olarak çağrılabilmektedir.
- Konuşma geçmişi turlar arasında korunmaktadır.
- SQLite'a yazılan uyarı sonraki turda tekrar okunabilmektedir.
- Tool sonuçları tekrar LLM'e gönderilmektedir.
- Veritabanında bulunmayan hidrolojik bilgilerin uydurulması engellenmektedir.
- Gradio tabanlı kullanıcı arayüzü bulunmaktadır.
- Tool-call adımları kullanıcı arayüzünde görüntülenebilmektedir.
