#!/usr/bin/env python3
"""
Monitor Alkira Living — Francos Rodríguez
Comprueba si la página ha pasado de "Próximamente" a disponible.
Diseñado para correr en GitHub Actions.
"""

import requests
import smtplib
import sys
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── Configuración (en GitHub Actions viene de los Secrets) ──────────
URL            = "https://alkiraliving.com/promociones/urva-francos-rodriguez"
NOTIFY_EMAIL   = os.environ.get("NOTIFY_EMAIL", "")
GMAIL_ADDRESS  = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
NTFY_TOPIC     = os.environ.get("NTFY_TOPIC", "")

# Texto que aparece cuando el piso está CERRADO
SEÑAL_CERRADO = "PRÓXIMAMENTE"


def revisar_pagina():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    resp = requests.get(URL, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text


def enviar_email():
    if not all([NOTIFY_EMAIL, GMAIL_ADDRESS, GMAIL_PASSWORD]):
        print("⚠️  Faltan credenciales de email. Revisa los Secrets de GitHub.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🚨 ¡CORRE! Francos Rodríguez YA ESTÁ ABIERTO para reservar"
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = NOTIFY_EMAIL

    html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:20px;">
      <div style="background:#e74c3c;color:white;padding:25px;border-radius:8px 8px 0 0;text-align:center;">
        <h1 style="margin:0;font-size:32px;">🚨 ¡ALERTA!</h1>
        <p style="font-size:20px;margin:10px 0 0 0;">Francos Rodríguez está abierto para reservar</p>
      </div>
      <div style="background:#f9f9f9;padding:25px;border:1px solid #ddd;border-radius:0 0 8px 8px;">
        <p style="font-size:16px;">
          La página ha dejado de mostrar <strong>"Próximamente"</strong>.
          ¡Es el momento de entrar y reservar!
        </p>
        <div style="text-align:center;margin:25px 0;">
          <a href="{URL}"
             style="background:#27ae60;color:white;padding:16px 32px;
                    text-decoration:none;border-radius:6px;font-size:20px;
                    font-weight:bold;">
            👉 IR A RESERVAR AHORA
          </a>
        </div>
        <p style="color:#999;font-size:12px;text-align:center;margin-top:20px;">
          Alerta generada el {datetime.utcnow().strftime("%d/%m/%Y a las %H:%M UTC")}<br>
          URL vigilada: {URL}
        </p>
      </div>
    </body></html>
    """

    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
        s.sendmail(GMAIL_ADDRESS, NOTIFY_EMAIL, msg.as_string())

    print(f"✅ Email enviado a {NOTIFY_EMAIL}")


def enviar_ntfy():
    if not NTFY_TOPIC:
        return
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data="🚨 ¡CORRE! Francos Rodríguez YA ESTÁ ABIERTO. Entra a alkiraliving.com a reservar AHORA".encode("utf-8"),
        headers={
            "Title":    "🏠 ¡ALERTA PISO!",
            "Priority": "urgent",
            "Tags":     "rotating_light,house",
            "Click":    URL,
        },
        timeout=10,
    )
    print(f"📱 Notificación push enviada (ntfy.sh/{NTFY_TOPIC})")


# ────────────────────────────────────────────────────────────────────

print(f"🔍 Comprobando: {URL}")
print(f"🕐 {datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S UTC')}")

try:
    contenido = revisar_pagina()
except Exception as e:
    print(f"❌ Error al acceder a la página: {e}")
    sys.exit(2)

if SEÑAL_CERRADO.upper() in contenido.upper():
    print("😴 Sin cambios — la página sigue mostrando 'Próximamente'")
    sys.exit(0)
else:
    print("🚨 ¡¡CAMBIO DETECTADO!! La página ya NO muestra 'Próximamente'")
    enviar_email()
    enviar_ntfy()
    sys.exit(1)   # exit 1 → el workflow sabe que hay que marcar la alerta
