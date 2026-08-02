import database

def execute_tool(func_name, kwargs):
    """
    Yapay zekadan (LLM) gelen JSON araç çağrısını (Tool Call) alır, 
    ilgili veritabanı fonksiyonuna yönlendirir ve sonucu döndürür.
    """
    if func_name == "list_stations":
        return database.list_stations(**kwargs)
        
    elif func_name == "get_latest_measurement":
        return database.get_latest_measurement(**kwargs)
        
    elif func_name == "create_flow_alert":
        return database.create_flow_alert(**kwargs)
        
    else:
        return {"success": False, "message": f"Bilinmeyen araç çağrısı: {func_name}"}