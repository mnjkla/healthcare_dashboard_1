import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../data_service.dart';
import '../patient_model.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final DataService _dataService = DataService();
  late Future<PatientStats> _statsFuture;

  @override
  void initState() {
    super.initState();
    _statsFuture = _dataService.fetchPatientStats();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('📊 Analytics Dashboard'),
      ),
      body: FutureBuilder<PatientStats>(
        future: _statsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          }
          if (!snapshot.hasData) {
            return const Center(child: Text('No data found'));
          }

          final stats = snapshot.data!;
          return SingleChildScrollView(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildSummaryCards(stats),
                const SizedBox(height: 24),
                _buildChartsGrid(stats),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildSummaryCards(PatientStats stats) {
    final currencyFormat = NumberFormat.currency(symbol: '\$', decimalDigits: 0);

    return Row(
      children: [
        _buildStatCard('Total Patients', '${stats.totalPatients}', Colors.blue),
        _buildStatCard('Avg Age', stats.avgAge.toStringAsFixed(1), Colors.green),
        _buildStatCard('Total Billing', currencyFormat.format(stats.totalBilling), Colors.orange),
      ],
    );
  }

  Widget _buildStatCard(String title, String value, Color color) {
    return Expanded(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            children: [
              Text(title, style: const TextStyle(fontSize: 14, color: Colors.grey)),
              const SizedBox(height: 8),
              Text(value, style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildChartsGrid(PatientStats stats) {
    return LayoutBuilder(
      builder: (context, constraints) {
        int crossAxisCount = constraints.maxWidth > 800 ? 2 : 1;
        return GridView.count(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisCount: crossAxisCount,
          childAspectRatio: 1.4,
          mainAxisSpacing: 16,
          crossAxisSpacing: 16,
          children: [
            _buildMedicalConditionChart(stats.medicalConditions),
            _buildGenderPieChart(stats.genderDist),
            _buildInsuranceChart(stats.totalBilling), // insurance data is missing in summary so I'll reuse totalBilling or skip
            _buildBloodTypeChart(stats.bloodTypes),
          ],
        );
      },
    );
  }

  Widget _buildMedicalConditionChart(Map<String, dynamic> counts) {
    var sorted = counts.entries.toList()..sort((a, b) => (b.value as int).compareTo(a.value as int));
    var top5 = sorted.take(5).toList();

    return _buildChartContainer('Top Medical Conditions', 
      BarChart(
        BarChartData(
          barGroups: top5.asMap().entries.map((e) => BarChartGroupData(
            x: e.key,
            barRods: [BarChartRodData(toY: (e.value.value as int).toDouble(), color: Colors.blueAccent, width: 16)],
          )).toList(),
          titlesData: FlTitlesData(
            leftTitles: const AxisTitles(sideTitles: SideTitles(showTitles: true, reservedSize: 40)),
            bottomTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                getTitlesWidget: (value, meta) => Text(top5[value.toInt()].key, style: const TextStyle(fontSize: 8)),
              ),
            ),
          ),
        ),
      )
    );
  }

  Widget _buildGenderPieChart(Map<String, dynamic> dist) {
    int male = dist['Male'] ?? 0;
    int female = dist['Female'] ?? 0;

    return _buildChartContainer('Gender Distribution', 
      PieChart(
        PieChartData(
          sections: [
            PieChartSectionData(value: male.toDouble(), title: 'Male', color: Colors.blue, radius: 40),
            PieChartSectionData(value: female.toDouble(), title: 'Female', color: Colors.pink, radius: 40),
          ],
        ),
      )
    );
  }

  Widget _buildInsuranceChart(double totalBilling) {
    // Mocking insurance breakdown based on total billing as we don't have it in the summary anymore
    return _buildChartContainer('Billing Summary', 
       Center(child: Text('Total Billing: \$${(totalBilling/1000000).toStringAsFixed(1)}M', style: TextStyle(fontSize: 18)))
    );
  }

  Widget _buildBloodTypeChart(Map<String, dynamic> counts) {
    var entries = counts.entries.toList();

    return _buildChartContainer('Patient Blood Types', 
      BarChart(
        BarChartData(
          barGroups: entries.asMap().entries.map((e) => BarChartGroupData(
            x: e.key,
            barRods: [BarChartRodData(toY: (e.value.value as int).toDouble(), color: Colors.redAccent, width: 12)],
          )).toList(),
          titlesData: FlTitlesData(
            leftTitles: const AxisTitles(sideTitles: SideTitles(showTitles: true, reservedSize: 30)),
            bottomTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                getTitlesWidget: (value, meta) => Text(entries[value.toInt()].key, style: const TextStyle(fontSize: 8)),
              ),
            ),
          ),
        ),
      )
    );
  }

  Widget _buildChartContainer(String title, Widget chart) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Column(
          children: [
            Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            Expanded(child: chart),
          ],
        ),
      ),
    );
  }
}
