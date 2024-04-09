from telethon.sync import TelegramClient
import json

with open('config.json', 'r') as config_file:
    config = json.load(config_file)
    api_id = config['api_id']
    api_hash = config['api_hash']

client = TelegramClient('session_name', api_id, api_hash)

async def main():
    await client.start()

    username = 'FabioBartoli'
    message = 'teste'

    try:
        await client.send_message(username, message)
        print(f"Mensagem enviada para {username} com sucesso!")
    except Exception as e:
        print(f"Falha ao enviar mensagem para {username}: {str(e)}")

    await client.disconnect()

with client:
    client.loop.run_until_complete(main())
