<?php 
$db = "mqtt_db";
$dbhost = "localhost";
$return["message"] = "";
$return["success"] = false;

$username = $_POST['username'];
$password = $_POST['password'];

try {
    $conn = mysqli_connect($dbhost, $username, $password, $db);

    if ($conn) {
        // Chamada à stored procedure
        $stmt = $conn->prepare("CALL ViewIDUtilizador(?)");
        $stmt->bind_param("s", $username);
        $stmt->execute();
        $result = $stmt->get_result();

        if ($row = $result->fetch_assoc()) {
            $return["success"] = true;
            $return["IDUtilizador"] = $row["IDUtilizador"];
        } else {
            $return["message"] = "Utilizador não encontrado.";
        }

        $stmt->close();
        mysqli_close($conn);
    }

    header('Content-Type: application/json');
    echo json_encode($return);

} catch (Exception $e) {
    $return["message"] = "The login failed. Check if the user exists in the database.";
    header('Content-Type: application/json');    
    echo json_encode($return);        
}
?>
