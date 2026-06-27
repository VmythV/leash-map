# simulator — Device Simulator

在真实硬件就绪前，模拟宠物定位器行为，驱动云端与 App 的端到端联调。
详见 [../docs/detailed-design/device-simulator.md](../docs/detailed-design/device-simulator.md)。

## 能力（MVP）

固定路线回放、随机游走、电量消耗、上线/离线/重连、围栏离区、
低精度漂移点、离线缓存与批量补传、寻宠高频上报。

## CLI 草案

```bash
leashmap-sim \
  --device-id dev_mvp_001 \
  --endpoint http://localhost:8080 \
  --token dev-token \
  --route fixtures/park-route.json \
  --interval 5s \
  --battery 85 \
  --mode normal   # normal | lost | offline | drift | low_battery | exit_zone
```

## 路线 fixture

存于 `fixtures/`，格式见详细设计文档第 4 节。

## 待定（Phase 0）

- [ ] 实现语言（建议与团队最熟悉的脚本/语言一致）
- [ ] 上报协议版本与字段（需与 `server/ingest` 对齐）
