import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/activity_provider.dart';
import '../models/activity_model.dart';
import 'package:intl/intl.dart';

class ActivityScreen extends StatelessWidget {
  const ActivityScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final activityProvider = context.watch<ActivityProvider>();
    final auth = context.read<AuthProvider>();
    
    // Fetch once
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (activityProvider.activities.isEmpty && auth.isAuthenticated) {
        activityProvider.fetchActivities(auth.userId);
      }
    });

    final activities = activityProvider.activities;

    return Scaffold(
      appBar: AppBar(
        title: const Text('🏃 Activity Logging'),
      ),
      body: activities.isEmpty
          ? const Center(child: Text('No activities logged yet.'))
          : ListView.builder(
              itemCount: activities.length,
              itemBuilder: (context, index) {
                final activity = activities[index];
                return ListTile(
                  leading: CircleAvatar(
                    child: Icon(_getActivityIcon(activity.type)),
                  ),
                  title: Text('${activity.type.name} - ${activity.durationMinutes} mins'),
                  subtitle: Text('Burned: ${activity.caloriesBurned} kcal - ${DateFormat('Md').format(activity.date)}'),
                  trailing: IconButton(
                    icon: const Icon(Icons.delete, color: Colors.red),
                    onPressed: () => activityProvider.deleteActivity(activity.id),
                  ),
                );
              },
            ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showAddActivityDialog(context),
        child: const Icon(Icons.add),
      ),
    );
  }

  IconData _getActivityIcon(ActivityType type) {
    switch (type) {
      case ActivityType.walking: return Icons.directions_walk;
      case ActivityType.running: return Icons.directions_run;
      case ActivityType.cycling: return Icons.directions_bike;
      case ActivityType.swimming: return Icons.pool;
      case ActivityType.gym: return Icons.fitness_center;
      case ActivityType.yoga: return Icons.self_improvement;
      default: return Icons.help_outline;
    }
  }

  void _showAddActivityDialog(BuildContext context) {
    final typeController = TextEditingController();
    final durationController = TextEditingController();
    ActivityType selectedType = ActivityType.walking;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: const Text('Log New Activity'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButton<ActivityType>(
                value: selectedType,
                isExpanded: true,
                onChanged: (val) => setState(() => selectedType = val!),
                items: ActivityType.values.map((e) => DropdownMenuItem(
                  value: e,
                  child: Text(e.name),
                )).toList(),
              ),
              TextField(
                controller: durationController,
                decoration: const InputDecoration(labelText: 'Duration (mins)'),
                keyboardType: TextInputType.number,
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () {
                final duration = int.tryParse(durationController.text) ?? 0;
                if (duration > 0) {
                  // Mock calorie calculation: 5 kcal/min for walking, 10 for running, etc.
                  int calories = duration * 7; 
                  context.read<ActivityProvider>().addActivity(
                    context.read<AuthProvider>().userId, 
                    selectedType, 
                    duration, 
                    calories
                  );
                  Navigator.pop(context);
                }
              },
              child: const Text('Add'),
            ),
          ],
        ),
      ),
    );
  }
}
