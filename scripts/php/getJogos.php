<?php
$db = "mqtt_db";
$dbhost = "localhost";
$return["success"] = false;

$username = $_POST['username'];
$password = $_POST['password'];
$idUtilizador = $_POST['IDUtilizador'];

try {
    $conn = mysqli_connect($dbhost, $username, $password, $db);

    if ($conn) {
        $stmt = $conn->prepare("CALL ViewJogos(?)");
        $stmt->bind_param("i", $idUtilizador);
        $stmt->execute();
        $result = $stmt->get_result();

        $jogos = array();
        while ($row = $result->fetch_assoc()) {
            $jogos[] = $row;
        }

        $return["success"] = true;
        $return["jogos"] = $jogos;

        $stmt->close();
        mysqli_close($conn);
    }

    header('Content-Type: application/json');
    echo json_encode($return);

} catch (Exception $e) {
    $return["message"] = "Erro ao obter jogos.";
    header('Content-Type: application/json');
    echo json_encode($return);
}
?>
