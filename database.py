import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "hydrology.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def list_stations(province=None):
    """Aktif gözlem istasyonlarını listeler."""
    with get_connection() as conn:
        cursor = conn.cursor()

        if province:
            cursor.execute(
                """
                SELECT name, river, province
                FROM stations
                WHERE province = ? COLLATE NOCASE
                  AND active = 1
                ORDER BY name
                """,
                (province.strip(),),
            )
        else:
            cursor.execute(
                """
                SELECT name, river, province
                FROM stations
                WHERE active = 1
                ORDER BY name
                """
            )

        results = cursor.fetchall()

    if not results:
        return {
            "found": False,
            "message": "Aktif istasyon bulunamadı.",
        }

    return {
        "found": True,
        "stations": [
            {
                "name": row[0],
                "river": row[1],
                "province": row[2],
            }
            for row in results
        ],
    }


def get_latest_measurement(station_name):
    """Seçilen aktif istasyonun en güncel ölçümünü getirir."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                s.name,
                m.flow_m3s,
                m.water_level_m,
                m.measured_at
            FROM stations AS s
            JOIN measurements AS m
                ON s.id = m.station_id
            WHERE s.name = ? COLLATE NOCASE
              AND s.active = 1
            ORDER BY m.measured_at DESC
            LIMIT 1
            """,
            (station_name.strip(),),
        )

        result = cursor.fetchone()

    if not result:
        return {
            "found": False,
            "message": (
                f"'{station_name}' adlı aktif istasyon için "
                "ölçüm kaydı bulunamadı."
            ),
        }

    return {
        "found": True,
        "station": result[0],
        "flow_m3s": result[1],
        "water_level_m": result[2],
        "measured_at": result[3],
    }


def create_flow_alert(station_name, threshold_m3s, note=""):
    """Aktif bir istasyon için debi eşik uyarısı oluşturur."""

    try:
        threshold_m3s = float(threshold_m3s)
    except (TypeError, ValueError):
        return {
            "success": False,
            "message": "Debi eşik değeri sayısal olmalıdır.",
        }

    if threshold_m3s <= 0:
        return {
            "success": False,
            "message": "Debi eşik değeri sıfırdan büyük olmalıdır.",
        }

    with get_connection() as conn:
        cursor = conn.cursor()

        # Halüsinasyon / geçersiz veri koruması:
        # Modelin verdiği istasyon gerçekten veritabanında var mı?
        cursor.execute(
            """
            SELECT id, name
            FROM stations
            WHERE name = ? COLLATE NOCASE
              AND active = 1
            """,
            (station_name.strip(),),
        )

        station = cursor.fetchone()

        if not station:
            return {
                "success": False,
                "message": (
                    f"'{station_name}' adında aktif bir istasyon "
                    "veritabanında mevcut değil."
                ),
            }

        station_id, canonical_name = station

        cursor.execute(
            """
            INSERT INTO alerts (
                station_id,
                threshold_m3s,
                note
            )
            VALUES (?, ?, ?)
            """,
            (
                station_id,
                threshold_m3s,
                note.strip() if note else "",
            ),
        )

        alert_id = cursor.lastrowid

    return {
        "success": True,
        "alert_id": alert_id,
        "station": canonical_name,
        "threshold_m3s": threshold_m3s,
        "message": (
            f"{canonical_name} istasyonu için "
            f"{threshold_m3s:g} m³/s eşik değerli uyarı "
            "başarıyla oluşturuldu."
        ),
    }