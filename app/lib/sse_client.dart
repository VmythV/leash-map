import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import 'config.dart';

/// One Server-Sent Event.
class SseEvent {
  final String event;
  final Map<String, dynamic> data;
  SseEvent(this.event, this.data);
}

/// Subscribes to the LeashMap realtime SSE stream. Flutter has no EventSource,
/// so we read the streamed response and parse SSE frames ourselves. The token
/// is passed as a query param (see docs/api/realtime-events.md).
class SseClient {
  SseClient({String? baseUrl}) : baseUrl = baseUrl ?? AppConfig.baseUrl;

  final String baseUrl;
  http.Client? _client;
  StreamSubscription<String>? _sub;

  Stream<SseEvent> connect({required String token, String? petId}) {
    final controller = StreamController<SseEvent>();
    _client = http.Client();

    final qp = <String, String>{'access_token': token};
    if (petId != null) qp['pet_id'] = petId;
    final uri = Uri.parse('$baseUrl/v1/realtime/stream').replace(queryParameters: qp);

    () async {
      try {
        final req = http.Request('GET', uri)..headers['accept'] = 'text/event-stream';
        final resp = await _client!.send(req);

        String currentEvent = 'message';
        final buffer = StringBuffer();

        _sub = resp.stream
            .transform(utf8.decoder)
            .transform(const LineSplitter())
            .listen((line) {
          if (line.isEmpty) {
            // dispatch on blank line
            final raw = buffer.toString();
            buffer.clear();
            if (raw.isNotEmpty) {
              try {
                controller.add(SseEvent(currentEvent, jsonDecode(raw) as Map<String, dynamic>));
              } catch (_) {}
            }
            currentEvent = 'message';
          } else if (line.startsWith(':')) {
            // comment / keepalive
          } else if (line.startsWith('event:')) {
            currentEvent = line.substring(6).trim();
          } else if (line.startsWith('data:')) {
            buffer.write(line.substring(5).trim());
          }
        }, onError: controller.addError, onDone: controller.close);
      } catch (e) {
        controller.addError(e);
        await controller.close();
      }
    }();

    controller.onCancel = close;
    return controller.stream;
  }

  void close() {
    _sub?.cancel();
    _sub = null;
    _client?.close();
    _client = null;
  }
}
