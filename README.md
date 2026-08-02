---
title: Hydrology Tool Assistant
emoji: 🌀
colorFrom: gray
colorTo: blue
sdk: gradio
sdk_version: 5.49.1
python_version: '3.12.12'
app_file: app.py
pinned: false
---

# 🌀 Akarsu Gözlem ve Debi Uyarı Asistanı

Bu proje, yapay zekâ dersi kapsamında hazırlanan iki ödevi tek bir depo altında sunmaktadır:

1. **Custom Chat Template (Jinja2)**
2. **Tool-Calling Assistant**

Projenin senaryosu, Kocaeli bölgesindeki sentetik akarsu gözlem istasyonları üzerinden hidrolojik ölçümlerin sorgulanması ve debi eşik uyarılarının oluşturulmasıdır.

---

## 1. Custom Chat Template (Jinja2)

`chat_template.jinja` dosyasında özel bir sohbet şablonu oluşturulmuştur.

Şablon aşağıdaki mesaj türlerini desteklemektedir:

- `system`
- `user`
- `assistant`
- `tool`

Ayrıca:

- Tool tanımları
- Tool call mesajları
- Tool response mesajları
- JSON serileştirme
- `add_generation_prompt`

desteklenmektedir.

Chat template, `test_chat_template.py` dosyası ile `Qwen/Qwen2.5-7B-Instruct` tokenizer'ı üzerinde test edilmiştir.

> **Not:** Custom Jinja2 şablonu 1. ödev kapsamında bağımsız olarak test edilmektedir. Tool-calling uygulamasında Hugging Face Inference Providers üzerinden kullanılan modelin kendi sunucu tarafı chat template yapısı kullanılmaktadır.

### Chat Template Testi

```bash
python test_chat_template.py
```

Başarılı test sonucunda mesajlar aşağıdaki yapıya benzer şekilde formatlanmaktadır:

```text
<|im_start|>system
...
<tools>
...
</tools>
<|im_end|>

<|im_start|>user
...
<|im_end|>

<|im_start|>assistant
<tool_call>
...
</tool_call>
<|im_end|>

<|im_start|>tool
<tool_response>
...
</tool_response>
<|im_end|>

<|im_start|>assistant
```

---

## 2. Tool-Calling Assistant

Tool-Calling Assistant, doğal dilde verilen kullanıcı isteklerini analiz ederek gerekli araçları çağırır ve SQLite veritabanı üzerinde gerçek okuma/yazma işlemleri gerçekleştirir.

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
Kullanıcı
   ↓
Gradio Arayüzü
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
Nihai Yanıt
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

Projede üç temel tool bulunmaktadır.

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

## 🔁 Çok Adımlı Tool Calling Örneği

Örnek kullanıcı isteği:

```text
Kirazdere istasyonunun en güncel debisini kontrol et.
Eğer debi 60 m³/s üzerindeyse 65 m³/s eşik değerli bir uyarı oluştur.
Uyarı notu: Arayüz testi.
```

Agent'ın gerçekleştirdiği işlem:

```text
1. get_latest_measurement("Kirazdere")

2. SQLite sonucu:
   flow_m3s = 61.2

3. Model:
   61.2 > 60 koşulunu değerlendirir.

4. Koşul sağlandığı için:

   create_flow_alert(
       station_name="Kirazdere",
       threshold_m3s=65,
       note="Arayüz testi"
   )

   çağrılır.

5. SQLite alerts tablosuna yeni kayıt eklenir.

6. Tool sonucu modele geri gönderilir.

7. Model nihai kullanıcı yanıtını üretir.
```

Bu yapı sayesinde agent, bir tool sonucunu kullanarak yeni bir karar verebilmekte ve ikinci bir tool çağrısı gerçekleştirebilmektedir.

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
```

Gerekli paketler `requirements.txt` dosyasında bulunmaktadır.

---

## 🧪 Testler

### Test 1 — Custom Chat Template

```bash
python test_chat_template.py
```

Bu test ile özel Jinja2 şablonunun tokenizer tarafından doğru şekilde işlendiği kontrol edilmektedir.

### Test 2 — Veritabanından Ölçüm Okuma

Kullanıcı:

```text
Kirazdere istasyonunun en güncel debi ve su seviyesi nedir?
```

Agent:

```text
get_latest_measurement
```

tool'unu çağırır.

SQLite sonucu:

```json
{
  "found": true,
  "station": "Kirazdere",
  "flow_m3s": 61.2,
  "water_level_m": 2.25,
  "measured_at": "2026-08-01 02:00"
}
```

### Test 3 — Çok Adımlı Okuma ve Yazma

Kullanıcı:

```text
Kirazdere istasyonunun en güncel debisini kontrol et.
Eğer debi 60 m³/s üzerindeyse 65 m³/s eşik değerli bir uyarı oluştur.
```

Agent sırasıyla:

```text
get_latest_measurement
```

ve:

```text
create_flow_alert
```

araçlarını çağırır.

Yeni uyarı SQLite veritabanına gerçek kayıt olarak eklenir.

### Test 4 — Hallüsinasyon Kontrolü

Kullanıcı:

```text
Atlantis istasyonunun en güncel debi ve su seviyesi nedir?
```

Veritabanında böyle bir istasyon bulunmadığından agent herhangi bir hidrolojik değer üretmez.

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

Tool-call terminal veya arayüz ekran görüntüsü teslim için depo içerisine ayrıca eklenecektir.

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

- Özel bir Jinja2 Chat Template oluşturulmuştur.
- `system`, `user`, `assistant` ve `tool` rolleri desteklenmektedir.
- Tool tanımları ve tool-call yapıları Chat Template içerisinde işlenmektedir.
- Gerçek structured tool calling kullanılmaktadır.
- SQLite üzerinden veri okunmaktadır.
- SQLite'a veri yazılmaktadır.
- Birden fazla tool ardışık olarak çağrılabilmektedir.
- Tool sonuçları tekrar LLM'e gönderilmektedir.
- Veritabanında bulunmayan hidrolojik bilgilerin uydurulması engellenmektedir.
- Gradio tabanlı kullanıcı arayüzü bulunmaktadır.
- Tool-call adımları kullanıcı arayüzünde görüntülenebilmektedir.