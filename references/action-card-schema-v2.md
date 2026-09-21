# 动作卡 Schema v2 · 完整规范

> 本文件是动作卡的结构化字段契约（P0-2 落地）。每个动作卡必须符合本 Schema；字段缺失视为不合格。
> 用途：① 统一「动作设计 Skill」输出与「8 方向 / 16 帧生成器」输入的字段对齐；② 供校验脚本与下游引擎消费。

---

## 一、字段清单

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `action_id` | string | ✅ | 动作唯一 ID，命名规范见分类框架 8.1 |
| `module` | string | ✅ | 所属模块：A-O（idle/locomotion/attack/defense/hit/skill/interaction/death/showoff/cinematic/combo/environment/status/boss/gameplay）|
| `priority` | string | ✅ | P0 / P1 / P2 / P3 |
| `loop_policy` | string | ✅ | `loop` / `one-shot` / `one-shot-freeze-last`（末帧冻结为尸体/停留贴图）|
| `frame_count` | int | ✅ | 总帧数（下游默认 16）|
| `frame_rate` | int | ✅ | 帧率 fps（下游默认 12）|
| `canvas_size` | [int, int] | ✅ | 单帧画布像素 [w, h] |
| `view_angle` | string | ✅ | 视角：top-down-45 / top-down-90 / side-2.5d / ortho-8dir |
| `key_poses` | list | ✅ | 5 帧关键姿势，每项含 frame / height / pose |
| `height` | string | ✅ | 每帧高度节奏：low / mid / high（构成 height_curve）|
| `consistency_locks` | object | ✅ | 一致性硬约束（见下节）|
| `transitions` | object | ⭕ | 状态机衔接（loop 动作可省略，战斗动作必填）|
| `hit_frame` | int | ⭕ | 命中判定帧（attack / skill 必填）|
| `motion_trail` | object | ⭕ | 特效拖尾；无则 `none` |
| `prompt` | string | ✅ | AI 出图 Prompt，由字段自动组装 |

---

## 二、一致性硬约束（consistency_locks）

> ★ v2 核心：这些字段**必须逐字写入 prompt**，是消除镜像/换手/身份漂移的关键。

| 字段 | 来源 | 说明 | 无此特征时 |
|---|---|---|---|
| `identity_anchor` | 输入清单字段 1-6 | 身份锚：职业/性格/体型/武器/阵营 一句话 | 必填，不可省略 |
| `asymmetry_lock` | 输入清单字段 16 | 不对称特征锁：描述不可镜像的特征及所在侧 | 写 `none` |
| `weapon_hand_lock` | 输入清单字段 4 | 武器锁：武器数量 + 持手 + 位置全程不变 | 必填（含"徒手"）|
| `palette_lock` | 输入清单字段 15 | 配色锁：主色/辅色/强调色 十六进制 | 必填 |
| `direction_hint` | 分类框架 7.3 | 逐向可见特征表（8 行） | 8 向动作必填 |

### 组装规则

1. `identity_anchor` + `weapon_hand_lock` + `palette_lock` 逐字拼接进 prompt 开头。
2. `asymmetry_lock` 逐字拼接进 prompt 中段；同时**禁止** prompt 出现"镜像/对称复制"等词。
3. `direction_hint` 拆解为当前方向的单行描述，拼接进 prompt 尾段。

---

## 三、YAML 模板（完整）

```yaml
action_card_v2:
  action_id: atk_chain_02
  module: combo
  priority: P0
  loop_policy: one-shot
  frame_count: 16
  frame_rate: 12
  canvas_size: [512, 512]
  view_angle: top-down-45

  key_poses:
    - frame: 1   height: mid  pose: "收刀预备，重心后压"
    - frame: 4   height: low  pose: "扭腰蓄力，武器最低"
    - frame: 8   height: high pose: "上挑命中，武器最高"    # hit_frame
    - frame: 12  height: mid  pose: "收势回摆"
    - frame: 16  height: mid  pose: "接下一段起手姿态"

  consistency_locks:
    identity_anchor: "暗夜刺客织羽·女性·精瘦·双匕首·左正握右反握·正派"
    asymmetry_lock: "右臂深红异化爪套永远在角色右侧，禁止镜像翻转"
    weapon_hand_lock: "仅双手各持一把匕首，数量与持手全程不可变"
    palette_lock: "#2A3B8F / #C8CBD0 / #B8863A"
    direction_hint:
      S:  "正面；右臂红爪在画面右侧可见"
      E:  "右侧全身；红爪朝前可见"
      NE: "右后方 45°；仅露右肩红爪"
      N:  "背面；红爪不可见"
      NW: "左后方 45°；仅露右肩红爪"
      W:  "左侧全身；红爪被身体遮挡"
      SW: "左前方 45°；红爪在画面右侧"
      SE: "右前方 45°；红爪在画面右侧"

  transitions:
    can_cancel_to: [dodge, atk_chain_03]
    interruptible: true
    blend_time: 2
    hit_frame: 8

  motion_trail:
    frames: [7, 8, 9]
    color: "#8FD8FF"
    style: "淡青色弧形剑气，宽 4px 渐变到 1px"

  prompt: "由上述字段自动组装的 AI 出图 Prompt，禁止出现'镜像'字样，必须含身份锚与风格锁"
```

---

## 四、JSON Schema（供校验与引擎消费）

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ActionCardV2",
  "type": "object",
  "required": ["action_id", "module", "priority", "loop_policy", "frame_count", "frame_rate", "canvas_size", "view_angle", "key_poses", "consistency_locks", "prompt"],
  "properties": {
    "action_id": { "type": "string" },
    "module": { "type": "string", "enum": ["idle", "locomotion", "attack", "defense", "hit", "skill", "interaction", "death", "showoff", "cinematic", "combo", "environment", "status", "boss", "gameplay"] },
    "priority": { "type": "string", "enum": ["P0", "P1", "P2", "P3"] },
    "loop_policy": { "type": "string", "enum": ["loop", "one-shot", "one-shot-freeze-last"] },
    "frame_count": { "type": "integer", "minimum": 1 },
    "frame_rate": { "type": "integer", "minimum": 1 },
    "canvas_size": { "type": "array", "items": { "type": "integer" }, "minItems": 2, "maxItems": 2 },
    "view_angle": { "type": "string", "enum": ["top-down-45", "top-down-90", "side-2.5d", "ortho-8dir"] },
    "key_poses": {
      "type": "array",
      "minItems": 5,
      "items": {
        "type": "object",
        "required": ["frame", "height", "pose"],
        "properties": {
          "frame": { "type": "integer" },
          "height": { "type": "string", "enum": ["low", "mid", "high"] },
          "pose": { "type": "string" }
        }
      }
    },
    "consistency_locks": {
      "type": "object",
      "required": ["identity_anchor", "asymmetry_lock", "weapon_hand_lock", "palette_lock"],
      "properties": {
        "identity_anchor": { "type": "string" },
        "asymmetry_lock": { "type": "string" },
        "weapon_hand_lock": { "type": "string" },
        "palette_lock": { "type": "string" },
        "direction_hint": { "type": "object" }
      }
    },
    "transitions": {
      "type": "object",
      "properties": {
        "can_cancel_to": { "type": "array", "items": { "type": "string" } },
        "interruptible": { "type": "boolean" },
        "blend_time": { "type": "integer" },
        "hit_frame": { "type": "integer" }
      }
    },
    "motion_trail": {
      "type": ["object", "null"],
      "properties": {
        "frames": { "type": "array", "items": { "type": "integer" } },
        "color": { "type": "string" },
        "style": { "type": "string" }
      }
    },
    "prompt": { "type": "string" }
  }
}
```

---

## 五、字段完备性自检（交付前逐卡核对）

- [ ] 必填字段 10 项齐全（action_id / module / priority / loop_policy / frame_count / frame_rate / canvas_size / view_angle / key_poses / prompt）
- [ ] key_poses 恰好 5 帧且帧号递增（F1/F4/F8/F12/F16 或等比分布）
- [ ] attack / skill 动作声明了 hit_frame 与 transitions
- [ ] consistency_locks 四锁齐全，无 `none` 的锁已逐字进 prompt
- [ ] prompt 中无"镜像/对称复制"字样
- [ ] 8 向动作有完整 direction_hint（8 行）
