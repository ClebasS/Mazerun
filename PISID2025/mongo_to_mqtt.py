import pymongo
import json
import time
import subprocess  # Para executar comandos do sistema

# Configuração do MongoDB
MONGO_URI = "mongodb://localhost:27019/mqtt_db?replicaSet=PISID25"
client_mongo = pymongo.MongoClient(MONGO_URI)
db = client_mongo["mqtt_db"]

# Configuração do Mosquitto
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
TOPICO_SOUND = "sound"
TOPICO_MOV = "mov"


# Função para buscar e remover dados do MongoDB
def buscar_e_remover_dados_mongo(collection_name):
    collection = db[collection_name]
    dados = list(collection.find())  # Buscar todos os dados disponíveis

    if dados:
        collection.delete_many({})  # Remover os dados após o envio
    return dados


# Função para enviar dados para o broker MQTT usando mosquitto_pub
def enviar_para_mqtt(dados, topico):
    if not dados:
        return  # Se não há dados, não faz nada

    for dado in dados:
        dado.pop("_id", None)  # Remover o '_id' do MongoDB

        if "Hour" in dado:
            dado["Hour"] = dado["Hour"].replace(" ", "_")

        # Converter para JSON
        mensagem_json = json.dumps(dado)  # Converter para JSON

        # Executar o comando mosquitto_pub
        comando = f'mosquitto_pub -h {MQTT_BROKER} -t {topico} -q 2 -m "{mensagem_json}"'
        subprocess.run(comando, shell=True)

        print(f"✅ Mensagem enviada para '{topico}': {mensagem_json}")


# Função principal em loop infinito
def main():
    player_id = 50  # Substitua com o ID do jogador

    while True:
        # Buscar e enviar dados da coleção 'pisid_mazesound_n' para o tópico 'sound'
        dados_sound = buscar_e_remover_dados_mongo(f"pisid_mazesound_{player_id}")
        enviar_para_mqtt(dados_sound, TOPICO_SOUND)

        # Buscar e enviar dados da coleção 'pisid_mazemov_n' para o tópico 'mov'
        dados_mov = buscar_e_remover_dados_mongo(f"pisid_mazemov_{player_id}")
        enviar_para_mqtt(dados_mov, TOPICO_MOV)

        # Espera 5 segundos antes de buscar novos dados
        time.sleep(5)


if __name__ == "__main__":
    main()
