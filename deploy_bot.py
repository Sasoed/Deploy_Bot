import json
import os
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

def check_or_create_api_txt():
    if not os.path.exists("api.txt"):
        with open("api.txt", "w") as file:
            file.write("YOUR_API_KEY")
        print("api.txt created.")

def read_token():
    with open('api.txt', 'r') as file:
        return file.read().strip()

def read_allowed_users():
    try:
        with open('allowed_users.json', 'r') as file:
            data = json.load(file)
            return set(data['allowed_users'])
    except FileNotFoundError:
        return set()

def read_project_paths():
    try:
        with open('project_paths.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_project_path(repo_name, path):
    paths = read_project_paths()
    paths[repo_name] = path
    with open('project_paths.json', 'w') as file:
        json.dump(paths, file)

TOKEN = read_token()
ALLOWED_USER_IDS = read_allowed_users()

async def deploy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USER_IDS:
        await update.message.reply_text("У вас нет доступа к этой команде.")
        return

    if len(context.args) != 2:
        await update.message.reply_text('Используйте команду в формате: /deploy <ссылка на репозиторий> <имя исполняемого файла>')
        return

    github_link, exec_file = context.args
    repo_name = github_link.split('/')[-1].replace('.git', '')
    project_path = f'/home/seva_romanovsky/bot/{repo_name}'

    save_project_path(repo_name, project_path)

    commands = [
        f"git clone {github_link} {project_path}",
        f"echo '[Unit]\\nDescription=Python Application\\nAfter=network.target\\n\\n[Service]\\nType=simple\\nUser=seva_romanovsky\\nWorkingDirectory={project_path}\\nExecStart=/home/seva_romanovsky/env/bin/python3 {project_path}/{exec_file}\\n\\n[Install]\\nWantedBy=multi-user.target' > {project_path}/{repo_name}.service",
        f"sudo mv {project_path}/{repo_name}.service /etc/systemd/system/",
        f"sudo systemctl enable {repo_name}",
        f"sudo systemctl start {repo_name}"
    ]

    for cmd in commands:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            await update.message.reply_text(f'Ошибка при выполнении команды {cmd}: {stderr.decode()}')
            return
        await update.message.reply_text(f'Результат выполнения {cmd}: {stdout.decode()}')

    await update.message.reply_text('Деплой завершен.')

async def update_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    repo_name = query.data.split('_')[1]
    project_paths = read_project_paths()
    project_path = project_paths.get(repo_name)

    if not project_path:
        await query.edit_message_text('Путь проекта не найден.')
        return

    commands = [
        f"cd {project_path} && git pull",
        f"sudo systemctl restart {repo_name}"
    ]

    for cmd in commands:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            await query.edit_message_text(f'Ошибка при выполнении команды {cmd}: {stderr.decode()}')
            return

        await query.edit_message_text(f'Результат выполнения {cmd}: {stdout.decode()}')

    await query.edit_message_text('Проект обновлен и перезапущен.')

def main():
    check_or_create_api_txt()
    app = Application.builder().token(TOKEN).build()

    deploy_handler = CommandHandler('deploy', deploy)
    update_handler = CallbackQueryHandler(update_project, pattern='^update_')

    app.add_handler(deploy_handler)
    app.add_handler(update_handler)

    app.run_polling()

if __name__ == '__main__':
    main()
