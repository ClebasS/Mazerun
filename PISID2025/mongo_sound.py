import subprocess

import paho.mqtt.client as mqtt
import pymongo
import json
import time

# Configuração do MongoDB
MONGO_URI = "mongodb://localhost:27019/mqtt_db?replicaSet=PISID25"
client_mongo = pymongo.MongoClient(MONGO_URI)
db = client_mongo["mqtt_db"]

# Configuração do MQTT
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
TOPICO_SOUND = "sound"  # Tópico para enviar dados de ruído


# Função para buscar e remover dados do MongoDB
def buscar_e_remover_dados_mongo(collection_name):
    collection = db[collection_name]
    dados = list(collection.find())  # Buscar todos os dados disponíveis

    return dados


# Função para enviar dados para o broker MQTT com QoS 2
def enviar_para_mqtt(dados):
    if not dados:
        return  # Se não há dados, não faz nada

    for dado in dados:
        dado.pop("_id", None)  # Remover o '_id' do MongoDB

        if "Hour" in dado:
            dado["Hour"] = dado["Hour"].replace(" ", "_")

        # Converter para JSON
        mensagem_json = json.dumps(dado)  # Converter para JSON

        # Executar o comando mosquitto_pub
        comando = f'mosquitto_pub -h {MQTT_BROKER} -t {TOPICO_SOUND} -q 2 -m "{mensagem_json}"'
        subprocess.run(comando, shell=True)

        print(f"✅ Mensagem enviada para '{TOPICO_SOUND}' (QoS 2): {mensagem_json}")


# Loop principal
if __name__ == "__main__":
    print(f"mongo_sound iniciou")
    player_id = 50  # Substitua com o ID do jogador
    while True:
        dados_sound = buscar_e_remover_dados_mongo(f"pisid_mazesound_{player_id}")
        enviar_para_mqtt(dados_sound)
        time.sleep(5)
