<?php
$db = "mqtt_db";
$dbhost = "localhost";
$return["success"] = false;

$username = $_POST["username"];
$password = $_POST["password"];
$idUtilizador = $_POST["IDUtilizador"];
$ultimoIDMensagem = $_POST["UltimoIDMensagem"];

try {
    $conn = mysqli_connect($dbhost, $username, $password, $db);
    if ($conn) {
        $stmt = $conn->prepare("CALL ViewNovosAlertas(?, ?)");
        $stmt->bind_param("ii", $idUtilizador, $ultimoIDMensagem);


        if ($stmt->execute()) {
            $result = $stmt->get_result();
            if ($row = $result->fetch_assoc()) {
                $return["success"] = true;
                $return["alertas"] = [
                    "IDMensagem" => $row["IDMensagem"],
                    "IDTipoAlerta" => $row["IDTipoAlerta"],
                    "Descricao" => $row["Mensagem"]
                ];
            } else {
                $return["message"] = "Nenhum alerta encontrado.";
            }
            $result->free_result();
        } else {
            $return["message"] = "Erro ao executar a procedure.";
        }

        $stmt->close();
        mysqli_close($conn);
    } else {
        $return["message"] = "Erro na ligação à base de dados.";
    }

} catch (Exception $e) {
    $return["message"] = "Erro: " . $e->getMessage();
}

header('Content-Type: application/json');
echo json_encode($return);
