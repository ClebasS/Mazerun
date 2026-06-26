import paho.mqtt.client as mqtt
import pymongo
import json
import re

# Configuração do MQTT
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
TOPICO_RUIDO = "pisid_mazesound_50"
TOPICO_MOVIMENTO = "pisid_mazemov_50"

# Configuração do MongoDB
MONGO_URI = "mongodb://localhost:27019/mqtt_db?replicaSet=PISID25"
client_mongo = pymongo.MongoClient(MONGO_URI)
db = client_mongo["mqtt_db"]


def is_valid_data(data, sensor_type):
    if sensor_type == "mazesound":
        required_fields = ["Player", "Hour", "Sound"]
        if not isinstance(data.get("Sound"), (int, float)):
            return False
    else:
        required_fields = ["Player", "Marsami", "RoomOrigin", "RoomDestiny", "Status"]
        if not all(isinstance(data.get(field), int) for field in required_fields if field != "Hour"):
            return False

    return all(field in data for field in required_fields)


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
            data = json.loads(payload)
        except json.JSONDecodeError:
            print(f"⚠️ JSON inválido, tentando corrigir: {payload}")
            payload_corrigido = re.sub(r'([{,])\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', payload)
            try:
                data = json.loads(payload_corrigido)
            except json.JSONDecodeError:
                print(f"❌ Erro ao corrigir JSON: {payload}")
                db["discarted_data"].insert_one({"original": payload, "reason": "Invalid JSON format"})
                return

        match = re.match(r"pisid_(mazesound|mazemov)_(\d+)", msg.topic)
        if not match:
            print(f"⚠️ Tópico desconhecido: {msg.topic}")
            db["discarted_data"].insert_one({"original": data, "reason": "Unknown topic"})
            return

        sensor_type, player_id = match.groups()
        player_id = int(player_id)

        if is_valid_data(data, sensor_type):
            collection_name = f"pisid_{sensor_type}_{player_id}"
            print(f"💾 Salvando na coleção: {collection_name}")
            db[collection_name].insert_one(data)
            print(f"✅ Dados salvos com sucesso!")
        else:
            print("⚠️ Dados inválidos, armazenando em 'discarted_data'")
            db["discarted_data"].insert_one({"original": data, "reason": "Invalid format or missing values"})

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