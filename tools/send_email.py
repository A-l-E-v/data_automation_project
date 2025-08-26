# python3 /home/al/data_automation_project/tools/send_email.py
import smtplib
from email.message import EmailMessage

msg = EmailMessage()
msg["From"] = "tester@example.com"
msg["To"] = "you@example.com"
msg["Subject"] = "SMTP TEST"
msg.set_content("Это тестовое сообщение. Если debug SMTP работает, вы увидите это в его терминале.")

try:
    s = smtplib.SMTP("127.0.0.1", 1025, timeout=10)
    s.send_message(msg)
    s.quit()
    print("Сообщение отправлено локальному debug SMTP (127.0.0.1:1025)")
except Exception as e:
    print("Ошибка при отправке тестового письма:", e)