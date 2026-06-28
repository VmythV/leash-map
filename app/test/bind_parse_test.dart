import 'package:flutter_test/flutter_test.dart';

import 'package:leashmap_app/screens/bind_screen.dart';

void main() {
  test('parseDeviceId accepts bare id', () {
    expect(parseDeviceId('dev_mvp_001'), 'dev_mvp_001');
    expect(parseDeviceId('  dev_abc  '), 'dev_abc');
  });

  test('parseDeviceId accepts url with device query', () {
    expect(parseDeviceId('leashmap://bind?device=dev_x'), 'dev_x');
    expect(parseDeviceId('https://leashmap.example/bind?device=dev_y&n=1'), 'dev_y');
  });

  test('parseDeviceId rejects invalid', () {
    expect(parseDeviceId(''), isNull);
    expect(parseDeviceId('hello'), isNull);
    expect(parseDeviceId('https://x.example/?device=nope'), isNull);
  });
}
