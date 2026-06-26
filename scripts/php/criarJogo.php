<?php
$db = "mqtt_db";
$dbhost = "localhost";
$return["success"] = false;

$descricao = $_POST["Descricao"];
$numeromarsamis = $_POST["NumeroMarsamis"];
$numerosalas = $_POST["NumeroSalas"];
$ruidonormal = $_POST["RuidoNormal"];
$tolerancia = $_POST["ToleranciaVariacaoRuido"];
$intervalo = $_POST["IntervaloMinimoAlertas"];
$tempoParagem = $_POST["TempoAteMarsamisPararem"];
$idEstado = 1;
$idUtilizador = $_POST["IDUtilizador"];

$username = $_POST['username'];
$password = $_POST['password'];

$alertas = isset($_POST["Alertas"]) ? json_decode($_POST["Alertas"], true) : [];

try {
    $conn = mysqli_connect($dbhost, $username, $password, $db);
    if ($conn) {
        // Inserir jogo
        $stmt = $conn->prepare("CALL InserirJogos(?, ?, ?, ?, ?, ?, ?, ?, ?)");
        $stmt->bind_param("siiidiiii", $descricao, $numeromarsamis, $numerosalas, $ruidonormal, $tolerancia, $intervalo, $tempoParagem, $idEstado, $idUtilizador);

        if ($stmt->execute()) {
            $stmt->close();
            mysqli_next_result($conn); // limpar resultado pendente da call anterior

            // Obter ID do último jogo
            $result = mysqli_query($conn, "CALL ViewUltimoIDJogo()");
            if ($row = mysqli_fetch_assoc($result)) {
                $idJogoCriado = $row['IDJogo'];
                mysqli_free_result($result);
                mysqli_next_result($conn);

                // Inserir alertas
                foreach ($alertas as $alerta) {
                    $idTipoAlerta = $alerta['IDTipoAlerta'];
                    $visivel = $alerta['Visivel'];
                    $descricao = $alerta['Descricao'];

                    $stmtAlerta = $conn->prepare("CALL InserirVisibilidadeAlerta(?, ?, ?, ?)");
                    $stmtAlerta->bind_param("iiis", $idJogoCriado, $idTipoAlerta, $visivel, $descricao);
                    $stmtAlerta->execute();
                    $stmtAlerta->close();

                    // limpar qualquer resultado interno da procedure
                    while (mysqli_more_results($conn)) {
                        mysqli_next_result($conn);
                    }
                }

                $return["success"] = true;
            } else {
                $return["message"] = "Erro ao obter ID do jogo.";
            }
        } else {
            $return["message"] = "Erro ao inserir jogo.";
        }

        mysqli_close($conn);
    } else {
        $return["message"] = "Erro na ligação à base de dados.";
    }

} catch (Exception $e) {
    $return["message"] = "Erro: " . $e->getMessage();
}

header('Content-Type: application/json');
echo json_encode($return);
?>
