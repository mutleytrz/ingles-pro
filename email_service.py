import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import config


def _get_smtp_runtime():
    """Busca SMTP config em tempo real (st.secrets > config)."""
    smtp = {"host": "", "user": "", "password": "", "port": 587, "from_name": "English Pro AI"}
    try:
        import streamlit as st
        smtp["host"] = st.secrets.get("SMTP_HOST", "") or ""
        smtp["user"] = st.secrets.get("SMTP_USER", "") or ""
        smtp["password"] = st.secrets.get("SMTP_PASS", "") or ""
        smtp["port"] = int(st.secrets.get("SMTP_PORT", 587))
        smtp["from_name"] = st.secrets.get("SMTP_FROM_NAME", "English Pro AI") or "English Pro AI"
    except Exception:
        pass
    if not smtp["host"]:
        smtp["host"] = config.SMTP_HOST
    if not smtp["user"]:
        smtp["user"] = config.SMTP_USER
    if not smtp["password"]:
        smtp["password"] = config.SMTP_PASS
    if not smtp["from_name"]:
        smtp["from_name"] = config.SMTP_FROM_NAME
    return smtp


def send_verification_email(to_email: str, code: str) -> bool:
    """Envia email com codigo de verificacao."""
    smtp = _get_smtp_runtime()
    
    if not smtp["host"] or not smtp["user"]:
        print(f"\n[DEV-MODE] SMTP nao configurado. CODIGO DE VERIFICACAO: {code}\n")
        return True  # Retorna True para permitir testar o fluxo UI

    sender_email = smtp["user"]
    password = smtp["password"]

    message = MIMEMultipart("alternative")
    from email.utils import formataddr
    message["Subject"] = f"Seu código de verificação: {code}"
    # Garante que o nome do remetente seja respeitado (RFC 5322)
    display_name = smtp['from_name'].strip()
    if not display_name or display_name.lower() == "eu":
        display_name = "English Pro AI"
    message["From"] = formataddr((display_name, sender_email))
    message["To"] = to_email

    # Versao texto simples
    text = f"""
    Olá!
    
    Seu código de verificação para o English Pro é: {code}
    
    Se você não solicitou este código, ignore este email.
    """

    # Versao HTML (Styled)
    html = f"""
    <html>
      <body style="font-family: 'Helvetica', 'Arial', sans-serif; background-color: #f4f4f9; margin: 0; padding: 0;">
        <div style="max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
          <div style="background: linear-gradient(135deg, #8b5cf6, #06b6d4); padding: 30px; text-align: center;">
             <h1 style="color: white; margin: 0; font-size: 24px;">🚀 English Pro</h1>
          </div>
          <div style="padding: 40px; text-align: center; color: #334155;">
             <h2 style="margin-top: 0; color: #1e293b;">Confirme seu Email</h2>
             <p style="font-size: 16px; line-height: 1.6;">Estamos quase lá! Use o código abaixo para ativar sua conta:</p>
             
             <div style="background: #f1f5f9; padding: 20px; border-radius: 8px; font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #475569; margin: 30px 0; border: 2px dashed #cbd5e1;">
                {code}
             </div>
             
             <p style="font-size: 14px; color: #94a3b8;">Se você não criou uma conta no English Pro, pode ignorar este email.</p>
          </div>
          <div style="background: #e2e8f0; padding: 20px; text-align: center; font-size: 12px; color: #64748b;">
             &copy; 2026 English Pro AI Learning
          </div>
        </div>
      </body>
    </html>
    """

    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    message.attach(part1)
    message.attach(part2)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp["host"], smtp["port"]) as server:
            server.starttls(context=context)
            server.login(sender_email, password)
            server.sendmail(sender_email, to_email, message.as_string())
        print(f"[INFO] Email enviado para {to_email}")
        return True
    except Exception as e:
        print(f"[ERR] Falha ao enviar email: {e}")
        return False
