import subprocess
import threading
from datetime import datetime

import paho.mqtt.client as mqtt
import pymongo
import json
import re

# Configuração do MQTT
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
TOPICO_RUIDO = "pisid_mazesound_50"  # Só para o jogador 10
TOPICO_MOVIMENTO = "pisid_mazemov_50"  # Só para o jogador 10

# Configuração do MongoDB
MONGO_URI = "mongodb://localhost:27019/mqtt_db?replicaSet=PISID25"
client_mongo = pymongo.MongoClient(MONGO_URI)
db = client_mongo["mqtt_db"]


def is_valid_data(data, sensor_type):
    if not isinstance(data, dict):
        return False

    if sensor_type == "mazesound":
        required_fields = {"Player": int, "Hour": str, "Sound": (int, float)}
    else:  # mazemov
        required_fields = {
            "Player": int,
            "Marsami": int,
            "RoomOrigin": int,
            "RoomDestiny": int,
            "Status": int
        }

    # Verificar que os campos são exatamente os esperados (sem mais nem menos)
    if set(data.keys()) != set(required_fields.keys()):
        return False

    for field, expected_type in required_fields.items():
        value = data.get(field)

        if isinstance(expected_type, tuple):
            if not isinstance(value, expected_type):
                return False
        else:
            if not isinstance(value, expected_type):
                return False

        # Validação extra para o campo Hour (se for do tipo som)
        if field == "Hour":
            try:
                datetime.fromisoformat(value)
            except ValueError:
                return False

    return True


# Callback de conexão ao MQTT
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Conectado ao broker MQTT")
        client.subscribe(TOPICO_RUIDO)
        client.subscribe(TOPICO_MOVIMENTO)
        print(f"📡 Inscrito nos tópicos: {TOPICO_RUIDO} e {TOPICO_MOVIMENTO}")
    else:
        print(f"❌ Falha na conexão MQTT, código de retorno: {rc}")


# Callback para mensagens recebidas
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        print(f"📥 Mensagem recebida no tópico {msg.topic}: {payload}")

        try:
            payload_corrigido = re.sub(r'([{,])\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', payload)
            data = json.loads(payload_corrigido)
        except json.JSONDecodeError:
            print(f"❌ Erro ao corrigir JSON: {payload}")
            db["discarted_data"].insert_one({
                "original": payload,
                "reason": "Invalid JSON format",
                "HoraRecebida": datetime.now().isoformat()
            })
            return

        match = re.match(r"pisid_(mazesound|mazemov)_(\d+)", msg.topic)
        if not match:
            print(f"❌ Tópico desconhecido: {msg.topic}")
            db["discarted_data"].insert_one({
                "original": data,
                "reason": "Unknown topic",
                "HoraRecebida": datetime.now().isoformat()
            })
            return

        sensor_type, player_id = match.groups()
        player_id = int(player_id)

        if is_valid_data(data, sensor_type):
            data_completa = data.copy()
            data_completa["Migrated"] = False
            data_completa["HoraRecebida"] = datetime.now().isoformat()

            collection_name = f"pisid_{sensor_type}_{player_id}"
            print(f"💾 Salvando na coleção: {collection_name}")
            db[collection_name].insert_one(data_completa)
            print(f"✅ Dados salvos com sucesso!")
        else:
            print("⚠️ Dados inválidos, armazenando em 'discarted_data'")
            db["discarted_data"].insert_one({
                "original": data,
                "reason": "Invalid format or missing values",
                "HoraRecebida": datetime.now().isoformat()
            })

    except Exception as e:
        print(f"❌ Erro inesperado ao processar mensagem: {e}")
        db["discarted_data"].insert_one({"original": msg.payload.decode("utf-8"), "reason": f"Exception: {str(e)}"})


# Criar e conectar ao MQTT
client_mqtt = mqtt.Client()
client_mqtt.on_connect = on_connect
client_mqtt.on_message = on_message

print("🔄 Conectando ao broker MQTT...")
client_mqtt.connect(MQTT_BROKER, MQTT_PORT)

print("🚀 Aguardando mensagens...")
client_mqtt.loop_forever()


def iniciar_script(nome_script):
    try:
        subprocess.Popen(["python", nome_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Script {nome_script} inciado")
    except Exception as e:
        print(f"❌ Erro ao iniciar {nome_script}: {e}")

# Função principal da aplicação
def main():
    iniciar_script("mongo_sound.py")
    iniciar_script("mongo_mov.py")
    # Inicia as threads para os scripts
    #threading.Thread(target=iniciar_script, args=("mongo_sound.py",)).start()
    #threading.Thread(target=iniciar_script, args=("mongo_mov.py",)).start()

    # Inicia o loop do cliente MQTT
    print("🚀 Aguardando mensagens...")
    client_mqtt.loop_forever()


if __name__ == "__main__":
    main()
