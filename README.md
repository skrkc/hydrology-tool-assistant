# 🌊 Akarsu Gözlem ve Debi Uyarı Asistanı

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

> Not: Custom Jinja2 şablonu 1. ödev kapsamında bağımsız olarak test edilmektedir. Tool-calling uygulamasında Hugging Face Inference Provider üzerinden kullanılan modelin kendi sunucu tarafı chat template yapısı kullanılmaktadır.

Test:

```bash
python test_chat_template.py
```

Başarılı test sonucunda mesajlar aşağıdaki yapıya benzer şekilde formatlanmaktadır:

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

## 2. Tool-Calling Assistant

Tool-Calling Assistant, doğal dilde verilen kullanıcı isteklerini analiz ederek gerekli araçları çağırır ve SQLite veritabanı üzerinde gerçek okuma/yazma işlemleri gerçekleştirir.

Kullanılan Model
openai/gpt-oss-20b

Model, Hugging Face Inference Providers üzerinden çağrılmaktadır.

🏗️ Mimari

Genel işlem akışı:

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

Ana bileşenler:

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
🛠️ Araçlar

Projede üç temel tool bulunmaktadır.

list_stations

Aktif akarsu gözlem istasyonlarını listeler.

Tür: Okuma

get_latest_measurement

Belirtilen istasyonun en güncel:

Debi (m³/s)
Su seviyesi (m)
Ölçüm zamanı

bilgilerini SQLite veritabanından getirir.

Tür: Okuma

create_flow_alert

Bir istasyon için yeni debi eşik uyarısı oluşturur.

Veritabanındaki alerts tablosuna gerçek kayıt ekler.

Tür: Yazma

🗄️ SQLite Veritabanı

Proje gerçek bir SQLite veritabanı kullanmaktadır:

data/hydrology.db

Temel tablolar:

stations
measurements
alerts

Örnek istasyonlar:

Kirazdere
Kullar
Yuvacık

Projedeki hidrolojik veriler eğitim ve demonstrasyon amacıyla oluşturulmuş sentetik verilerdir.

🧠 Hallüsinasyon Önleme

Agent'ın veritabanında bulunmayan hidrolojik değerleri üretmemesi için sistem promptunda kısıtlamalar bulunmaktadır.

Örneğin:

Atlantis istasyonunun en güncel debi ve su seviyesi nedir?

isteğinde sistem get_latest_measurement aracını çağırır.

Veritabanı:

{
  "found": false,
  "message": "'Atlantis' adlı aktif istasyon için ölçüm kaydı bulunamadı."
}

sonucunu verdiğinde model herhangi bir debi veya su seviyesi uydurmaz.

🔁 Çok Adımlı Tool Calling Örneği

Örnek kullanıcı isteği:

Kirazdere istasyonunun en güncel debisini kontrol et.
Eğer debi 60 m³/s üzerindeyse 65 m³/s eşik değerli
bir uyarı oluştur.
Uyarı notu: Arayüz testi.

Agent'ın gerçekleştirdiği işlem:

1. get_latest_measurement("Kirazdere")

2. SQLite sonucu:
   flow_m3s = 61.2

3. Model:
   61.2 > 60 koşulunu değerlendirir.

4. create_flow_alert(
       station_name="Kirazdere",
       threshold_m3s=65,
       note="Arayüz testi"
   )

5. SQLite alerts tablosuna yeni kayıt eklenir.

6. Tool sonucu modele geri gönderilir.

7. Model nihai kullanıcı yanıtını üretir.
💻 Yerel Kurulum
1. Projeyi indirin
git clone <GITHUB_REPO_URL>
cd hydrology-tool-assistant
2. Gerekli paketleri kurun
python -m pip install -r requirements.txt
3. Hugging Face hesabına giriş yapın
hf auth login

Inference yetkisine sahip bir Hugging Face Access Token kullanılmalıdır.

4. Veritabanını hazırlayın
python init_database.py
5. Uygulamayı çalıştırın
python app.py

Ardından tarayıcıdan:

http://127.0.0.1:7860

adresine erişilebilir.

📦 Gereksinimler

Test edilen temel paket sürümleri:

gradio==6.22.0
huggingface_hub==1.23.0
transformers==5.14.1
🧪 Testler

Custom Chat Template:

python test_chat_template.py

Tool-calling sistemi, aşağıdaki senaryolarla test edilmiştir:

İstasyon ölçümü okuma
Çok adımlı ölçüm kontrolü ve uyarı oluşturma
SQLite'a gerçek kayıt yazma
Veritabanında olmayan istasyon için hallüsinasyon engelleme
🌐 Hugging Face Space

Uygulamanın çalışan Hugging Face Space bağlantısı:

SPACE_LINK_BURAYA_GELECEK
📸 Tool-Call Örneği

Gradio arayüzünde tool çağrıları ve tool sonuçları JSON formatında görüntülenmektedir.

Örnek işlem:

get_latest_measurement
        ↓
SQLite
        ↓
61.2 m³/s
        ↓
create_flow_alert
        ↓
SQLite alerts tablosuna kayıt

Tool-call ekran görüntüsü Hugging Face Space / GitHub deposunda sunulacaktır.

📁 Proje Yapısı
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
📌 Özet

Bu projede:

Özel bir Jinja2 Chat Template oluşturulmuştur.
Gerçek structured tool calling kullanılmaktadır.
SQLite üzerinden veri okunmaktadır.
SQLite'a veri yazılmaktadır.
Birden fazla tool ardışık olarak çağrılabilmektedir.
Tool sonuçları tekrar LLM'e gönderilmektedir.
Veritabanında bulunmayan hidrolojik bilgilerin uydurulması engellenmektedir.
Gradio tabanlı kullanıcı arayüzü bulunmaktadır.

