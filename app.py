import json
from flask import Flask, render_template, request, send_from_directory
from telethon.sync import TelegramClient
from flask_socketio import SocketIO, emit
import asyncio
import redis


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

# Carregar as credenciais do arquivo config.json
with open('config.json', 'r') as config_file:
    config = json.load(config_file)
    api_id = config['api_id']
    api_hash = config['api_hash']

# Função para iniciar o cliente Telegram
async def start_telegram_client():
    global client
    client = TelegramClient('session_name', api_id, api_hash)
    await client.start()

# Rota inicial
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('images', filename)

# Função para desconectar o cliente Telegram
async def disconnect_telegram_client():
    await client.disconnect()

@app.route('/add_users', methods=['POST'])
def add_users():
    users = request.json.get('users')
    if users:
        try:
            for user in users:
                redis_client.sadd('users', user)
            return 'Usuários adicionados com sucesso!', 200
        except Exception as e:
            return f'Erro ao adicionar usuários: {str(e)}', 500
    else:
        return 'Nenhum usuário fornecido', 400

# Rota para obter a lista de usuários cadastrados no Redis
@app.route('/get_users', methods=['GET'])
def get_users():
    users = redis_client.smembers('users')
    users_html = '<ul>'
    for user in users:
        users_html += f'<li><input type="checkbox" class="user-checkbox" value="{user.decode()}"> {user.decode()}</li>'
    users_html += '</ul>'
    return users_html

# Rota para excluir os usuários selecionados no Redis
@app.route('/delete_users', methods=['POST'])
def delete_users():
    users = request.json.get('users')
    if users:
        redis_client.srem('users', *users)
        return 'Usuários excluídos com sucesso!', 200
    else:
        return 'Nenhum usuário fornecido', 400
        
# Rota para enviar mensagem
@socketio.on('send_message')
def send_message(data):
    message = data['message']

    # Obtém todos os usuários cadastrados no Redis
    users = redis_client.smembers('users')

    # Inicia a sessão do cliente Telegram
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_telegram_client())

    # Função para enviar a mensagem para um usuário
    async def send_to_user(username):
        try:
            print(f"Enviando mensagem para {username.decode()}...")
            await client.send_message(username.decode(), message)
            print(f"Mensagem enviada para {username.decode()} com sucesso!")
            emit('status', f"Mensagem enviada para {username.decode()} com sucesso!")
        except Exception as e:
            print(f"Falha ao enviar mensagem para {username.decode()}: {str(e)}")
            emit('status', f"Falha ao enviar mensagem para {username.decode()}: {str(e)}")

    # Lista para armazenar tarefas de envio de mensagem
    tasks = []

    # Itera sobre cada username e adiciona a tarefa à lista
    for username in users:
        tasks.append(send_to_user(username))

    # Aguarda o envio de todas as mensagens
    loop.run_until_complete(asyncio.gather(*tasks))

    # Desconecta o cliente Telegram
    print("Desconectando o cliente Telegram...")
    loop.run_until_complete(disconnect_telegram_client())

    # Encerra a sessão do cliente
    print("Encerrando a sessão do cliente...")
    loop.close()
    print("Sessão encerrada!")

    return 'Mensagem enviada com sucesso!'


if __name__ == '__main__':
    socketio.run(app, debug=True)
