<?php
header('Content-Type: application/json');

// Dados da base de dados
$db = "mqtt_db";
$dbhost = "localhost";

$return = ['success' => false];

// Verifica se os parâmetros necessários existem
if (isset($_POST['username'], $_POST['password'], $_POST['IDUtilizador'], $_POST['IDJogo'])) {
    $username = $_POST['username'];
    $password = $_POST['password'];
    $IDUtilizador = intval($_POST['IDUtilizador']);
    $IDJogo = intval($_POST['IDJogo']);

    // Tenta conectar à base de dados
    $conn = mysqli_connect($dbhost, $username, $password, $db);

    if ($conn) {
        // Chamada à stored procedure ViewJogoPorID
        $stmt1 = $conn->prepare("CALL ViewJogoPorID(?, ?)");
        $stmt1->bind_param("ii", $IDUtilizador, $IDJogo);
        $stmt1->execute();
        $result1 = $stmt1->get_result();

        $jogo_data = null;
        if ($result1 && $result1->num_rows > 0) {
            $jogo_data = $result1->fetch_assoc();
        }

        $stmt1->close();
        mysqli_next_result($conn); // importante limpar result set antes da próxima CALL

        // Chamada à stored procedure ViewVisibilidadeAlertaPorID
        $stmt2 = $conn->prepare("CALL ViewVisibilidadeAlertaPorID(?, ?)");
        $stmt2->bind_param("ii", $IDUtilizador, $IDJogo);
        $stmt2->execute();
        $result2 = $stmt2->get_result();

        $alertas_data = [];
        if ($result2) {
            while ($row = $result2->fetch_assoc()) {
                $alertas_data[] = $row;
            }
        }

        $stmt2->close();
        mysqli_close($conn);

        if ($jogo_data) {
            $return['success'] = true;
            $return['jogo'] = $jogo_data;
            $return['alertas'] = $alertas_data;
        } else {
            $return['message'] = 'Jogo não encontrado.';
        }
    } else {
        $return['message'] = 'Erro na ligação à base de dados.';
    }
} else {
    $return['message'] = 'Parâmetros inválidos.';
}

echo json_encode($return);
?>
