import spaces
import os
os.environ["GRADIO_SSR_MODE"] = "False"

import gradio as gr
import agent
@spaces.GPU(duration=30)
def run_agent_space(user_message):
    yield from agent.run_agent(user_message)

# Ekrandan taşmaları önlemek ve kaydırma çubuğu eklemek için
css_ayari = """
#log-box {
    height: 70vh !important;
    max-height: 600px !important;
    overflow-y: auto !important;
    padding: 15px !important;
    border: 1px solid #444 !important;
    border-radius: 8px !important;
    background-color: #1e1e1e !important;
    font-family: monospace !important;
}
#answer-box {
    font-size: 16px !important;
    padding: 15px !important;
    background-color: #2b2b2b !important;
    border-radius: 8px !important;
    border: 1px solid #555 !important;
}
"""

with gr.Blocks(
    css=css_ayari,
    theme=gr.themes.Soft()
) as demo:
    gr.Markdown("# 🌀 Akarsu Gözlem ve Debi Uyarı Asistanı (Tool-Calling)")
    gr.Markdown("Bu asistan, Kocaeli havzasındaki istasyonların hidrolojik verilerini SQLite veritabanı üzerinden okuyup, debi eşik değeri uyarıları oluşturabilir. Sistem, modelin aracı ne zaman ve nasıl çağırdığını şeffaf bir şekilde günlüğe kaydeder.")
    
    with gr.Row():
        # SOL SÜTUN: Kullanıcı Etkileşimi ve Nihai Cevap
        with gr.Column(scale=1):
            mesaj = gr.Textbox(
                label="Sorunuzu Yazın", 
                placeholder="Örn: Kocaeli'deki istasyonları listele. Ardından Kirazdere'nin debisine bak ve 60 üzerine çıkarsa uyarı oluştur.", 
                lines=3
            )
            gonder = gr.Button("Asistana Sor", variant="primary")
            
            gr.Markdown("### 🤖 Asistanın Nihai Yanıtı")
            cevap_alani = gr.Markdown(elem_id="answer-box")
            
        # SAĞ SÜTUN: Arka Plan İşlemleri (Ödev için istenen ekran görüntüsü alanı)
        with gr.Column(scale=1):
            gr.Markdown("### 🛠️ Tool-Call Günlüğü (JSON Formatında)")
            log_alani = gr.Markdown(elem_id="log-box")
            
    # Butona tıklandığında agent.py içindeki run_agent fonksiyonu çalışır
    # log_alani ve cevap_alani eşzamanlı olarak güncellenir
    gonder.click(
    fn=run_agent_space,
    inputs=mesaj,
    outputs=[log_alani, cevap_alani]
)

if __name__ == "__main__":
    demo.launch()