# app — User App (Flutter)

宠物主人端 App：实时位置、轨迹回放、安全区、告警。接现有云端 API/SSE。
详细设计见 [../docs/detailed-design/app.md](../docs/detailed-design/app.md)，
接口契约见 [../docs/api/](../docs/api/)。

## 技术栈（Phase 0 已定）

Flutter（Material 3，dark）+ provider 状态管理 + http + intl。
地图用自包含 **Canvas MiniMap**（CustomPaint，不依赖外部瓦片），MVP 零外部地图 key。
目标平台先做 **Web**（便于联调），后续可加 iOS/Android。

## 快速开始

```bash
# 1) 先起云端（另一个终端）
cd ../server && uv run uvicorn leashmap.main:app --port 8080

# 2) 跑 App（Web）
cd app
flutter run -d chrome --dart-define=LEASHMAP_API=http://localhost:8080

flutter analyze        # 静态检查
flutter test           # widget 测试
flutter build web      # 产物在 build/web
```

`LEASHMAP_API` 默认 `http://localhost:8080`，云端 `local` 环境已开 CORS。

## 自带演示

App 启动会自动：建 demo 会话 → 建/取宠物 → 绑定一台设备 → 在演示中心建安全区「家」→ 订阅 SSE。
首页点 **「模拟走动」** 调用云端 `/demo/run`，让宠物走出安全区——地图实时移动、
电量更新、离区告警弹出（全程经 SSE）。无需硬件、无需单独跑模拟器。

## 代码布局

```text
lib/
  main.dart            应用入口 + 主题 + Provider
  config.dart          API base URL、演示中心坐标
  models.dart          数据模型（对应 openapi.yaml）+ LatLng
  api_client.dart      REST 客户端（App API）
  sse_client.dart      SSE 流解析（EventSource 替代，token 走 query）
  app_state.dart       ChangeNotifier：会话/宠物/实时位置/告警
  util.dart            时间格式化、告警文案
  widgets/
    mini_map.dart      自包含 Canvas 地图（安全区 + 轨迹 + 标记）
  screens/
    home_screen.dart   地图首页（实时位置、状态卡、入口）
    trail_screen.dart  轨迹回放（近 24 小时）
    safezone_screen.dart 安全区列表 + 新建
    alerts_screen.dart 告警列表 + 确认
test/
  widget_test.dart     启动 smoke 测试
```

## 现状与后续

已实现：demo 会话、宠物/绑定、地图首页（实时位置/电量/在线/精度/来源）、
轨迹回放、圆形安全区新建、告警列表与确认、SSE 实时更新、自带走动演示。

后续：
- [ ] iOS/Android 平台与真实地图 SDK（高德/腾讯/Mapbox）
- [ ] 多宠物切换、设备绑定扫码
- [ ] 寻宠模式（下行命令）
- [ ] 正式账号体系替代 demo 会话
