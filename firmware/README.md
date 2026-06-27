# firmware — Device Firmware

设备固件：采集定位/运动/电量，按状态切换上报频率，离线缓存补传，支持 OTA。
详见 [../docs/detailed-design/firmware.md](../docs/detailed-design/firmware.md)。

## 状态机

```text
BOOT -> PROVISIONING -> IDLE -> TRACKING -> GUARD -> LOST
        LOW_BATTERY / OTA / FAULT_RECOVER
```

## 模块边界

modem（4G Cat 1 bis）、GNSS、IMU、battery、本地存储队列、
payload 序列化、上报重试、串口日志、配置存储。

## 上报

MQTT over TLS 优先，HTTPS 兜底；消息建议 Protobuf / CBOR。

## 接入顺序

软件闭环（`simulator` + `server` + `app`）跑通后，再用开发板接入真实数据：
GNSS -> Cat 1 bis -> IMU -> 电量。

## 待定（Phase 0）

- [ ] 固件工具链（MCU 选型：STM32 / nRF52）
- [ ] RTOS / 裸机
- [ ] 上报协议与 `server/ingest` 对齐
