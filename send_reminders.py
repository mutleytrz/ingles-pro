import database
import email_service
import time
from datetime import datetime

def check_and_send_reminders():
    print(f"[{datetime.now()}] Iniciando verificação de expiração...")
    
    # Lembretes: 7 dias, 3 dias e 1 dia antes
    for days in [7, 3, 1]:
        expiring_users = database.get_expiring_users(days)
        print(f"  Encontrados {len(expiring_users)} usuários expirando em {days} dias.")
        
        for user in expiring_users:
            if user.get("email"):
                print(f"    Enviando lembrete para: {user['username']} ({user['email']})")
                success = email_service.send_renewal_reminder_email(
                    to_email=user["email"],
                    name=user["name"],
                    plan_type=user["plan_type"],
                    expiry_date=user["premium_until"],
                    days_left=days
                )
                if success:
                    print("      OK!")
                else:
                    print("      FALHOU!")
                
                # Pequeno delay para evitar spam/bloqueio SMTP
                time.sleep(1)

    print(f"[{datetime.now()}] Verificação concluída.")

if __name__ == "__main__":
    check_and_send_reminders()
