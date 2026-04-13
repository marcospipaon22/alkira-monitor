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
NOTIFY_EMAIL_2 = os.environ.get("NOTIFY_EMAIL_2", "")
GMAIL_ADDRESS  = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
NTFY_TOPIC     = os.environ.get("NTFY_TOPIC", "")

# Texto que aparece cuando el piso está CERRADO
SEÑAL_CERRADO = "XYZXYZXYZ"


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
    msg["Subject"] = "🚨 PISO FRANCOS ABIERTO 🚨"
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = NOTIFY_EMAIL
    if NOTIFY_EMAIL_2:
        msg["Cc"]  = NOTIFY_EMAIL_2

    html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:20px;background:#ffffff;">

      <!-- Cabecera -->
      <div style="background:#e74c3c;border-radius:10px 10px 0 0;padding:30px 20px;text-align:center;">
        <div style="font-size:48px;margin-bottom:10px;">🚨🏠🚨</div>
        <h1 style="color:white;margin:0;font-size:28px;letter-spacing:1px;">PISO FRANCOS ABIERTO</h1>
      </div>

      <!-- Cuerpo -->
      <div style="background:#f8f8f8;border:1px solid #e0e0e0;border-top:none;border-radius:0 0 10px 10px;padding:35px 30px;text-align:center;">

        <p style="font-size:22px;font-weight:bold;color:#222;margin:0 0 10px;">
          ¡Ya están abiertas las reservas de los pisos de Francos Rodríguez!
        </p>

        <p style="font-size:28px;margin:10px 0 30px;">
          ¡¡¡CORRE!!!  🏃💨
        </p>

        <a href="{URL}"
           style="display:inline-block;background:#e74c3c;color:white;
                  padding:18px 40px;text-decoration:none;border-radius:8px;
                  font-size:20px;font-weight:bold;letter-spacing:0.5px;">
          🏠 IR A RESERVAR AHORA
        </a>

        <p style="color:#aaa;font-size:12px;margin-top:30px;">
          Alerta generada el {datetime.utcnow().strftime("%d/%m/%Y a las %H:%M UTC")}
        </p>

      </div>

    </body></html>
    """

    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
        destinatarios = [NOTIFY_EMAIL] + ([NOTIFY_EMAIL_2] if NOTIFY_EMAIL_2 else [])
        s.sendmail(GMAIL_ADDRESS, destinatarios, msg.as_string())

    print(f"✅ Email enviado a {NOTIFY_EMAIL}" + (f" y {NOTIFY_EMAIL_2}" if NOTIFY_EMAIL_2 else ""))


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
