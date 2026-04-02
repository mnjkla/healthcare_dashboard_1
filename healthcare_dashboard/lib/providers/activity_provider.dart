import 'package:flutter/material.dart';
import '../models/activity_model.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

class ActivityProvider with ChangeNotifier {
  List<Activity> _activities = [];
  final String baseUrl = 'http://localhost:8000';

  List<Activity> get activities => List.unmodifiable(_activities);

  Future<void> fetchActivities(int userId) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/activities/$userId'));
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        _activities = data.map((json) => Activity(
          id: json['id'].toString(),
          date: DateTime.parse(json['date']),
          type: _parseType(json['type']),
          durationMinutes: json['duration_minutes'],
          caloriesBurned: json['calories_burned'],
          notes: json['notes'] ?? '',
        )).toList();
        notifyListeners();
      }
    } catch (e) {
      print('Fetch error: $e');
    }
  }

  ActivityType _parseType(String type) {
    return ActivityType.values.firstWhere(
      (e) => e.name == type,
      orElse: () => ActivityType.other,
    );
  }

  Future<void> addActivity(int userId, ActivityType type, int duration, int calories, {String notes = ''}) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/activities/$userId'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'type': type.name,
          'duration_minutes': duration,
          'calories_burned': calories,
          'notes': notes,
        }),
      );

      if (response.statusCode == 200) {
        fetchActivities(userId);
      }
    } catch (e) {
      print('Add activity error: $e');
    }
  }

  Future<void> deleteActivity(String id) async {
    // In real app, call DELETE /activities/{id}
    _activities.removeWhere((a) => a.id == id);
    notifyListeners();
  }

  int get totalCalories => _activities.fold(0, (sum, a) => sum + a.caloriesBurned);
}
