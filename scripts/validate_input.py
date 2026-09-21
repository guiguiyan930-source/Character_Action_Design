#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
角色动作设计 Skill v2 · 输入校验脚本（P1-3 落地）

用途：校验「角色动作设计输入清单 v2」的 YAML 输入，在进入动作设计流程前拦截错误。

校验项：
  1. 必填字段齐全（character 8 项 + game 3 项）
  2. 枚举合法（游戏类型 / 夸张度 1-5 / 方向集合 / 帧数正整数）
  3. 不对称特征声明存在（有特征则必填，无则须显式写 none）

用法：
  python3 validate_input.py <input.yaml>
  python3 validate_input.py --example   # 运行内置示例自检

退出码：0 = 通过；1 = 校验失败；2 = 文件/参数错误
"""

import sys
import re
import argparse

try:
    import yaml
except ImportError:
    print("[ERROR] 缺少 PyYAML，请先安装：pip install pyyaml", file=sys.stderr)
    sys.exit(2)

# ---------- 合法枚举 ----------
VALID_GENRES = {
    "2D横版ACT", "横版ACT", "2D ACT", "side-scroll",
    "俯视角ARPG", "ARPG", "top-down", "等距ARPG",
    "SLG战棋", "战棋", "SRPG",
    "塔防", "TD",
    "卡牌立绘", "卡牌", "立绘",
    "MMO", "MMO社交",
    "解谜探索", "解谜", "探索",
}
VALID_DIRECTIONS = {"N", "NE", "E", "SE", "S", "SW", "W", "NW"}
VALID_CAMERAS = {"45°俯视", "45度俯视", "top-down-45", "正俯视90°", "正俯视", "top-down-90",
                 "2.5D侧视", "2.5D", "side-2.5d", "正交8向", "ortho-8dir"}

REQUIRED_CHARACTER = ["identity", "personality", "body_type", "weapon_main", "combat_style", "faction_vibe"]
REQUIRED_GAME = ["genre", "camera", "exaggeration"]


def _norm(s):
    """归一化：去空格、全角转半角括号，便于枚举匹配"""
    if s is None:
        return ""
    s = str(s).strip().replace("（", "(").replace("）", ")")
    return s


def validate(data):
    """返回 (ok, errors[])"""
    errors = []

    if not isinstance(data, dict):
        return False, ["输入不是 YAML 对象"]

    char = data.get("character") or {}
    game = data.get("game") or {}
    tech = data.get("tech") or {}

    # 1. 必填字段
    for f in REQUIRED_CHARACTER:
        if not char.get(f):
            errors.append(f"character.{f} 缺失")
    for f in REQUIRED_GAME:
        if game.get(f) is None or (isinstance(game.get(f), str) and not game[f].strip()):
            errors.append(f"game.{f} 缺失")

    # 2. 性格关键词 2-4 个
    personality = char.get("personality")
    if personality is not None:
        if isinstance(personality, list):
            if not (2 <= len([p for p in personality if p]) <= 4):
                errors.append("character.personality 需 2-4 个关键词")
        elif isinstance(personality, str):
            if not (2 <= len([p for p in re.split(r"[、,，]", personality) if p]) <= 4):
                errors.append("character.personality 需 2-4 个关键词")

    # 3. 不对称特征声明（有则必填）
    asym = char.get("asymmetry")
    if asym is None:
        errors.append("character.asymmetry 缺失（无不对称特征请写 none）")

    # 4. 游戏类型枚举
    genre = _norm(game.get("genre"))
    if genre and genre not in VALID_GENRES:
        errors.append(f"game.genre 不在支持列表：{genre}")

    # 5. 镜头视角枚举
    camera = _norm(game.get("camera"))
    if camera and camera not in VALID_CAMERAS:
        errors.append(f"game.camera 不在支持列表：{camera}")

    # 6. 夸张度 1-5
    ex = game.get("exaggeration")
    if ex is not None:
        try:
            if not (1 <= int(ex) <= 5):
                errors.append(f"game.exaggeration 需在 1-5 之间，当前 {ex}")
        except (TypeError, ValueError):
            errors.append(f"game.exaggeration 需为整数 1-5，当前 {ex}")

    # 7. 方向集合
    directions = tech.get("directions")
    if directions is not None:
        bad = [d for d in directions if d not in VALID_DIRECTIONS]
        if bad:
            errors.append(f"tech.directions 含非法方向：{bad}")

    # 8. 帧数 / 帧率正整数
    for f in ("frames_per_dir", "frame_rate"):
        v = tech.get(f)
        if v is not None:
            try:
                if int(v) <= 0:
                    errors.append(f"tech.{f} 需为正整数，当前 {v}")
            except (TypeError, ValueError):
                errors.append(f"tech.{f} 需为正整数，当前 {v}")

    return (len(errors) == 0), errors


def _example():
    return {
        "character": {
            "name": "织羽",
            "identity": "暗夜刺客",
            "personality": ["冷静", "机敏"],
            "body_type": "7头身 精瘦",
            "weapon_main": "双匕首",
            "weapon_sub": "烟雾弹",
            "combat_style": "近战突进",
            "faction_vibe": "正派光明",
            "asymmetry": "none",
        },
        "game": {
            "genre": "横版ACT",
            "camera": "2.5D侧视",
            "exaggeration": 3,
        },
        "signature": {
            "signature_pose": "抽刀入鞘甩袖",
            "gait": "猫步",
            "dynamic_parts": ["长披风"],
            "vfx": ["烟雾"],
            "color_palette": ["#2A3B8F", "#C8CBD0"],
        },
        "tech": {
            "canvas": "512x512",
            "directions": ["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
            "frames_per_dir": 16,
            "frame_rate": 12,
            "transparent_bg": True,
            "style_refs": [],
            "action_list": [],
        },
    }


def main():
    parser = argparse.ArgumentParser(description="角色动作设计 Skill v2 输入校验")
    parser.add_argument("file", nargs="?", help="输入 YAML 文件路径")
    parser.add_argument("--example", action="store_true", help="运行内置示例自检")
    args = parser.parse_args()

    if args.example:
        ok, errors = validate(_example())
        if ok:
            print("[PASS] 内置示例校验通过")
            return 0
        print("[FAIL] 内置示例校验失败（内置示例应始终通过，请检查脚本）")
        for e in errors:
            print(f"  - {e}")
        return 1

    if not args.file:
        parser.print_help()
        return 2

    try:
        with open(args.file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"[ERROR] 文件不存在：{args.file}", file=sys.stderr)
        return 2
    except yaml.YAMLError as e:
        print(f"[ERROR] YAML 解析失败：{e}", file=sys.stderr)
        return 2

    ok, errors = validate(data)
    if ok:
        print(f"[PASS] {args.file} 校验通过，可进入动作设计流程")
        return 0

    print(f"[FAIL] {args.file} 校验失败，共 {len(errors)} 项：")
    for e in errors:
        print(f"  - {e}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
