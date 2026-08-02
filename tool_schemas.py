# LLM'in hangi araçlara sahip olduğunu anlatan JSON şemaları
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_stations",
            "description": "Kocaeli ilindeki veya havzadaki akarsu gözlem istasyonlarını listeler. (Okuma Aracı)",
            "parameters": {
                "type": "object",
                "properties": {
                    "province": {
                        "type": "string",
                        "description": "Filtrelemek istenen il adı (örn: Kocaeli). Boş bırakılabilir."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_latest_measurement",
            "description": "Seçilen bir istasyonun en son debi (m3/s) ve su seviyesi (m) ölçümlerini getirir. (Okuma Aracı)",
            "parameters": {
                "type": "object",
                "properties": {
                    "station_name": {
                        "type": "string",
                        "description": "Ölçümü getirilecek istasyonun tam adı (örn: Kirazdere)."
                    }
                },
                "required": ["station_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_flow_alert",
            "description": "Belirli bir istasyon için debi eşik değeri uyarısı (alarm) oluşturur. (Yazma Aracı)",
            "parameters": {
                "type": "object",
                "properties": {
                    "station_name": {
                        "type": "string",
                        "description": "Uyarının oluşturulacağı istasyonun adı."
                    },
                    "threshold_m3s": {
                        "type": "number",
                        "description": "Uyarı tetiklenecek debi eşik değeri (m3/s)."
                    },
                    "note": {
                        "type": "string",
                        "description": "Uyarı için eklenecek not veya açıklama."
                    }
                },
                "required": ["station_name", "threshold_m3s", "note"]
            }
        }
    }
]