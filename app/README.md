# app — User App

宠物主人端 App：绑定设备、查看实时位置、回放历史轨迹、设置安全区、接收安全告警。
详见 [../docs/detailed-design/app.md](../docs/detailed-design/app.md)。

## 核心页面（MVP）

地图首页（主屏）、宠物列表、设备绑定、轨迹回放、安全区设置、
告警列表、寻宠模式入口。

## UX 原则

- 地图优先，打开即见宠物位置。
- 始终展示最后更新时间、定位来源与精度，不隐藏不确定性。
- 空状态明确：无宠物 / 无设备 / 暂无定位 / 设备离线。
- 寻宠模式必须提示耗电。

## 实时事件

订阅 `location.updated` `alert.created` `device.status_updated`
`device.battery_updated`；实时断开时降级为轮询最新位置。

## 待定（Phase 0）

- [ ] App 技术栈（技术方案建议 Flutter 双端）
- [ ] 地图 SDK（国内高德/腾讯，海外 Mapbox/Google）
- [ ] 登录方式（MVP 可用 demo 会话）
