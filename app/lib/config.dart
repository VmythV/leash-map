/// App configuration. Override the API base URL at build/run time with:
///   flutter run -d chrome --dart-define=LEASHMAP_API=http://localhost:8080
class AppConfig {
  static const String baseUrl =
      String.fromEnvironment('LEASHMAP_API', defaultValue: 'http://localhost:8080');

  /// Demo safe-zone center, matching the server's /demo/run movement.
  static const double demoCenterLat = 31.2304;
  static const double demoCenterLng = 121.4737;
  static const double demoRadiusM = 120.0;
}
