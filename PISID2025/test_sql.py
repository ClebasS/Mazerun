import subprocess
import json
import re
import threading
import time

import mysql.connector
import numpy as np
from _decimal import Decimal

REMOTE_DB_CONFIG = {
    "host": "194.210.86.10",
    "user": "aluno",
    "password": "aluno",
    "database": "maze"
}

MQTT_DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "rootpass",
    "database": "mqtt_db",
    "charset": "utf8mb4",
    "collation": "utf8mb4_general_ci"
}

MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = "1883"

sound_leituras = []


def conectar_db_mqtt():
    try:
        conn = mysql.connector.connect(**MQTT_DB_CONFIG)
        print("✅ Conectado ao banco de dados SQL MQTT!")
        return conn
    except mysql.connector.Error as err:
        print(f"❌ Erro ao conectar ao SQL MQTT: {err}")
        return None


def converter_decimals(obj):
    if isinstance(obj, dict):
        return {k: converter_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [converter_decimals(elem) for elem in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj


def ler_dados_setup_corridor():
    while True:
        try:
            conn = mysql.connector.connect(**REMOTE_DB_CONFIG)
            cursor = conn.cursor(dictionary=True)

            print("✅ Conectado ao banco de dados remoto!")

            # Lê os dados da tabela setupMaze
            cursor.execute("""
                SELECT normalnoise, numberrooms, numbermarsamis, noisevartoleration, timemarsamilive
                FROM setupMaze
                LIMIT 1
            """)
            setup_data = cursor.fetchone()
            print("🧩 Dados da tabela setupMaze:")
            print(json.dumps(converter_decimals(setup_data), indent=4))

            # Lê todos os dados da tabela Corridor
            cursor.execute("SELECT roomA, roomB FROM Corridor")
            corridor_data = cursor.fetchall()
            corredores_validos = set()
            for c in corridor_data:
                a, b = c["roomA"], c["roomB"]
                corredores_validos.add((a, b))
            print("🛣️ Dados da tabela Corridor:")
            for row in corridor_data:
                print(row)

            cursor.close()
            conn.close()
            return setup_data, corredores_validos

        except mysql.connector.Error as err:
            print(f"❌ Erro ao acessar banco remoto: {err}")
            print("🔁 Tentando novamente em 5 segundos...")
            time.sleep(5)


def substituir_colon(data):
    return re.sub(r'(?<!\d):|:(?!\d)', '":"', data)


def calcular_iqr(valores):
    q1 = np.percentile(valores, 25)
    q3 = np.percentile(valores, 75)
    iqr = q3 - q1
    lim_inf = q1 - 1.5 * iqr
    lim_sup = q3 + 1.5 * iqr
    return lim_inf, lim_sup


def inserir_alerta(leitura, hora, mensagem):
    conn = conectar_db_mqtt()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        sql = "CALL InserirMensagemAlerta(NULL, NULL, %s, %s, NULL, %s)"
        cursor.execute(sql, (leitura, mensagem, hora))
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"❌ Erro ao inserir alerta: {e}")
    finally:
        conn.close()


def processar_mensagem(topico, payload, setup, corridor_data):
    global sound_leituras
    try:
        print(f"📥 Mensagem recebida em {topico}: {payload}")
        payload_corrigido = substituir_colon(payload)
        payload_corrigido = payload_corrigido.replace(",", "\",\"").replace("{", "{\"").replace("}", "\"}").replace("_",
                                                                                                                    " ")

        data = json.loads(payload_corrigido)
        data = {k.strip(): v.strip() if isinstance(v, str) else v for k, v in data.items()}

        conn = conectar_db_mqtt()
        if not conn:
            return

        cursor = conn.cursor()

        if topico == "sound":
            sound = float(data["Sound"])
            hora = data["Hour"]
            leitura_invalida = 0

            # Verificação de alerta por proximidade ao limite
            limite = float(setup["normalnoise"]) + float(setup["noisevartoleration"])
            limite_atencao = limite - 0.5 * float(setup["noisevartoleration"])
            if limite_atencao <= sound - limite_atencao <= limite:
                print(f"⚠️ Atenção: leitura de som ({sound}) próxima ao limite ({limite:.2f})")
                inserir_alerta(sound, hora, mensagem="Atenção: som próximo ao limite")
            elif sound - limite_atencao > limite:
                print(f"‼️ Perigo: leitura de som ({sound}) ultrapassou o limite ({limite:.2f})")
                inserir_alerta(sound, hora, mensagem="Atenção: som ultrapassou o limite")

            if len(sound_leituras) >= 10:
                lim_inf, lim_sup = calcular_iqr(sound_leituras)
                print(f"📊 IQR: {lim_inf:.2f} - {lim_sup:.2f}")
                if sound < lim_inf or sound > lim_sup:
                    leitura_invalida = 1
                    mensagem = "Leitura de som fora do intervalo esperado (IQR)"
                    inserir_alerta(sound, hora, mensagem)
                    print(f"⚠️ Outlier detectado: {sound}")
                else:
                    sound_leituras.append(sound)
                    if len(sound_leituras) > 10:
                        sound_leituras.pop(0)
            else:
                sound_leituras.append(sound)

            sql = "CALL InserirRuido(%s, %s, %s)"
            valores = (hora, sound, leitura_invalida)

        elif topico == "mov":
            room_origin = int(data["RoomOrigin"])
            room_destiny = int(data["RoomDestiny"])
            movimento_invalido = 0
            if (room_origin, room_destiny) not in corridor_data:
                movimento_invalido = 1
                print(f"⚠️ Movimento inválido: não existe corredor entre {room_origin} e {room_destiny}")
                inserir_alerta(None, data.get("Hour", None),
                               mensagem=f"Movimento inválido entre salas {room_origin} e {room_destiny}")

            sql = "CALL InserirMovimento(%s, %s, %s, %s, %s, %s)"
            valores = (
                data["Marsami"],
                data["RoomOrigin"],
                data["RoomDestiny"],
                data["Status"],
                data.get("Hour", None),
                movimento_invalido
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


def escutar_topico(topico, normal_noise, noise_tolerance):
    try:
        comando = f'mosquitto_sub -h {MQTT_BROKER} -p {MQTT_PORT} -t "{topico}"'
        processo = subprocess.Popen(comando, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        print(f"🚀 Aguardando mensagens do tópico '{topico}'...")

        for linha in processo.stdout:
            mensagem = linha.strip()
            if mensagem:
                processar_mensagem(topico, mensagem, normal_noise, noise_tolerance)

    except Exception as e:
        print(f"❌ Erro ao escutar tópico '{topico}': {e}")


def main():
    setup, corridor_data = ler_dados_setup_corridor()
    if not setup:
        print("❌ Falha ao carregar dados do setup.")
        return

    # Cria uma thread para cada tópico
    topicos = ["sound", "mov"]
    threads = []

    for topico in topicos:
        t = threading.Thread(target=escutar_topico, args=(topico, setup, corridor_data))
        t.start()
        threads.append(t)

    # Aguarda as threads finalizarem (em teoria, nunca vão)
    for t in threads:
        t.join()


if __name__ == "__main__":
    main()
