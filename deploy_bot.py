from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import subprocess
import os

# Замени 'your_bot_token_here' на токен, который ты получил от BotFather
TOKEN = 'your_bot_token_here'

async def deploy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получаем ссылку на GitHub репозиторий
    if len(context.args) != 1:
        await update.message.reply_text('Пожалуйста, предоставьте ссылку на репозиторий GitHub.')
        return
    
    github_link = context.args[0]
    
    # Команды для выполнения
    commands = [
        f"git clone {github_link}",
        "echo your_service_configuration > your_service.service",
        "sudo mv your_service.service /etc/systemd/system/",
        "sudo systemctl enable your_service",
        "sudo systemctl start your_service",
        "sudo systemctl status your_service"
    ]
    
    try:
        # Активация виртуального окружения
        process = subprocess.Popen("source env/bin/activate", shell=True, executable="/bin/bash")
        process.wait()

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

    deploy_handler = CommandHandler('deploy', deploy, pass_args=True)
    app.add_handler(deploy_handler)

    app.run_polling()

if __name__ == '__main__':
    main()
