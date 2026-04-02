import 'dart:convert';
import 'package:http/http.dart' as http;

class PatientStats {
  final int totalPatients;
  final double avgAge;
  final double totalBilling;
  final Map<String, dynamic> medicalConditions;
  final Map<String, dynamic> genderDist;
  final Map<String, dynamic> bloodTypes;

  PatientStats({
    required this.totalPatients,
    required this.avgAge,
    required this.totalBilling,
    required this.medicalConditions,
    required this.genderDist,
    required this.bloodTypes,
  });

  factory PatientStats.fromJson(Map<String, dynamic> json) {
    return PatientStats(
      totalPatients: json['total_patients'],
      avgAge: json['avg_age'].toDouble(),
      totalBilling: json['total_billing'].toDouble(),
      medicalConditions: json['medical_conditions'],
      genderDist: json['gender_dist'],
      bloodTypes: json['blood_types'],
    );
  }
}

class DataService {
  final String baseUrl = 'http://localhost:8000';

  Future<PatientStats> fetchPatientStats() async {
    final response = await http.get(Uri.parse('$baseUrl/patients/stats/'));
    
    if (response.statusCode == 200) {
      return PatientStats.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to load patient stats');
    }
  }
}
