import 'package:flutter_test/flutter_test.dart';

import 'package:leashmap_app/main.dart';

void main() {
  testWidgets('App boots into a loading state', (tester) async {
    await tester.pumpWidget(const LeashMapApp());
    // Before bootstrap completes it shows the connecting state.
    expect(find.text('连接云端…'), findsOneWidget);
  });
}
