import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/activity_provider.dart';

class DssScreen extends StatelessWidget {
  const DssScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final activityProvider = context.watch<ActivityProvider>();
    final totalCalories = activityProvider.totalCalories;
    final activityCount = activityProvider.activities.length;

    return Scaffold(
      appBar: AppBar(
        title: const Text('🧠 AI Health Insights'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            _buildInsightCard(
              'Activity Status',
              activityCount > 0 ? 'Good job! You have logged $activityCount activities.' : 'Sedentary alert! No activities logged yet.',
              activityCount > 0 ? Colors.green : Colors.orange,
              Icons.trending_up,
            ),
            const SizedBox(height: 16),
            _buildInsightCard(
              'Calorie Burn',
              'Total calories burned today: $totalCalories kcal.',
              totalCalories > 200 ? Colors.blue : Colors.grey,
              Icons.local_fire_department,
            ),
            const SizedBox(height: 16),
            if (activityCount == 0)
              _buildRecommendationCard(
                'Next Best Action',
                'Based on your data, we recommend a 15-minute walk to jumpstart your metabolism.',
                'Start Walking',
                () {},
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildInsightCard(String title, String content, Color color, IconData icon) {
    return Card(
      child: ListTile(
        leading: Icon(icon, color: color, size: 32),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Text(content),
      ),
    );
  }

  Widget _buildRecommendationCard(String title, String content, String action, VoidCallback onPressed) {
    return Card(
      color: Colors.blue.withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.blue)),
            const SizedBox(height: 8),
            Text(content),
            const SizedBox(height: 16),
            ElevatedButton(onPressed: onPressed, child: Text(action)),
          ],
        ),
      ),
    );
  }
}
