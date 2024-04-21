import json
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import subprocess
import os

def read_token():
    # Чтение токена из файла
    with open('/home/seva_romanovsky/bot/Deploy_Bot/API.txt', 'r') as file:
        token = file.read().strip()
    return token

def read_allowed_users():
    # Чтение списка разрешенных пользователей из JSON файла
    with open('/home/seva_romanovsky/bot/Deploy_Bot/allowed_users.json', 'r') as file:
        data = json.load(file)
    return set(data['allowed_users'])

TOKEN = read_token()
ALLOWED_USER_IDS = read_allowed_users()

async def deploy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USER_IDS:
        await update.message.reply_text("У вас нет доступа к этой команде.")
        return

    # Получаем ссылку на GitHub репозиторий
    if len(context.args) != 1:
        await update.message.reply_text('Пожалуйста, предоставьте ссылку на репозиторий GitHub.')
        return
    
    github_link = context.args[0]

    # Команды для выполнения
    commands = [
        f"git clone {github_link}",
        "echo '[Unit]\\nDescription=My Python App\\nAfter=network.target\\n\\n[Service]\\nType=simple\\nUser=seva_romanovsky\\nWorkingDirectory=/home/seva_romanovsky/bot/Deploy_Bot\\nExecStart=/home/seva_romanovsky/env/bin/python3 /home/seva_romanovsky/bot/Deploy_Bot/deploy_bot.py\\n\\n[Install]\\nWantedBy=multi-user.target' > your_service.service",
        "sudo mv your_service.service /etc/systemd/system/",
        "sudo systemctl enable your_service",
        "sudo systemctl start your_service",
        "sudo systemctl status your_service"
    ]

    try:
        # Переходим в директорию для клонирования проекта
        os.chdir('./bot')

        # Выполняем команды
        for cmd in commands:
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                # В случае ошибки отправляем сообщение об ошибке
                await update.message.reply_text(f'Ошибка при выполнении команды {cmd}: {stderr.decode()}')
                return
            
            # Отправляем результаты выполнения
            await update.message.reply_text(f'Результат выполнения {cmd}: {stdout.decode()}')

    except Exception as e:
        await update.message.reply_text(f'Произошла ошибка: {str(e)}')

    await update.message.reply_text('Деплой завершен.')


def main():
    app = Application.builder().token(TOKEN).build()

    deploy_handler = CommandHandler('deploy', deploy)
    app.add_handler(deploy_handler)

    app.run_polling()

if __name__ == '__main__':
    main()
