# firmware — Device Firmware

设备固件。本阶段交付**纯逻辑骨架**：状态机 + 上报协议封装 + 离线缓存，
全部硬件无关、可在宿主机单元测试，为后续接开发板做准备。
详细设计见 [../docs/detailed-design/firmware.md](../docs/detailed-design/firmware.md)，
上报协议契约见 [../docs/api/device-protocol.md](../docs/api/device-protocol.md)。

## 技术栈（Phase 0 暂定）

- **C（C11）**，零外部依赖，宿主机用 clang 编译运行单测。
- 选 C 的原因：STM32/nRF52 厂商 SDK 以 C 为主，最贴近真实固件；本机自带 clang，无需新工具链。
- 可回退方案：Rust + embassy/RTIC（`cargo test` 同样适合纯逻辑单测）。MCU 选型确定后再定。

## 构建与测试

```bash
cd firmware
make test     # 用 clang 编译 src/ + tests/，运行宿主单测
make clean
```

当前为**纯逻辑核心**，不含 MCU 工程（启动文件、HAL、链接脚本）。接开发板时再加
具体 MCU 的构建工程，复用此处的 `src/` 逻辑。

## 代码布局

```text
include/
  lm_config.h     设备配置（各模式上报间隔、低电阈值、蜂鸣/LED）
  lm_state.h      状态机：9 态 + 事件 + 纯转移函数 + 每态上报间隔
  lm_command.h    下行命令模型（set_mode/set_interval/locate_now/ota）
  lm_drivers.h    硬件驱动抽象（HAL vtable）：gnss/modem/imu/battery/clock/log
  lm_protocol.h   上行序列化 + command_ack + 命令解析
  lm_cache.h      离线缓存环形缓冲（定长，无堆）
  lm_app.h        应用编排器（基于 HAL 的纯逻辑）
src/
  lm_state.c      状态转移 + 间隔策略 + 状态名/模式名映射
  lm_protocol.c   snprintf JSON 序列化 + 极简命令解析（无 JSON 库）
  lm_cache.c      环形缓冲：push 满则丢最旧、批量 drain
  lm_app.c        一次 tick：感知→采集→上报/缓存→重连补传→应用下行命令+ack
tests/
  lm_test.h       极简断言框架（无依赖）
  test_state.c    状态转移、优先级覆盖、间隔
  test_protocol.c JSON 字段/可选字段/截断
  test_cache.c    FIFO、溢出丢最旧、部分 drain
  test_command.c  命令解析（set_mode/set_interval/缺字段）
  test_app.c      mock 驱动：上报/无定位跳过/离线缓存+补传/命令应用+ack
  test_main.c     测试入口
Makefile          host 构建 + 运行测试
```

## 驱动抽象与编排（mock 可测）

业务逻辑只依赖 `lm_drivers.h` 的 vtable（函数指针 + ctx），同一套 `lm_app` 主循环
既能在 MCU 上跑真实驱动，也能在宿主用 mock 驱动单测：

```text
lm_app_tick():
  imu_read_motion → 状态机事件(MOTION/STILL)
  battery_read    → 低电事件
  gnss_read       → 有定位才采集（否则 log GNSS_NO_FIX）
  modem_connect   → 失败则入离线缓存
  modem_publish   → 成功则补传缓存；响应带命令则 apply + 发 command_ack
```

下行命令：`modem_publish` 的响应里带命令（HTTP body / MQTT），由 `lm_protocol_parse_command`
解析为 `lm_command_t`，`lm_app_apply_command` 应用（如 set_mode lost → 进 LOST），
再回 `command_ack` 事件。与服务端 `docs/api/device-protocol.md §8` 闭环。

## 状态机（docs/detailed-design/firmware.md §4）

```text
BOOT -> PROVISIONING -> IDLE <-> TRACKING <-> GUARD
高优先级事件（任意态生效）：FAULT->FAULT_RECOVER，OTA_START->OTA，
                          BATTERY_LOW->LOW_BATTERY，LOST_ON->LOST
恢复：LOST_OFF/BATTERY_OK/OTA_DONE/FAULT_RECOVERED -> TRACKING/IDLE
```

每态上报间隔（默认值，可配置）：idle 1800s、tracking 120s、guard 15s、
lost 7s、low_battery 1800s；boot/provisioning/ota/fault_recover 不周期上报。

## 协议对齐说明

`lm_protocol_*` 输出字段以 [docs/api/device-protocol.md](../docs/api/device-protocol.md)
为准（心跳用 `mode` + `network` 对象）。`firmware.md` §6 早于 API 契约，其
`state`/扁平 `rssi` 写法以本目录与 device-protocol.md 为准。

## 接开发板 TODO

驱动**接口**已定义（`lm_drivers.h`），接板即实现这些回调，业务逻辑不变：

- [ ] 选定 MCU 与工具链（STM32CubeIDE / arm-none-eabi-gcc 或 Rust embassy）
- [ ] 实现 `lm_drivers_t` 回调：GNSS、modem(Cat 1 bis)、IMU、battery、clock、log
- [ ] network/：MQTT over TLS 上报（`modem_publish` 实现），HTTPS 兜底；解析下行命令
- [ ] storage/：把 `lm_cache` 落到掉电保持存储；配置持久化
- [ ] ota/：固件包校验与回滚
- [ ] 把 `lm_app_tick` 接入主循环/RTOS 任务（按 `lm_reporting_interval_s` 调度）
