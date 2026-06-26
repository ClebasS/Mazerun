import 'package:flutter/material.dart';
import 'package:new_proj/BasePage.dart';

class ConfiguracaoUtilizador extends StatefulWidget {
  const ConfiguracaoUtilizador({super.key});

  @override
  State<ConfiguracaoUtilizador> createState() => _ConfiguracaoUtilizadorState();
}

class _ConfiguracaoUtilizadorState extends State<ConfiguracaoUtilizador> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController(text: 'pedro.pereira@iscte-ul.pt');
  final _telemovelController = TextEditingController(text: '911234215');
  final _novaPassController = TextEditingController();
  final _repitaPassController = TextEditingController();

  @override
  void dispose() {
    _emailController.dispose();
    _telemovelController.dispose();
    _novaPassController.dispose();
    _repitaPassController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BasePage(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Dados do Utilizador', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
              const SizedBox(height: 20),
              _buildDisabledField('Tipo de Utilizador', 'Jogador'),
              _buildDisabledField('Nome', 'Pedro Pereira'),
              _buildEditableField('Email', _emailController, keyboardType: TextInputType.emailAddress),
              _buildEditableField('Telemóvel', _telemovelController, keyboardType: TextInputType.phone),
              _buildPasswordField('Nova Password', _novaPassController),
              _buildPasswordField('Repita Password', _repitaPassController, validator: (value) {
                if (value != _novaPassController.text) {
                  return 'As palavras-passe não coincidem.';
                }
                return null;
              }),
              const SizedBox(height: 20),
              Row(
                children: [
                  ElevatedButton(
                    onPressed: () {
                      if (_formKey.currentState!.validate()) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Dados guardados com sucesso')),
                        );
                      }
                    },
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.black87),
                    child: const Text('Guardar'),
                  ),
                  const SizedBox(width: 10),
                  ElevatedButton(
                    onPressed: () {
                      Navigator.pop(context);
                    },
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.grey),
                    child: const Text('Retroceder'),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDisabledField(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextFormField(
        initialValue: value,
        decoration: InputDecoration(labelText: label),
        enabled: false,
      ),
    );
  }

  Widget _buildEditableField(String label, TextEditingController controller, {TextInputType? keyboardType}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextFormField(
        controller: controller,
        decoration: InputDecoration(labelText: label),
        keyboardType: keyboardType,
      ),
    );
  }

  Widget _buildPasswordField(String label, TextEditingController controller, {String? Function(String?)? validator}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextFormField(
        controller: controller,
        decoration: InputDecoration(
          labelText: label,
          suffixIcon: const Icon(Icons.password),
        ),
        obscureText: true,
        validator: validator,
      ),
    );
  }
}
