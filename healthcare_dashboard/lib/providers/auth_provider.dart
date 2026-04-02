import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

class AuthProvider with ChangeNotifier {
  bool _isAuthenticated = false;
  String _userName = '';
  String _userEmail = '';
  int _userId = 0;
  int _points = 0;

  bool get isAuthenticated => _isAuthenticated;
  String get userName => _userName;
  String get userEmail => _userEmail;
  int get userId => _userId;
  int get points => _points;

  Future<void> fetchUserProfile() async {
    if (!_isAuthenticated) return;
    try {
      final usersResponse = await http.get(Uri.parse('http://localhost:8000/leaderboard/'));
      if (usersResponse.statusCode == 200) {
        final List<dynamic> users = jsonDecode(usersResponse.body);
        final user = users.firstWhere((u) => u['email'] == _userEmail, orElse: () => null);
        if (user != null) {
          _points = user['points'];
          _userId = user['id'];
          notifyListeners();
        }
      }
    } catch (e) {
      print('Fetch profile error: $e');
    }
  }

  Future<bool> login(String email, String password) async {
    try {
      // For now, we use a simple POST to /users/ or check if user exists.
      // In a real app, this would be a /login endpoint returning a JWT.
      final response = await http.post(
        Uri.parse('http://localhost:8000/users/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email,
          'full_name': 'Nguyễn Văn A',
          'password': password,
        }),
      );

      if (response.statusCode == 200 || response.statusCode == 400) {
        // 400 means email already registered (mock "login" as "register or login")
        _isAuthenticated = true;
        _userName = 'Nguyễn Văn A';
        _userEmail = email;
        _userId = 1; // Default
        await fetchUserProfile();
        notifyListeners();
        return true;
      }
    } catch (e) {
      print('Login error: $e');
    }
    return false;
  }

  void logout() {
    _isAuthenticated = false;
    _userName = '';
    _userEmail = '';
    _userId = 0;
    notifyListeners();
  }
}
