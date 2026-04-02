import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

class LeaderboardScreen extends StatefulWidget {
  const LeaderboardScreen({super.key});

  @override
  State<LeaderboardScreen> createState() => _LeaderboardScreenState();
}

class _LeaderboardScreenState extends State<LeaderboardScreen> {
  final String baseUrl = 'http://localhost:8000';

  Future<List<dynamic>> _fetchLeaderboard() async {
    final response = await http.get(Uri.parse('$baseUrl/leaderboard/'));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    return [];
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🏆 Community Leaderboard'),
      ),
      body: FutureBuilder<List<dynamic>>(
        future: _fetchLeaderboard(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          }
          final users = snapshot.data ?? [];
          if (users.isEmpty) {
            return const Center(child: Text('No participants yet.'));
          }

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: users.length,
            itemBuilder: (context, index) {
              final user = users[index];
              final isMe = user['email'] == context.read<AuthProvider>().userEmail;
              
              return Card(
                color: isMe ? Colors.blue.withOpacity(0.1) : null,
                child: ListTile(
                  leading: _buildRankBadge(index + 1),
                  title: Text(user['full_name'], style: TextStyle(fontWeight: isMe ? FontWeight.bold : FontWeight.normal)),
                  subtitle: Text('${user['health_score']} Health Score'),
                  trailing: Text('${user['points']} pts', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.orange)),
                ),
              );
            },
          );
        },
      ),
    );
  }

  Widget _buildRankBadge(int rank) {
    Color badgeColor;
    if (rank == 1) badgeColor = Colors.yellow[700]!;
    else if (rank == 2) badgeColor = Colors.grey[400]!;
    else if (rank == 3) badgeColor = Colors.orange[300]!;
    else badgeColor = Colors.transparent;

    return CircleAvatar(
      backgroundColor: badgeColor,
      child: Text('#$rank', style: TextStyle(color: rank <= 3 ? Colors.black : Colors.white)),
    );
  }
}
