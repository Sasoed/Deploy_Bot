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

    # Проверяем, предоставлены ли ссылка на репозиторий и имя файла
    if len(context.args) != 2:
        await update.message.reply_text('Используйте команду в формате: /deploy <ссылка на репозиторий> <имя исполняемого файла>')
        return

    github_link = context.args[0]
    exec_file = context.args[1]

    # Определяем имя репозитория для создания пути и имени сервиса
    repo_name = github_link.split('/')[-1]
    if repo_name.endswith('.git'):
        repo_name = repo_name[:-4]

    # Команды для выполнения
    commands = [
        f"git clone {github_link} /home/seva_romanovsky/bot/{repo_name}",  # Путь, куда клонировать репозиторий
        f"echo '[Unit]\\nDescription=Python Application\\nAfter=network.target\\n\\n[Service]\\nType=simple\\nUser=seva_romanovsky\\nWorkingDirectory=/home/seva_romanovsky/bot/{repo_name}\\nExecStart=/home/seva_romanovsky/env/bin/python3 /home/seva_romanovsky/bot/{repo_name}/{exec_file}\\n\\n[Install]\\nWantedBy=multi-user.target' > /home/seva_romanovsky/bot/{repo_name}/{repo_name}.service",
        f"sudo mv /home/seva_romanovsky/bot/{repo_name}/{repo_name}.service /etc/systemd/system/",
        f"sudo systemctl enable {repo_name}",
        f"sudo systemctl start {repo_name}",
        f"sudo systemctl status {repo_name}"
    ]

    try:
        # Переходим в директорию для клонирования проекта
        os.chdir('/home/seva_romanovsky/bot')

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
