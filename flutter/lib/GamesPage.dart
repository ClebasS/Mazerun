import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:http/http.dart' as http;
import 'package:new_proj/BasePage.dart';
import 'package:new_proj/ConfiguracaoJogoPage.dart';
import 'dart:async';

class GamesPage extends StatefulWidget {
  const GamesPage({super.key});

  @override
  State<GamesPage> createState() => _GamesPageState();
}

class _GamesPageState extends State<GamesPage> {

  List<Map<String, dynamic>> alertas = [];
  Timer? alertaTimer;

  List<dynamic> jogos = [];

  @override
  void initState() {
    super.initState();
    carregarJogos();
    iniciarVerificacaoAlertas();
  }

  Future<void> carregarJogos() async {
    final prefs = await SharedPreferences.getInstance();
    final ip = prefs.getString('ip')!;
    final port = prefs.getString('port')!;
    final username = prefs.getString('username')!;
    final password = prefs.getString('password')!;
    final idUser = prefs.getInt('IDUtilizador')!;

    final url = Uri.parse("http://$ip:$port/scripts/php/getJogos.php");

    final response = await http.post(url, body: {
      'username': username,
      'password': password,
      'IDUtilizador': idUser.toString(),
    });

    if (response.statusCode == 200) {
      final jsonData = json.decode(response.body);
      if (jsonData["success"]) {
        setState(() {
          jogos = List<Map<String, dynamic>>.from(jsonData["jogos"]);
        });
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Erro ao carregar jogos.")),
        );
      }
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Erro na comunicação com o servidor.")),
      );
    }
  }

  void iniciarVerificacaoAlertas() {
    alertaTimer = Timer.periodic(const Duration(seconds: 5), (_) {
      verificarNovosAlertas();
    });
  }

  Future<void> verificarNovosAlertas() async {
    final prefs = await SharedPreferences.getInstance();
    final ip = prefs.getString('ip')!;
    final port = prefs.getString('port')!;
    final username = prefs.getString('username')!;
    final password = prefs.getString('password')!;
    final idUser = prefs.getInt('IDUtilizador')!;
    final ultimoID = await obterUltimoIDMensagem();

    final url = Uri.parse("http://$ip:$port/scripts/php/getAlertas.php");
    final response = await http.post(url, body: {
      'username': username,
      'password': password,
      'IDUtilizador': idUser.toString(),
      'UltimoIDMensagem': ultimoID.toString(),
    });

    if (response.statusCode == 200) {
      final jsonData = json.decode(response.body);
      if (jsonData["success"] && jsonData["alertas"] != null) {
        final alertasData = jsonData["alertas"];
        final novosAlertas = alertasData is List
            ? List<Map<String, dynamic>>.from(alertasData)
            : [Map<String, dynamic>.from(alertasData)];
        if (novosAlertas.isNotEmpty) {
          setState(() {
            for (var alerta in novosAlertas.reversed) {
              final novo = {
                'tipo': alerta["IDTipoAlerta"],
                'descricao': alerta["Descricao"],
                'cor': _corAlerta(alerta["IDTipoAlerta"]),
              };
              if (!alertas.any((a) => a['descricao'] == novo['descricao'])) {
                alertas.insert(0, novo);
                if (alertas.length > 3) alertas.removeLast();
              }
            }
          });

          // Atualiza último ID
          final maiorID = novosAlertas.map((a) => a["IDMensagem"] as int).reduce((a, b) => a > b ? a : b);
          await atualizarUltimoIDMensagem(maiorID);
        }
      }
    }
  }

  Color _corAlerta(int tipo) {
    switch (tipo) {
      case 1:
        return Colors.blue;
      case 2:
        return Colors.amber;
      case 3:
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  Future<int> obterUltimoIDMensagem() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getInt('ultimoIDMensagem') ?? 0; // Retorna 0 na primeira vez
  }

  Future<void> atualizarUltimoIDMensagem(int novoID) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt('ultimoIDMensagem', novoID);
  }

  @override
  Widget build(BuildContext context) {
    return BasePage(
      child: Column(
        children: [
          const SizedBox(height: 10),
          const Text(
            'Lista de Jogos',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 10),
          Expanded(
            child: ListView.builder(
              itemCount: jogos.length,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              itemBuilder: (context, index) {
                final jogo = jogos[index];
                return _buildGameTile(jogo);
              },
            ),
          ),
          const SizedBox(height: 10),
          const Text(
            'Alertas Atuais',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 5),
          ...alertas.map((alerta) => Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: alerta['cor'].withOpacity(0.2),
                border: Border.all(color: alerta['cor']),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                alerta['descricao'],
                style: TextStyle(color: alerta['cor'], fontWeight: FontWeight.bold),
              ),
            ),
          )),
          const Divider(height: 1),
          _footerBar(context),
        ],
      ),
    );
  }

  Widget _buildGameTile(Map<String, dynamic> jogo) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      elevation: 2,
      child: ListTile(
        leading: const Icon(Icons.videogame_asset),
        title: Text(jogo['Descricao']),
        subtitle: Text(
          'Início: ${jogo['DataHoraInicio'] ?? '-'}\n'
          'Fim: ${jogo['DataHoraFim'] ?? '-'}\n'
          'Marsamis: ${jogo['NumeroMarsamis'] ?? 0}',
        ),
        trailing: Text(
          (jogo['IDEstadoJogo'] ?? 'Desconhecido').toString(),
          style: TextStyle(
            color: (jogo['IDEstadoJogo'] == 'Concluído') ? Colors.green : Colors.orange,
            fontWeight: FontWeight.bold,
          ),
        ),
        isThreeLine: true,
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => ConfiguracaoJogoPage(idJogo: jogo['IDJogo']),
            ),
          );
        },
      ),
    );
  }

  Widget _footerBar(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          Expanded(
            child: _footerButton(
              'Criar',
              Icons.add,
              () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const ConfiguracaoJogoPage()),
                ).then((_) {
                  carregarJogos();
                });
              },
            ),
          ),
          Expanded(child: _footerButton('Iniciar', Icons.play_arrow, () {})),
          Expanded(child: _footerButton('Terminar', Icons.stop, () {})),
          Expanded(child: _footerButton('Visualizar', Icons.visibility, () {})),
        ],
      ),
    );
  }

  Widget _footerButton(String label, IconData icon, VoidCallback onPressed) {
    return ElevatedButton.icon(
      onPressed: onPressed,
      icon: Icon(icon, size: 18),
      label: Text(label),
      style: ElevatedButton.styleFrom(
        backgroundColor: Colors.white,
        foregroundColor: Colors.blue,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      ),
    );
  }
}
