import subprocess
import json
import re

import mysql.connector

REMOTE_DB_CONFIG = {
    "host": "194.210.86.10",
    "user": "aluno",
    "password": "aluno",
    "database": "pisid20245"
}

# Configuração do banco de dados MQTT
MQTT_DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "rootpass",
    "database": "mqtt_db",
    "charset": "utf8mb4",
    "collation": "utf8mb4_general_ci"
}

# Configuração do Mosquitto (Broker MQTT)
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = "1883"
TOPICOS = ["sound", "mov"]  # Todos os jogadores

global dados_setup
global corredores


# Conectar ao banco de dados MQTT
def conectar_db_mqtt():
    try:
        conn = mysql.connector.connect(**MQTT_DB_CONFIG)
        print("✅ Conectado ao banco de dados SQL MQTT!")
        return conn
    except mysql.connector.Error as err:
        print(f"❌ Erro ao conectar ao SQL MQTT: {err}")
        return None


def importar_setup_maze():
    resultados = []
    corredores_resultados = []
    try:
        conn = mysql.connector.connect(**REMOTE_DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT normalnoise, numberrooms, numbermarsamis, noisevartoleration FROM setupMaze")
        resultados = cursor.fetchall()

        cursor.execute("SELECT roomA, roomB FROM corridor")
        corredores_resultados = cursor.fetchall()

        cursor.close()
        conn.close()
        print("✅ Dados importados do banco remoto:")
        for row in resultados:
            print(row)
    except Exception as e:
        print(f"❌ Erro ao importar da base remota: {e}")
    return resultados, corredores_resultados


def substituir_colon(data):
    # Substitui ":" por "\":\"" somente se não estiver entre números
    return re.sub(r'(?<!\d):|:(?!\d)', '":"', data)


# Processa as mensagens recebidas e insere no SQL
def processar_mensagem(topico, payload):
    try:
        print(f"📥 Mensagem recebida em {topico}: {payload}")
        payload_corrigido = substituir_colon(payload)
        payload_corrigido = payload_corrigido.replace(",", "\",\"").replace("{", "{\"").replace("}", "\"}").replace("_", " ")

        print(f"📥 Mensagem recebida em {topico}: {payload_corrigido}")
        data = json.loads(payload_corrigido)

        data = {k.strip(): v.strip() if isinstance(v, str) else v for k, v in data.items()}

        conn = conectar_db_mqtt()
        if conn:
            cursor = conn.cursor()

            if "sound" in topico:
                sql = "CALL InserirRuido(%s, %s, %s, %s, %s, %s)"
                valores = (
                    data["Hour"],
                    data["Sound"],
                    data.get("LeituraInvalida", 0)
                )
            elif "mov" in topico:
                sql = "CALL InserirMovimento(%s, %s, %s, %s, %s, %s)"
                valores = (
                    data["Marsami"],
                    data["RoomOrigin"],
                    data["RoomDestiny"],
                    data["Status"],
                    data.get("Hour", None),
                    data.get("MovimentoInvalido", 0)  # Se não houver valor, assume 0
                )
            else:
                print("⚠️ Tópico desconhecido, ignorando...")
                return

            cursor.execute(sql, valores)
            conn.commit()
            cursor.close()
            conn.close()
            print(f"✅ Dados inseridos no SQL ({topico})!")

    except json.JSONDecodeError:
        print(f"❌ Erro ao decodificar JSON: {payload}")
    except Exception as e:
        print(f"❌ Erro ao processar mensagem: {e}")


# Inicia o mosquitto_sub e processa as mensagens recebidas
def iniciar_mosquitto_sub():
    try:
        comando = f'mosquitto_sub -h {MQTT_BROKER} -p {MQTT_PORT} -t "sound" -t "mov"'
        processo = subprocess.Popen(comando, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        print("🚀 Aguardando mensagens do MQTT para salvar no SQL...")

        for linha in processo.stdout:
            mensagem = linha.strip()
            if mensagem:
                # Verifica se a mensagem contém a palavra "Marsami" ou "Sound"
                if "Marsami" in mensagem:
                    topico = "mov"
                elif "Sound" in mensagem:
                    topico = "sound"
                else:
                    print(f"⚠️ Mensagem desconhecida: {mensagem}")
                    continue

                processar_mensagem(topico, mensagem)

    except Exception as e:
        print(f"❌ Erro ao executar mosquitto_sub: {e}")


# Inicia o script
if __name__ == "__main__":
    dados_setup, corredores = importar_setup_maze()
    iniciar_mosquitto_sub()
