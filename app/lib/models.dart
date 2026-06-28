// Data models mirroring docs/api/openapi.yaml.

class LatLng {
  final double lat;
  final double lng;
  const LatLng(this.lat, this.lng);
}

double _toD(dynamic v) => v == null ? 0.0 : (v as num).toDouble();
int? _toIntN(dynamic v) => v == null ? null : (v as num).toInt();

class AppLocation {
  final String ts;
  final double lat;
  final double lng;
  final double accuracyM;
  final String source;
  final double? speedMps;
  final int? heading;
  final String? motionState;

  AppLocation({
    required this.ts,
    required this.lat,
    required this.lng,
    required this.accuracyM,
    required this.source,
    this.speedMps,
    this.heading,
    this.motionState,
  });

  factory AppLocation.fromJson(Map<String, dynamic> j) => AppLocation(
        ts: j['ts'] as String,
        lat: _toD(j['lat']),
        lng: _toD(j['lng']),
        accuracyM: _toD(j['accuracy_m']),
        source: j['source'] as String,
        speedMps: j['speed_mps'] == null ? null : _toD(j['speed_mps']),
        heading: _toIntN(j['heading']),
        motionState: j['motion_state'] as String?,
      );
}

class DeviceStatus {
  final String deviceId;
  final bool online;
  final String mode;
  final int? batteryPct;
  final String? lastSeenAt;

  DeviceStatus({
    required this.deviceId,
    required this.online,
    required this.mode,
    this.batteryPct,
    this.lastSeenAt,
  });

  factory DeviceStatus.fromJson(Map<String, dynamic> j) => DeviceStatus(
        deviceId: j['device_id'] as String,
        online: j['online'] as bool? ?? false,
        mode: j['mode'] as String? ?? 'idle',
        batteryPct: _toIntN(j['battery_pct']),
        lastSeenAt: j['last_seen_at'] as String?,
      );
}

class LatestLocation {
  final String petId;
  final AppLocation? location;
  final DeviceStatus? device;

  LatestLocation({required this.petId, this.location, this.device});

  factory LatestLocation.fromJson(Map<String, dynamic> j) => LatestLocation(
        petId: j['pet_id'] as String,
        location: j['location'] == null
            ? null
            : AppLocation.fromJson(j['location'] as Map<String, dynamic>),
        device: j['device'] == null
            ? null
            : DeviceStatus.fromJson(j['device'] as Map<String, dynamic>),
      );
}

class Pet {
  final String id;
  final String name;
  final String species;
  final String? deviceId;
  final String? lastLocationAt;

  Pet({required this.id, required this.name, required this.species, this.deviceId, this.lastLocationAt});

  factory Pet.fromJson(Map<String, dynamic> j) => Pet(
        id: j['id'] as String,
        name: j['name'] as String,
        species: j['species'] as String? ?? 'dog',
        deviceId: j['device_id'] as String?,
        lastLocationAt: j['last_location_at'] as String?,
      );
}

class Geofence {
  final String id;
  final String petId;
  final String name;
  final double centerLat;
  final double centerLng;
  final double radiusM;
  final bool enabled;
  final bool alertOnExit;
  final bool alertOnEnter;

  Geofence({
    required this.id,
    required this.petId,
    required this.name,
    required this.centerLat,
    required this.centerLng,
    required this.radiusM,
    required this.enabled,
    required this.alertOnExit,
    required this.alertOnEnter,
  });

  factory Geofence.fromJson(Map<String, dynamic> j) => Geofence(
        id: j['id'] as String,
        petId: j['pet_id'] as String? ?? '',
        name: j['name'] as String,
        centerLat: _toD(j['center_lat']),
        centerLng: _toD(j['center_lng']),
        radiusM: _toD(j['radius_m']),
        enabled: j['enabled'] as bool? ?? true,
        alertOnExit: j['alert_on_exit'] as bool? ?? true,
        alertOnEnter: j['alert_on_enter'] as bool? ?? false,
      );
}

class AlertSettings {
  final bool exitEnabled;
  final bool enterEnabled;
  final bool lowBatteryEnabled;
  final bool offlineEnabled;
  final int? lowBatteryThreshold;
  final int? quietStart;
  final int? quietEnd;
  final bool trackingPaused;
  final int retentionDays;

  AlertSettings({
    required this.exitEnabled,
    required this.enterEnabled,
    required this.lowBatteryEnabled,
    required this.offlineEnabled,
    this.lowBatteryThreshold,
    this.quietStart,
    this.quietEnd,
    required this.trackingPaused,
    required this.retentionDays,
  });

  factory AlertSettings.fromJson(Map<String, dynamic> j) => AlertSettings(
        exitEnabled: j['exit_enabled'] as bool? ?? true,
        enterEnabled: j['enter_enabled'] as bool? ?? false,
        lowBatteryEnabled: j['low_battery_enabled'] as bool? ?? true,
        offlineEnabled: j['offline_enabled'] as bool? ?? true,
        lowBatteryThreshold: _toIntN(j['low_battery_threshold']),
        quietStart: _toIntN(j['quiet_start']),
        quietEnd: _toIntN(j['quiet_end']),
        trackingPaused: j['tracking_paused'] as bool? ?? false,
        retentionDays: (j['retention_days'] as num?)?.toInt() ?? 30,
      );
}

class Alert {
  final String id;
  final String petId;
  final String? deviceId;
  final String type;
  final String severity;
  final String status;
  final String message;
  final String createdAt;
  final String? acknowledgedAt;

  Alert({
    required this.id,
    required this.petId,
    this.deviceId,
    required this.type,
    required this.severity,
    required this.status,
    required this.message,
    required this.createdAt,
    this.acknowledgedAt,
  });

  factory Alert.fromJson(Map<String, dynamic> j) => Alert(
        id: j['id'] as String,
        petId: j['pet_id'] as String? ?? '',
        deviceId: j['device_id'] as String?,
        type: j['type'] as String,
        severity: j['severity'] as String,
        status: j['status'] as String,
        message: j['message'] as String,
        createdAt: (j['created_at'] ?? '') as String,
        acknowledgedAt: j['acknowledged_at'] as String?,
      );
}

class Stop {
  final double lat;
  final double lng;
  final int count;
  final int durationS;
  Stop({required this.lat, required this.lng, required this.count, required this.durationS});
  factory Stop.fromJson(Map<String, dynamic> j) => Stop(
        lat: _toD(j['lat']),
        lng: _toD(j['lng']),
        count: (j['count'] as num).toInt(),
        durationS: (j['duration_s'] as num).toInt(),
      );
}

class ActivitySummary {
  final int pointCount;
  final double distanceM;
  final int movingPoints;
  final double activeMinutes;
  final List<double> byHourM;
  final List<Stop> stops;

  ActivitySummary({
    required this.pointCount,
    required this.distanceM,
    required this.movingPoints,
    required this.activeMinutes,
    required this.byHourM,
    required this.stops,
  });

  factory ActivitySummary.fromJson(Map<String, dynamic> j) => ActivitySummary(
        pointCount: (j['point_count'] as num).toInt(),
        distanceM: _toD(j['distance_m']),
        movingPoints: (j['moving_points'] as num).toInt(),
        activeMinutes: _toD(j['active_minutes']),
        byHourM: ((j['by_hour_m'] as List?) ?? []).map((e) => _toD(e)).toList(),
        stops: ((j['stops'] as List?) ?? [])
            .map((e) => Stop.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class TrailData {
  final String petId;
  final int pointCount;
  final double distanceM;
  final List<AppLocation> points;

  TrailData({required this.petId, required this.pointCount, required this.distanceM, required this.points});

  factory TrailData.fromJson(Map<String, dynamic> j) => TrailData(
        petId: j['pet_id'] as String,
        pointCount: (j['point_count'] as num).toInt(),
        distanceM: _toD(j['distance_m']),
        points: ((j['points'] as List?) ?? [])
            .map((e) => AppLocation.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}
