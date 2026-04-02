import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('👤 Profile & Gamification'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () => auth.logout(),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            const CircleAvatar(
              radius: 50,
              child: Icon(Icons.person, size: 50),
            ),
            const SizedBox(height: 16),
            Text(auth.userName, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
            Text(auth.userEmail, style: const TextStyle(color: Colors.grey)),
            const SizedBox(height: 32),
            _buildSectionHeader('🏆 Gamification'),
            const SizedBox(height: 16),
            _buildAchievementList(),
            const SizedBox(height: 32),
            _buildSectionHeader('📍 Statistics'),
            const SizedBox(height: 16),
            _buildSimpleStat('Reward Points', '${auth.points} pts', Colors.orange),
            _buildSimpleStat('Health Score', '85/100', Colors.green),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
    );
  }

  Widget _buildAchievementList() {
    return SizedBox(
      height: 100,
      child: ListView(
        scrollDirection: Axis.horizontal,
        children: [
          _buildBadge('Early Bird', Icons.wb_sunny, Colors.orange),
          _buildBadge('Cyclist', Icons.directions_bike, Colors.blue),
          _buildBadge('Step King', Icons.directions_run, Colors.green),
          _buildBadge('Goal Setter', Icons.flag, Colors.red),
        ],
      ),
    );
  }

  Widget _buildBadge(String label, IconData icon, Color color) {
    return Padding(
      padding: const EdgeInsets.only(right: 16.0),
      child: Column(
        children: [
          CircleAvatar(
            backgroundColor: color.withOpacity(0.2),
            child: Icon(icon, color: color),
          ),
          const SizedBox(height: 4),
          Text(label, style: const TextStyle(fontSize: 12)),
        ],
      ),
    );
  }

  Widget _buildSimpleStat(String label, String value, Color color) {
    return Card(
      child: ListTile(
        title: Text(label),
        trailing: Text(value, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: color)),
      ),
    );
  }
}
