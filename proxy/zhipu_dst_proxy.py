# -*- coding: utf-8 -*-
"""Local Zhipu AI proxy for a private Don't Starve Together NPC talk mod."""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from contextlib import suppress
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
DEFAULT_MODEL = "glm-5.1"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765

MIN_TALK_CHARS = int(os.environ.get("DST_AI_MIN_TALK_CHARS", "10"))
MAX_TALK_CHARS = int(os.environ.get("DST_AI_MAX_TALK_CHARS", "20"))
if MIN_TALK_CHARS > MAX_TALK_CHARS:
    MIN_TALK_CHARS = MAX_TALK_CHARS
REQUEST_TIMEOUT_SECONDS = float(os.environ.get("DST_AI_REQUEST_TIMEOUT", "10"))
CACHE_SECONDS = float(os.environ.get("DST_AI_CACHE_SECONDS", "120"))
MIN_API_INTERVAL_SECONDS = float(os.environ.get("DST_AI_MIN_API_INTERVAL", "4"))
GENERATION_ATTEMPTS = max(1, int(os.environ.get("DST_AI_GENERATION_ATTEMPTS", "2")))
RECENT_LINES_PER_PREFAB = max(1, int(os.environ.get("DST_AI_RECENT_LINES_PER_PREFAB", "4")))

LEGACY_NPC_TO_PROFILE = {
    "pigman": ("intelligent", "pigman"),
    "bunnyman": ("intelligent", "bunnyman"),
    "rabbit": ("animal", "rabbit"),
}

PREFAB_NAMES = {
    "pigman": "猪人",
    "pigguard": "猪人守卫",
    "bunnyman": "兔人",
    "merm": "鱼人",
    "mermguard": "鱼人守卫",
    "walrus": "海象",
    "little_walrus": "小海象",
    "rocky": "石虾",
    "rabbit": "兔子",
    "mole": "鼹鼠",
    "catcoon": "浣猫",
    "beefalo": "皮弗娄牛",
    "babybeefalo": "小皮弗娄牛",
    "koalefant_summer": "考拉象",
    "koalefant_winter": "冬考拉象",
    "lightninggoat": "伏特羊",
    "grassgekko": "草蜥蜴",
    "perd": "火鸡",
    "tallbird": "高脚鸟",
    "smallbird": "小高脚鸟",
    "teenbird": "青年高脚鸟",
    "penguin": "企鸥",
    "crow": "乌鸦",
    "robin": "红雀",
    "robin_winter": "雪雀",
    "canary": "金丝雀",
    "puffin": "海鹦鹉",
    "butterfly": "蝴蝶",
    "lightflier": "球状光虫",
    "lightcrab": "发光蟹",
    "spider": "蜘蛛",
    "spider_warrior": "蜘蛛战士",
    "spider_dropper": "穴居悬蛛",
    "spider_hider": "洞穴蜘蛛",
    "spider_spitter": "喷吐蜘蛛",
    "spider_water": "水中木蜘蛛",
    "hound": "猎犬",
    "firehound": "红猎犬",
    "icehound": "蓝猎犬",
    "frog": "青蛙",
    "mosquito": "蚊子",
    "bee": "蜜蜂",
    "killerbee": "杀人蜂",
    "bat": "蝙蝠",
    "ruins_bat": "遗迹蝙蝠",
    "molebat": "裸鼹鼠蝙蝠",
    "slurper": "啜食者",
    "slurtle": "蛞蝓龟",
    "snurtle": "蜗牛龟",
    "worm": "深渊蠕虫",
    "tentacle": "触手",
    "birchnutdrake": "桦栗果精",
    "krampus": "坎普斯",
    "monkey": "穴居猴",
    "knight": "发条骑士",
    "bishop": "发条主教",
    "rook": "发条战车",
    "knight_nightmare": "梦魇发条骑士",
    "bishop_nightmare": "梦魇发条主教",
    "rook_nightmare": "梦魇发条战车",
    "cookiecutter": "饼干切割机",
    "squid": "鱿鱼",
    "gnarwail": "一角鲸",
    "shark": "岩石大白鲨",
    "wobster_sheller": "龙虾",
    "wobster_sheller_land": "陆地龙虾",
    "wobster_moonglass": "月光龙虾",
    "wobster_moonglass_land": "陆地月光龙虾",
}

NPC_PROFILES = {
    "intelligent": {
        "name": "普通智慧生物",
        "style": "像饥荒联机版里的普通智慧 NPC，说话短促、有生存感；用低调暗示制造细思极恐的异常感。",
        "fallback": [
            "刚才多了一个陌生影子。",
            "有人正在学我说话呀。",
            "门外脚步一直停在原地。",
            "别回头，它已经认人。",
        ],
    },
    "animal": {
        "name": "普通动物",
        "style": "胆小、机警、靠本能行动；像察觉到看不见的东西，台词有细思极恐的错位感。",
        "fallback": [
            "洞口刚才自己慢慢合上。",
            "草里有东西同我呼吸。",
            "我的影子慢了整一步。",
            "它闻起来像明天的土。",
        ],
    },
    "bird": {
        "name": "普通鸟类",
        "style": "轻快但过分警觉，关注树梢、风向和影子；用短句暗示天空里不该存在的注视。",
        "fallback": [
            "树梢忽然少了一阵风。",
            "羽毛下面有谁在数数。",
            "地上的影子已经先飞走。",
            "天上的眼睛一直没眨。",
        ],
    },
    "insect": {
        "name": "普通昆虫",
        "style": "小巧、忙碌、神经质，关注花粉、翅膀和微小震动；像听见地下或花里传来的低语。",
        "fallback": [
            "花粉里面藏着低语声。",
            "翅膀听见地下轻轻敲门。",
            "甜味从空壳里面出来。",
            "草尖正在数我的细腿。",
        ],
    },
    "monster": {
        "name": "普通怪物",
        "style": "危险、饥饿、粗野但不是 Boss；恐怖感来自影子、名字、空地和异常呼吸，不要血腥。",
        "fallback": [
            "黑夜刚才叫了我的名。",
            "影子比牙齿更早饿了。",
            "它躲在我的眼睛后面。",
            "空地中间多了一口呼吸。",
        ],
    },
    "spider": {
        "name": "蜘蛛",
        "style": "黏糊、群居、爱护蛛网和巢穴；让蛛丝像记录了不该存在的低语和脚印。",
        "fallback": [
            "网里吊着明天的影子。",
            "有东西正在学会抖网。",
            "巢外脚印自己走回来。",
            "丝线上挂着细小低语。",
        ],
    },
    "hound": {
        "name": "猎犬",
        "style": "凶、急、靠嗅觉追踪；强调没有主人的脚印、伪装成自己的叫声和先来的影子。",
        "fallback": [
            "脚印闻起来没有主人。",
            "远处叫声正在装成我。",
            "牙缝里面吹出旧名字。",
            "猎物的影子先跑过来。",
        ],
    },
    "cave_monster": {
        "name": "洞穴怪物",
        "style": "阴暗、潮湿、靠声音和气味行动；让回声、洞壁和黑暗表现出像活物一样的异常。",
        "fallback": [
            "洞壁正在慢慢学呼吸。",
            "回声比声音更先回来。",
            "石头下面有人轻轻笑。",
            "黑暗里面多了一盏眼。",
        ],
    },
    "clockwork": {
        "name": "发条生物",
        "style": "机械、齿轮、巡逻、损坏、冷冰冰但短促；恐怖感来自停机后仍在执行的旧指令。",
        "fallback": [
            "齿轮里面卡着旧心跳。",
            "巡逻路线多出空白一圈。",
            "错误目标正在自己靠近。",
            "停机以后仍有人转动。",
        ],
    },
    "ocean": {
        "name": "海洋生物",
        "style": "湿漉漉、神秘、受潮汐影响；用水下影子、泡泡里的眼睛和学人说话的浪声制造不安。",
        "fallback": [
            "潮水退后留下湿脚印。",
            "泡泡里面有人在眨眼。",
            "水下影子比小船还长。",
            "浪声正在学会人的话。",
        ],
    },
}

cache: dict[tuple[str, str, str, str, str, str, str], tuple[float, str]] = {}
recent_lines: dict[tuple[str, str], list[str]] = {}
last_api_call_at = 0.0
last_error: str | None = None


class LocalProxyServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def proxy_log(message: str) -> None:
    stream = getattr(sys, "stdout", None)
    if stream is None:
        return

    with suppress(Exception):
        print(message, flush=True)


def json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    with suppress(BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)


def get_model() -> str:
    return DEFAULT_MODEL


def get_api_key() -> str | None:
    return os.environ.get("ZHIPU_API_KEY")


def supports_thinking(model: str) -> bool:
    return model.startswith(("glm-5", "glm-4.7", "glm-4.6", "glm-4.5"))


def resolve_profile(npc: str, prefab: str) -> tuple[str, str]:
    npc = npc or "animal"
    prefab = prefab or "unknown"

    if npc in LEGACY_NPC_TO_PROFILE and prefab == "unknown":
        npc, prefab = LEGACY_NPC_TO_PROFILE[npc]
    elif npc in LEGACY_NPC_TO_PROFILE:
        npc = LEGACY_NPC_TO_PROFILE[npc][0]

    if npc not in NPC_PROFILES:
        npc = "animal"

    return npc, prefab


def recent_key(npc: str, prefab: str) -> tuple[str, str]:
    npc, prefab = resolve_profile(npc, prefab)
    return npc, prefab


def is_recent_line(npc: str, prefab: str, text: str) -> bool:
    return text in recent_lines.get(recent_key(npc, prefab), [])


def remember_line(npc: str, prefab: str, text: str) -> None:
    if not text:
        return

    key = recent_key(npc, prefab)
    lines = recent_lines.setdefault(key, [])
    if text in lines:
        lines.remove(text)
    lines.append(text)
    del lines[:-RECENT_LINES_PER_PREFAB]


def choose_non_recent_line(lines: list[str], npc: str, prefab: str) -> str:
    key = recent_key(npc, prefab)
    recent = recent_lines.get(key, [])
    candidates = [line for line in lines if line not in recent]
    if not candidates and recent:
        candidates = [line for line in lines if line != recent[-1]]
    return random.choice(candidates or lines)


def clean_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""

    text = value.strip()
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"^.{1,12}\s*[:：]\s*", "", text)
    text = re.sub(r"^(猪人|兔人|兔子|NPC|台词|对白)\s*[:：]\s*", "", text, flags=re.I)
    text = text.strip(" \"'“”‘’`")

    text = text.strip(" \"'“”‘’")

    if not text:
        return ""

    if len(text) > MAX_TALK_CHARS:
        text = text[:MAX_TALK_CHARS]

    if len(text) < MIN_TALK_CHARS:
        return ""

    return text


def fallback_line(npc: str, prefab: str = "unknown") -> str:
    npc, prefab = resolve_profile(npc, prefab)
    profile = NPC_PROFILES.get(npc, NPC_PROFILES["animal"])
    text = choose_non_recent_line(profile["fallback"], npc, prefab)
    remember_line(npc, prefab, text)
    return text


def build_messages(npc: str, prefab: str, event: str, season: str, phase: str, day: str, cave: str) -> list[dict[str, str]]:
    npc, prefab = resolve_profile(npc, prefab)
    profile = NPC_PROFILES.get(npc, NPC_PROFILES["animal"])
    role_name = PREFAB_NAMES.get(prefab, profile["name"])
    place = "洞穴" if cave == "1" else "地面"

    return [
        {
            "role": "system",
            "content": (
                "你为电子游戏《饥荒联机版》的非玩家生物生成短台词。"
                "只输出一句角色台词，不要解释，不要加引号，不要写角色名。"
                f"必须不少于{MIN_TALK_CHARS}个且不超过{MAX_TALK_CHARS}个中文字符。"
                "不要生成系统提示、现实世界说明、玩家指令或长段对白。"
                "整体风格尽量细思极恐：暗示异常、错位、被注视、回声、重复、失踪感；不要血腥直白。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"角色：{role_name}。"
                f"分类：{profile['name']}。"
                f"风格：{profile['style']}"
                f"事件：{event}。季节：{season}。时间段：{phase}。"
                f"天数：{day}。地点：{place}。"
                "生成一句随机、自然、细思极恐且符合饥荒联机版气氛的中文短句。"
            ),
        },
    ]


def read_http_error(error: urllib.error.HTTPError) -> str:
    try:
        return error.read().decode("utf-8", errors="replace")
    except Exception:
        return ""


def call_zhipu(messages: list[dict[str, str]]) -> str:
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("ZHIPU_API_KEY is not set")

    model = get_model()
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 1.0,
        "max_tokens": 1024,
        "stream": False,
        "response_format": {"type": "text"},
    }
    if supports_thinking(model):
        payload["thinking"] = {"type": "disabled"}

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = read_http_error(exc)
        if detail:
            raise RuntimeError(f"Zhipu HTTP {exc.code}: {detail}") from exc
        raise RuntimeError(f"Zhipu HTTP {exc.code}") from exc

    return response_data["choices"][0]["message"]["content"]


def generate_line(
    npc: str,
    prefab: str,
    entity: str,
    event: str,
    season: str,
    phase: str,
    day: str,
    cave: str,
) -> tuple[str, str]:
    global last_api_call_at, last_error

    npc, prefab = resolve_profile(npc, prefab)
    now = time.monotonic()
    key = (npc, prefab, entity or "unknown", event, season, phase, cave)
    cached = cache.get(key)
    if cached and now - cached[0] <= CACHE_SECONDS and not is_recent_line(npc, prefab, cached[1]):
        remember_line(npc, prefab, cached[1])
        return cached[1], "cache"

    if now - last_api_call_at < MIN_API_INTERVAL_SECONDS:
        return fallback_line(npc, prefab), "fallback_rate_limited"

    try:
        last_api_call_at = now
        text = ""
        for _ in range(GENERATION_ATTEMPTS):
            raw_text = call_zhipu(build_messages(npc, prefab, event, season, phase, day, cave))
            text = clean_text(raw_text)
            if text and not is_recent_line(npc, prefab, text):
                break
            text = ""
        if not text:
            raise RuntimeError("model output empty, duplicate, or outside length range")

        last_error = None
        cache[key] = (now, text)
        remember_line(npc, prefab, text)
        return text, "zhipu"
    except (RuntimeError, KeyError, IndexError, json.JSONDecodeError, urllib.error.URLError) as exc:
        last_error = f"{type(exc).__name__}: {exc}"
        proxy_log(f"[zhipu_dst_proxy] fallback for {npc}/{prefab}: {last_error}")
        return fallback_line(npc, prefab), "fallback_error"


def health_payload() -> dict[str, Any]:
    return {
        "status": "ok",
        "model": get_model(),
        "has_api_key": bool(get_api_key()),
        "min_talk_chars": MIN_TALK_CHARS,
        "max_talk_chars": MAX_TALK_CHARS,
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        message = fmt % args
        if message.startswith("Request timed out:"):
            return
        proxy_log(f"[zhipu_dst_proxy] {self.address_string()} - {message}")

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)

        query = urllib.parse.parse_qs(parsed.query)
        debug = query.get("debug", ["0"])[0] == "1"

        if parsed.path == "/health":
            payload = health_payload()
            if debug:
                payload["last_error"] = last_error
            json_response(self, 200, payload)
            return

        if parsed.path != "/say":
            json_response(self, 404, {"error": "not_found"})
            return

        npc = query.get("npc", ["animal"])[0]
        prefab = query.get("prefab", ["unknown"])[0]
        entity = query.get("entity", ["unknown"])[0]
        event = query.get("event", ["idle"])[0]
        season = query.get("season", ["unknown"])[0]
        phase = query.get("phase", ["unknown"])[0]
        day = query.get("day", ["0"])[0]
        cave = query.get("cave", ["0"])[0]

        text, source = generate_line(npc, prefab, entity, event, season, phase, day, cave)
        payload = {"text": text, "source": source}
        if debug:
            payload["last_error"] = last_error
        json_response(self, 200, payload)


def create_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    return LocalProxyServer((host, port), Handler)


def run_server(host: str, port: int) -> None:
    server = create_server(host, port)
    proxy_log(f"[zhipu_dst_proxy] listening on http://{host}:{port}")
    proxy_log("[zhipu_dst_proxy] health: /health, DST endpoint: /say")
    try:
        server.serve_forever()
    finally:
        server.server_close()


def self_test() -> None:
    text, source = generate_line("intelligent", "pigman", "self-test", "idle", "winter", "dusk", "12", "0")
    print(json.dumps({"health": health_payload(), "sample": {"text": text, "source": source}}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Local Zhipu AI proxy for DST NPC talk.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", default=int(os.environ.get("DST_AI_PROXY_PORT", str(DEFAULT_PORT))), type=int)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return

    run_server(args.host, args.port)


if __name__ == "__main__":
    main()
