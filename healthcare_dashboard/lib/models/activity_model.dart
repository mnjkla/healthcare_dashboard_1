import 'package:flutter/material.dart';

enum ActivityType { walking, running, cycling, swimming, gym, yoga, other }

class Activity {
  final String id;
  final DateTime date;
  final ActivityType type;
  final int durationMinutes;
  final int caloriesBurned;
  final String notes;

  Activity({
    required this.id,
    required this.date,
    required this.type,
    required this.durationMinutes,
    required this.caloriesBurned,
    this.notes = '',
  });

  Activity copyWith({
    String? id,
    DateTime? date,
    ActivityType? type,
    int? durationMinutes,
    int? caloriesBurned,
    String? notes,
  }) {
    return Activity(
      id: id ?? this.id,
      date: date ?? this.date,
      type: type ?? this.type,
      durationMinutes: durationMinutes ?? this.durationMinutes,
      caloriesBurned: caloriesBurned ?? this.caloriesBurned,
      notes: notes ?? this.notes,
    );
  }
}
