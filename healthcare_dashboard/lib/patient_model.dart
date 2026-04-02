class Patient {
  final String name;
  final int age;
  final String gender;
  final String bloodType;
  final String medicalCondition;
  final DateTime dateOfAdmission;
  final String doctor;
  final String hospital;
  final String insuranceProvider;
  final double billingAmount;
  final int roomNumber;
  final String admissionType;
  final DateTime dischargeDate;
  final String medication;
  final String testResults;

  Patient({
    required this.name,
    required this.age,
    required this.gender,
    required this.bloodType,
    required this.medicalCondition,
    required this.dateOfAdmission,
    required this.doctor,
    required this.hospital,
    required this.insuranceProvider,
    required this.billingAmount,
    required this.roomNumber,
    required this.admissionType,
    required this.dischargeDate,
    required this.medication,
    required this.testResults,
  });

  factory Patient.fromCsv(List<dynamic> row) {
    return Patient(
      name: row[0].toString(),
      age: int.tryParse(row[1].toString()) ?? 0,
      gender: row[2].toString(),
      bloodType: row[3].toString(),
      medicalCondition: row[4].toString(),
      dateOfAdmission: DateTime.tryParse(row[5].toString()) ?? DateTime.now(),
      doctor: row[6].toString(),
      hospital: row[7].toString(),
      insuranceProvider: row[8].toString(),
      billingAmount: double.tryParse(row[9].toString()) ?? 0.0,
      roomNumber: int.tryParse(row[10].toString()) ?? 0,
      admissionType: row[11].toString(),
      dischargeDate: DateTime.tryParse(row[12].toString()) ?? DateTime.now(),
      medication: row[13].toString(),
      testResults: row[14].toString(),
    );
  }
}
