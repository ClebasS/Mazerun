import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ConfiguracaoJogoPage extends StatefulWidget {
  final int? idJogo; // Se tiver ID, é visualização

  const ConfiguracaoJogoPage({super.key, this.idJogo});

  @override
  State<ConfiguracaoJogoPage> createState() => _ConfiguracaoJogoPageState();
}

class _ConfiguracaoJogoPageState extends State<ConfiguracaoJogoPage> {
  bool get isVisualizacao => widget.idJogo != null;

  Map<String, String> configJogo = {
    'Identificador': '1',
    'Nível de ruído normal [dB]': '20.5',
    'Número de salas': '5',
    'Número de marsamis': '10',
    'Tempo até um marsami se cansar e parar [s]': '120',
    'Variação do ruído tolerada [dB]': '2.5',
    'Pontuação': '0',
  };

  // Estado das opções de alerta
  bool alertaCansados = true;
  bool alertaPontuacao = true;
  bool alertaLimiteRuido = true;
  bool alertaParesImpares = false;
  bool alertaOutliers = true;
  int intervaloMinimo = 10;

  @override
  void initState() {
    super.initState();
    if (widget.idJogo != null) {
      carregarDadosJogo(widget.idJogo!);
    }
  }

  Future<void> carregarDadosJogo(int idJogo) async {
    final prefs = await SharedPreferences.getInstance();
    final ip = prefs.getString('ip')!;
    final port = prefs.getString('port')!;
    final username = prefs.getString('username')!;
    final password = prefs.getString('password')!;
    final idUser = prefs.getInt('IDUtilizador')!;

    final url = Uri.parse("http://$ip:$port/scripts/php/getJogoPorId.php");

    final response = await http.post(url, body: {
      'username': username,
      'password': password,
      'IDUtilizador': idUser.toString(),
      'IDJogo': idJogo.toString(),
    });

    if (response.statusCode == 200) {
      final jsonData = json.decode(response.body);
      if (jsonData["success"]) {
        final dados = jsonData["jogo"];
        final alertas = (jsonData['alertas'] as List)
          .map((item) => {
                'IDTipoAlerta': item['IDTipoAlerta'],
                'Descricao': item['Descricao'],
                'Visivel': item['Visibilidade'] == 1
              })
          .toList();

        setState(() {
          configJogo = {
            'Identificador': idJogo.toString(),
            'Nível de ruído normal [dB]': dados['RuidoNormal'].toString(),
            'Número de salas': dados['NumeroSalas'].toString(),
            'Número de marsamis': dados['NumeroMarsamis'].toString(),
            'Tempo até um marsami se cansar e parar [s]': dados['TempoAteMarsamisPararem'].toString(),
            'Variação do ruído tolerada [dB]': dados['ToleranciaVariacaoRuido'].toString(),
            'Pontuação': dados['Pontuacao'].toString(),
          };

          // Atualizar alertas com base na Descricao
          for (var alerta in alertas) {
            switch (alerta['Descricao']) {
              case 'Marsamis cansados':
                alertaCansados = alerta['Visivel'];
                break;
              case 'Pontuação':
                alertaPontuacao = alerta['Visivel'];
                break;
              case 'Limite de ruído':
                alertaLimiteRuido = alerta['Visivel'];
                break;
              case 'Pares e ímpares':
                alertaParesImpares = alerta['Visivel'];
                break;
              case 'Outliers':
                alertaOutliers = alerta['Visivel'];
                break;
            }
          }
        });
      }
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Erro ao carregar dados do jogo.")),
      );
    }
  }

  Future<void> guardarJogo() async {
    final prefs = await SharedPreferences.getInstance();
    final ip = prefs.getString('ip')!;
    final port = prefs.getString('port')!;
    final username = prefs.getString('username')!;
    final password = prefs.getString('password')!;
    final idUser = prefs.getInt('IDUtilizador')!;

    final url = Uri.parse("http://$ip:$port/scripts/php/criarJogo.php");

    // Preparar a lista de alertas para enviar
    final alertas = [
      {
        "IDTipoAlerta": 1,
        "Visivel": alertaCansados ? 1 : 0,
        "Descricao": "Marsamis cansados"
      },
      {
        "IDTipoAlerta": 1,
        "Visivel": alertaPontuacao ? 1 : 0,
        "Descricao": "Pontuação"
      },
      {
        "IDTipoAlerta": 2,
        "Visivel": alertaLimiteRuido ? 1 : 0,
        "Descricao": "Limite de ruído"
      },
      {
        "IDTipoAlerta": 1,
        "Visivel": alertaParesImpares ? 1 : 0,
        "Descricao": "Pares e ímpares"
      },
      {
        "IDTipoAlerta": 3,
        "Visivel": alertaOutliers ? 1 : 0,
        "Descricao": "Outliers"
      },
    ];

    final response = await http.post(url, body: {
      "username": username,
      "password": password,
      "Descricao": "Jogo automático",
      "NumeroMarsamis": configJogo['Número de marsamis'],
      "NumeroSalas": configJogo['Número de salas'],
      "RuidoNormal": configJogo['Nível de ruído normal [dB]'],
      "ToleranciaVariacaoRuido": configJogo['Variação do ruído tolerada [dB]'],
      "IntervaloMinimoAlertas": intervaloMinimo.toString(),
      "TempoAteMarsamisPararem": configJogo['Tempo até um marsami se cansar e parar [s]'],
      "IDUtilizador": idUser.toString(),
      "Alertas": jsonEncode(alertas), // 👈 enviar lista de alertas em JSON
    });

    if (response.statusCode == 200) {
      final jsonData = json.decode(response.body);
      if (jsonData["success"]) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("Jogo criado com sucesso!")),
          );
          Navigator.pop(context); // volta à GamesPage
        }
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Erro ao criar jogo.")),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Configurações do Jogo'),
        backgroundColor: Colors.blue,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: ListView(
          children: [
            _buildSectionTitle('Configurações do Jogo'),
            ...configJogo.entries.map((entry) => _buildDisabledField(entry.key, entry.value)),
            const SizedBox(height: 24),
            _buildSectionTitle('Configuração de Mensagens de Alerta'),
            _buildRadioGroup("Marsamis cansados e parados", alertaCansados, (val) {
              setState(() => alertaCansados = val);
            }),
            _buildRadioGroup("Pontuação", alertaPontuacao, (val) {
              setState(() => alertaPontuacao = val);
            }),
            _buildRadioGroup("Proximidade do limite de ruído", alertaLimiteRuido, (val) {
              setState(() => alertaLimiteRuido = val);
            }),
            _buildRadioGroup("Igualdade de marsamis pares e ímpares", alertaParesImpares, (val) {
              setState(() => alertaParesImpares = val);
            }),
            _buildRadioGroup("Detecção de outliers e valores anómalos", alertaOutliers, (val) {
              setState(() => alertaOutliers = val);
            }),
            const SizedBox(height: 16),
            Row(
              children: [
                const Text("Intervalo mínimo entre alertas [s]: "),
                const SizedBox(width: 10),
                Expanded(
                  child: TextField(
                    keyboardType: TextInputType.number,
                    controller: TextEditingController(text: intervaloMinimo.toString()),
                    onChanged: isVisualizacao
                        ? null // 👈 Desativa edição
                        : (val) {
                            setState(() => intervaloMinimo = int.tryParse(val) ?? 10);
                          },
                    enabled: !isVisualizacao,
                  ),
                ),
              ],
            ),
            SizedBox(height: 24),
              if (widget.idJogo != null)
                Center(
                  child: ElevatedButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text('Retroceder'),
                  ),
                )
              else
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    ElevatedButton(
                      onPressed: guardarJogo,
                      child: const Text('Guardar'),
                    ),
                    ElevatedButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('Cancelar'),
                    ),
                  ],
                ),
          ],
        ),
      ),
    );
  }

  Widget _buildDisabledField(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: TextField(
        decoration: InputDecoration(
          labelText: label,
          border: const OutlineInputBorder(),
        ),
        controller: TextEditingController(text: value),
        enabled: false,
      ),
    );
  }

  Widget _buildRadioGroup(String label, bool value, Function(bool) onChanged) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label),
        Row(
          children: [
            Radio<bool>(
              value: true,
              groupValue: value,
              onChanged: isVisualizacao ? null : (val) => onChanged(val!),
            ),
            const Text('Sim'),
            Radio<bool>(
              value: false,
              groupValue: value,
              onChanged: isVisualizacao ? null : (val) => onChanged(val!),
            ),
            const Text('Não'),
          ],
        ),
        const SizedBox(height: 8),
      ],
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Text(
        title,
        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
      ),
    );
  }
}
