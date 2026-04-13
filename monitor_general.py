#!/usr/bin/env python3
"""
Monitor Alkira Living — Todos los edificios en Próximamente
Avisa cuando cualquier edificio cambia de estado.
"""

import requests
import smtplib
import sys
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── Credenciales (vienen de los Secrets de GitHub) ──────────────────
NOTIFY_EMAIL   = os.environ.get("NOTIFY_EMAIL", "")
NOTIFY_EMAIL_2 = os.environ.get("NOTIFY_EMAIL_2", "")
GMAIL_ADDRESS  = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

# ── Edificios a vigilar ─────────────────────────────────────────────
EDIFICIOS = [
    {
        "nombre": "URVA - Francos Rodríguez ⭐",
        "url": "https://alkiraliving.com/promociones/urva-francos-rodriguez",
    },
    {
        "nombre": "URVA - La Alegría",
        "url": "https://alkiraliving.com/promociones/urva-la-alegria",
    },
    {
        "nombre": "URVA - Opanel",
        "url": "https://alkiraliving.com/promociones/urva-opanel",
    },
    {
        "nombre": "URVA - Los Rosales",
        "url": "https://alkiraliving.com/promociones/urva-los-rosales",
    },
    {
        "nombre": "URVA - Planetario",
        "url": "https://alkiraliving.com/promociones/urva-planetario",
    },
    {
        "nombre": "Las Rozas",
        "url": "https://alkiraliving.com/promociones/las-rozas",
    },
    {
        "nombre": "Tectum Barajas",
        "url": "https://alkiraliving.com/promociones/tectum-barajas",
    },
    {
        "nombre": "Meco",
        "url": "https://alkiraliving.com/promociones/meco",
    },
    {
        "nombre": "Tectum Cañaveral I",
        "url": "https://alkiraliving.com/promociones/tectum-canaveral-i",
    },
]

SEÑAL_CERRADO = "PRÓXIMAMENTE"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def revisar_edificio(url):
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return SEÑAL_CERRADO.upper() not in resp.text.upper()


def enviar_email(abiertos):
    if not all([NOTIFY_EMAIL, GMAIL_ADDRESS, GMAIL_PASSWORD]):
        print("⚠️  Faltan credenciales de email.")
        return

    es_francos = any("Francos" in e["nombre"] for e in abiertos)
    asunto = "🚨 PISO FRANCOS ABIERTO 🚨" if es_francos else "🚨 ALKIRA — Nuevo edificio abierto para reservar"

    filas_html = ""
    for e in abiertos:
        es_el_tuyo = "Francos" in e["nombre"]
        bg = "#e74c3c" if es_el_tuyo else "#2c3e50"
        extra = " ⭐ ¡ESTE ES EL TUYO!" if es_el_tuyo else ""
        filas_html += f"""
        <div style="background:{bg};border-radius:8px;padding:16px 20px;margin:10px 0;text-align:center;">
          <p style="color:white;font-size:18px;font-weight:bold;margin:0 0 10px;">
            🏠 {e['nombre']}{extra}
          </p>
          <a href="{e['url']}"
             style="display:inline-block;background:white;color:{bg};
                    padding:10px 24px;text-decoration:none;border-radius:6px;
                    font-size:16px;font-weight:bold;">
            👉 IR A RESERVAR
          </a>
        </div>
        """

    html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:20px;">
      <div style="background:#e74c3c;border-radius:10px 10px 0 0;padding:30px 20px;text-align:center;">
        <div style="font-size:48px;margin-bottom:10px;">🚨🏠🚨</div>
        <h1 style="color:white;margin:0;font-size:26px;">
          {'¡FRANCOS ABIERTO!' if es_francos else '¡NUEVO EDIFICIO ABIERTO!'}
        </h1>
      </div>
      <div style="background:#f8f8f8;border:1px solid #e0e0e0;border-top:none;border-radius:0 0 10px 10px;padding:25px 20px;">
        <p style="font-size:18px;font-weight:bold;color:#222;text-align:center;margin:0 0 20px;">
          ¡Ya están abiertas las reservas! ¡¡¡CORRE!!! 🏃💨
        </p>
        {filas_html}
        <p style="color:#aaa;font-size:12px;text-align:center;margin-top:25px;">
          Alerta generada el {datetime.utcnow().strftime("%d/%m/%Y a las %H:%M UTC")}
        </p>
      </div>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = NOTIFY_EMAIL
    if NOTIFY_EMAIL_2:
        msg["Cc"]  = NOTIFY_EMAIL_2
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
        destinatarios = [NOTIFY_EMAIL] + ([NOTIFY_EMAIL_2] if NOTIFY_EMAIL_2 else [])
        s.sendmail(GMAIL_ADDRESS, destinatarios, msg.as_string())

    print(f"✅ Email enviado a {NOTIFY_EMAIL}")


# ── Main ─────────────────────────────────────────────────────────────

print(f"🔍 Revisando {len(EDIFICIOS)} edificios...")
print(f"🕐 {datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S UTC')}")

abiertos = []

for edificio in EDIFICIOS:
    try:
        if revisar_edificio(edificio["url"]):
            print(f"🚨 ¡ABIERTO! → {edificio['nombre']}")
            abiertos.append(edificio)
        else:
            print(f"😴 Sigue en Próximamente → {edificio['nombre']}")
    except Exception as e:
        print(f"⚠️  Error revisando {edificio['nombre']}: {e}")

if abiertos:
    print(f"\n🚨 {len(abiertos)} edificio(s) han abierto reservas!")
    enviar_email(abiertos)
    sys.exit(1)   # exit 1 = cambio detectado
else:
    print("\n✅ Todos los edificios siguen en Próximamente")
    sys.exit(0)   # exit 0 = sin cambios
