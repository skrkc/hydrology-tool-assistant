import json
import os

from huggingface_hub import InferenceClient

import tools
import tool_schemas


# Hugging Face üzerinde kullanılacak model.
# İstenilirse daha sonra .env / Space Variables üzerinden değiştirilebilir.
MODEL_ID = os.getenv("MODEL_ID", "openai/gpt-oss-20b")

# Sonsuz tool-call döngüsünü önlemek için üst sınır.
MAX_TOOL_STEPS = 6

# HF_TOKEN ortam değişkeni varsa otomatik olarak kullanılır.
client = InferenceClient(
    api_key=os.getenv("HF_TOKEN")
)


SYSTEM_PROMPT = """
Sen Kocaeli için geliştirilmiş bir Akarsu Gözlem ve Debi Uyarı Asistanısın.

Kurallar:
1. İstasyon listesi, ölçüm bilgileri ve uyarı oluşturma işlemlerinde mutlaka
   sana verilen araçları kullan.
2. Veritabanından veya araç sonucundan gelmeyen hiçbir hidrolojik değeri uydurma.
3. Bir araç found=false veya success=false döndürürse işlemin başarısız olduğunu
   açıkça belirt.
4. Veritabanında bulunmayan bir istasyon hakkında ölçüm veya uyarı bilgisi üretme.
5. Uyarının başarıyla oluşturulduğunu yalnızca create_flow_alert aracı
   success=true döndürürse söyle.
6. Kullanıcı birden fazla işlem isterse gerekli araçları sırayla kullan.
7. Araçlardan dönen sonuçları değiştirme veya yeni sayısal değer ekleme.
8. Nihai yanıtını profesyonel, kısa ve anlaşılır Türkçe ile ver.
""".strip()


def _arguments_to_dict(arguments):
    """
    Modelden gelen function arguments alanını güvenli biçimde Python dict'e çevirir.
    """
    if isinstance(arguments, dict):
        return arguments

    if not arguments:
        return {}

    return json.loads(arguments)


def _tool_call_to_dict(tool_call):
    """
    Hugging Face'in döndürdüğü tool-call nesnesini mesaj geçmişinde
    kullanılabilecek standart sözlük yapısına çevirir.
    """
    arguments = tool_call.function.arguments

    if isinstance(arguments, dict):
        arguments = json.dumps(arguments, ensure_ascii=False)

    return {
        "id": tool_call.id,
        "type": tool_call.type or "function",
        "function": {
            "name": tool_call.function.name,
            "arguments": arguments,
        },
    }


def run_agent(user_message):
    """
    Kullanıcı mesajını LLM'e gönderir.

    Model araç çağırırsa:
        LLM -> Tool Call -> Python -> SQLite -> Tool Response -> LLM

    döngüsünü gerektiği kadar tekrarlar.

    Gradio arayüzü için:
        1. çıktı = Tool-Call günlüğü
        2. çıktı = Kullanıcıya gösterilen nihai cevap
    """

    user_message = (user_message or "").strip()

    if not user_message:
        yield "", "Lütfen önce bir soru veya işlem girin."
        return

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]

    log_text = "## ⚙️ Tool-Call Günlüğü\n\n"

    yield log_text, "İstek analiz ediliyor..."

    try:
        for step in range(1, MAX_TOOL_STEPS + 1):

            response = client.chat_completion(
                model=MODEL_ID,
                messages=messages,
                tools=tool_schemas.TOOLS,
                tool_choice="auto",
                max_tokens=800,
                temperature=0.1,
            )

            assistant = response.choices[0].message
            tool_calls = assistant.tool_calls or []

            # ---------------------------------------------------------
            # Model artık araç çağırmıyorsa işlem tamamlanmıştır.
            # ---------------------------------------------------------
            if not tool_calls:
                final_answer = (
                    assistant.content
                    or "İşlem tamamlandı ancak model metin yanıtı üretmedi."
                )

                log_text += (
                    f"\n✅ **Agent tamamlandı.** "
                    f"Toplam LLM adımı: {step}\n"
                )

                yield log_text, final_answer
                return

            # ---------------------------------------------------------
            # Assistant'ın tool-call kararını konuşma geçmişine
            # yalnızca BİR KEZ ekliyoruz.
            # ---------------------------------------------------------
            assistant_message = {
                "role": "assistant",
                "content": assistant.content or "",
                "tool_calls": [
                    _tool_call_to_dict(tc)
                    for tc in tool_calls
                ],
            }

            messages.append(assistant_message)

            log_text += f"### 🔁 Adım {step}\n\n"

            # Aynı assistant cevabında birden fazla tool-call olabilir.
            for tool_call in tool_calls:

                function_name = tool_call.function.name

                try:
                    function_args = _arguments_to_dict(
                        tool_call.function.arguments
                    )
                except json.JSONDecodeError:
                    function_args = {}

                    tool_result = {
                        "success": False,
                        "message": (
                            "Model araç parametrelerini geçerli JSON "
                            "formatında üretemedi."
                        ),
                    }

                else:
                    # Gerçek Python fonksiyonu burada çalışıyor.
                    tool_result = tools.execute_tool(
                        function_name,
                        function_args,
                    )

                # LLM'in ne çağırdığını log'a yaz.
                log_text += (
                    f"**➡️ Tool Call:** `{function_name}`\n\n"
                    "```json\n"
                    f"{json.dumps(function_args, indent=2, ensure_ascii=False)}\n"
                    "```\n\n"
                )

                yield (
                    log_text,
                    f"`{function_name}` aracı çalıştırılıyor...",
                )

                # Gerçek SQLite/Python sonucunu log'a yaz.
                log_text += (
                    "**⬅️ Tool Response:**\n\n"
                    "```json\n"
                    f"{json.dumps(tool_result, indent=2, ensure_ascii=False)}\n"
                    "```\n\n"
                )

                # Araç sonucunu ilgili tool-call ID'siyle
                # tekrar LLM konuşma geçmişine ekliyoruz.
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps(
                            tool_result,
                            ensure_ascii=False,
                        ),
                    }
                )

                yield (
                    log_text,
                    "Araç sonucu modele geri gönderiliyor...",
                )

            # Döngü burada başa döner.
            # Model tool sonuçlarını görür ve:
            #
            # - başka bir tool çağırabilir
            # - veya nihai kullanıcı cevabını verebilir.

        # Güvenlik sınırı aşılırsa:
        log_text += (
            "\n⚠️ **Agent güvenlik sınırına ulaştı.** "
            f"En fazla {MAX_TOOL_STEPS} araç adımına izin veriliyor.\n"
        )

        yield (
            log_text,
            "İşlem çok fazla araç çağrısı gerektirdiği için güvenlik amacıyla durduruldu.",
        )

    except Exception as exc:
        log_text += (
            "\n### ❌ Sistem Hatası\n\n"
            "```text\n"
            f"{type(exc).__name__}: {exc}\n"
            "```\n"
        )

        yield (
            log_text,
            "Model veya Hugging Face bağlantısında bir hata oluştu.",
        )