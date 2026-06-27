import 'package:intl/intl.dart';

/// Format an ISO-8601 UTC timestamp as local HH:mm:ss; empty -> '—'.
String fmtTime(String? iso) {
  if (iso == null || iso.isEmpty) return '—';
  try {
    return DateFormat('MM-dd HH:mm:ss').format(DateTime.parse(iso).toLocal());
  } catch (_) {
    return iso;
  }
}

const Map<String, String> alertTypeLabel = {
  'exit_zone': '离开安全区',
  'low_battery': '低电量',
  'offline': '设备离线',
};
