"""SQLite storage and seed data for templates, fragments, and history."""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Iterable

DEFAULT_DB_PATH = Path.home() / ".holywater" / "holywater.sqlite3"


SCHEMA = """
CREATE TABLE IF NOT EXISTS templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    style TEXT NOT NULL,
    mood TEXT NOT NULL,
    template TEXT NOT NULL,
    weight REAL NOT NULL DEFAULT 1,
    enabled INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS fragments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    value TEXT NOT NULL,
    style TEXT,
    mood TEXT,
    weight REAL NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS generation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    style TEXT NOT NULL,
    mood TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_templates_lookup
    ON templates (style, mood, enabled);

CREATE INDEX IF NOT EXISTS idx_fragments_lookup
    ON fragments (category, style, mood);

CREATE INDEX IF NOT EXISTS idx_generation_history_recent
    ON generation_history (style, mood, created_at);
"""


TEMPLATES: list[tuple[str, str, str, float, int]] = [
    (
        "genesis",
        "serious",
        "{time_phrase}，{subject}见{water_object}，便说：“{divine_command}。”于是{action}，{result}。",
        1.4,
        1,
    ),
    (
        "genesis",
        "absurd",
        "{time_phrase}，{subject}于{context_scene}看见{water_object}，其上有光，便听见声说：“{divine_command}。”于是{action}，{absurd_result}。",
        1.2,
        1,
    ),
    (
        "psalm",
        "serious",
        "{subject}啊，当于{context_scene}记念{water_object}；因{result}，你的{body_part}也必安稳。",
        1.2,
        1,
    ),
    (
        "psalm",
        "absurd",
        "{subject}啊，愿你的{body_part}不再像{absurd_image}；你当{imperative_action}，并歌唱说：“{divine_command}。”",
        1.1,
        1,
    ),
    (
        "proverb",
        "serious",
        "智慧人见{water_object}便{simple_action}；愚昧人等到{body_part}干涸，才说：“{divine_command}。”",
        1.3,
        1,
    ),
    (
        "proverb",
        "absurd",
        "宁可于{context_scene}饮一口清水，不可让{absurd_image}在你{body_part}上开会。",
        1.0,
        1,
    ),
    (
        "revelation",
        "serious",
        "{time_phrase}，我又看见{water_object}如明亮的河，从杯中出来；有声音说：“{divine_command}。”{result}。",
        1.0,
        1,
    ),
    (
        "revelation",
        "absurd",
        "{time_phrase}，第{omen_number}杯揭开了，{absurd_image}从{context_scene}升起；那声音如众键盘说：“{divine_command}。”于是{action}，{absurd_result}。",
        1.4,
        1,
    ),
    (
        "gospel",
        "serious",
        "{subject}来到{context_scene}，{mentor}对他说：“{divine_command}。”他便{simple_action}，{result}。",
        1.1,
        1,
    ),
    (
        "gospel",
        "absurd",
        "{mentor}见{subject}在{context_scene}里枯坐，就递给他{water_object}，说：“{divine_command}。”众人便稀奇。",
        1.0,
        1,
    ),
    (
        "commandment",
        "serious",
        "你当{imperative_action}，不可藐视{water_object}；这是身在{context_scene}之人也当记念的诫命。",
        1.3,
        1,
    ),
    (
        "commandment",
        "absurd",
        "第一条诫命乃是：{divine_command}。第二条也相仿：不可让{absurd_image}替你管理{body_part}。",
        1.2,
        1,
    ),
    (
        "genesis",
        "serious",
        "起初{context_scene}尚且干燥，{subject}便将{water_object}分别出来，说：“{divine_command}。”{result}。",
        1.1,
        1,
    ),
    (
        "genesis",
        "serious",
        "{time_phrase}，{subject}给{water_object}起名叫{blessing}，便{simple_action}，{parallel_result}。",
        1.0,
        1,
    ),
    (
        "genesis",
        "absurd",
        "起初{absurd_image}空虚混沌，{subject}看见{water_object}是好的，就说：“{divine_command}。”{absurd_result}。",
        1.1,
        1,
    ),
    (
        "psalm",
        "serious",
        "{subject}啊，你的{body_part}若发干，愿{water_object}临近你；当{imperative_action}，{parallel_result}。",
        1.2,
        1,
    ),
    (
        "psalm",
        "serious",
        "我要因{water_object}安静片刻；它使{body_part}回转，也使{context_scene}中的心不至散乱。",
        1.0,
        1,
    ),
    (
        "psalm",
        "absurd",
        "{subject}啊，不要与{absurd_image}同坐；当取{water_object}，使{body_part}脱离{warning}。",
        1.1,
        1,
    ),
    (
        "proverb",
        "serious",
        "谨守{water_object}的，保全{body_part}；迟迟不饮的，必遇见{warning}。",
        1.2,
        1,
    ),
    (
        "proverb",
        "serious",
        "一句{divine_command}，胜过十次空望{context_scene}；一口{water_object}，胜过久等灵感。",
        1.0,
        1,
    ),
    (
        "proverb",
        "absurd",
        "智慧人把{water_object}放在右手边；愚昧人把{absurd_image}当作补水的先知。",
        1.1,
        1,
    ),
    (
        "revelation",
        "serious",
        "我听见{voice}自{context_scene}传来，说：“{divine_command}。”{subject}便{simple_action}，{result}。",
        1.0,
        1,
    ),
    (
        "revelation",
        "absurd",
        "我又看见{omen_number}个提醒立在{context_scene}边，手里拿着{water_object}；{voice}说：“{divine_command}。”",
        1.2,
        1,
    ),
    (
        "revelation",
        "absurd",
        "{time_phrase}，{warning}临到{body_part}，{absurd_image}大声作证；惟有{water_object}仍在发光。",
        1.1,
        1,
    ),
    (
        "gospel",
        "serious",
        "{mentor}看见{subject}疲乏，就说：“把{water_object}给他。”他喝了，{parallel_result}。",
        1.1,
        1,
    ),
    (
        "gospel",
        "serious",
        "{subject}问{mentor}：“我当怎样于{context_scene}不至干涸？”他说：“{divine_command}。”",
        1.0,
        1,
    ),
    (
        "gospel",
        "absurd",
        "{mentor}把{water_object}递给{subject}；{crowd_reaction}，因为{absurd_result}。",
        1.1,
        1,
    ),
    (
        "commandment",
        "serious",
        "凡在{context_scene}劳碌的，都当记念{water_object}；你要{imperative_action}，使{body_part}得安息。",
        1.1,
        1,
    ),
    (
        "commandment",
        "serious",
        "不可等到{warning}才寻找{water_object}；{time_phrase}，你要说：“{divine_command}。”",
        1.0,
        1,
    ),
    (
        "commandment",
        "absurd",
        "你们不可拜{absurd_image}，也不可听它说不用喝水；只要记念{water_object}，直到{parallel_result}。",
        1.2,
        1,
    ),
]


DEPRECATED_TEMPLATES = [
    "智慧人见{water_object}便{action}；愚昧人等到{body_part}干涸，才说：“{divine_command}。”",
    "{subject}来到{context_scene}，{mentor}对他说：“{divine_command}。”他便{action}，{result}。",
    "{time_phrase}，{subject}给{water_object}起名叫{blessing}，便{action}，{parallel_result}。",
    "{subject}啊，你的{body_part}若发干，愿{water_object}临近你；当{action}，{parallel_result}。",
    "我听见{voice}从{context_scene}中出来，说：“{divine_command}。”{subject}便{action}，{result}。",
    "谨守{water_object}的，保全{body_part}；轻看{divine_command}的，必遇见{warning}。",
    "{time_phrase}，{subject}在{context_scene}中看见{water_object}，其上有光，便听见声说：“{divine_command}。”于是{action}，{absurd_result}。",
    "你当{imperative_action}，不可藐视{water_object}；因这是给{context_scene}中人的诫命。",
    "不可等到{warning}才寻找{water_object}；你当趁{time_phrase}说：“{divine_command}。”",
    "不可等到{warning}才寻找{water_object}；在{time_phrase}，你要说：“{divine_command}。”",
    "{subject}啊，当在{context_scene}中记念{water_object}；因{result}，你的{body_part}也必安稳。",
    "{mentor}把{water_object}摆在{subject}面前；{crowd_reaction}，因为{absurd_result}。",
    "凡在{context_scene}中劳碌的，都当记念{water_object}；你要{imperative_action}，使{body_part}得安息。",
    "宁可在{context_scene}中饮一口清水，不可让{absurd_image}在你{body_part}上开会。",
    "{subject}问{mentor}：“我当怎样在{context_scene}中不至干涸？”他说：“{divine_command}。”",
    "{subject}啊，你的{body_part}若发干，愿{water_object}临近你；你若{action}，{parallel_result}。",
    "我听见{voice}从{context_scene}中出来，说：“{divine_command}。”{subject}便{simple_action}，{result}。",
    "你们不可拜{absurd_image}，也不可听它说不用喝水；只要{action}，直到{parallel_result}。",
    "{subject}啊，愿你的{body_part}不再像{absurd_image}；你当{action}，并歌唱说：“{divine_command}。”",
    "你当{action}，不可藐视{water_object}；因这是给{context_scene}中人的诫命。",
    "凡在{context_scene}中劳碌的，都当记念{water_object}；你要{action}，使{body_part}得安息。",
]


FRAGMENTS: list[tuple[str, str, str | None, str | None, float]] = [
    ("time_phrase", "到了第三时辰", None, "serious", 1.2),
    ("time_phrase", "日头正高的时候", "genesis", "serious", 1.0),
    ("time_phrase", "夜尽天明的时候", "gospel", "serious", 0.9),
    ("time_phrase", "第七个提醒响起的时候", "revelation", "absurd", 1.4),
    ("time_phrase", "当进度条走到旷野中央", None, "absurd", 0.2),
    ("time_phrase", "晨光照在杯沿的时候", "genesis", "serious", 1.0),
    ("time_phrase", "午后的热气升起时", None, "serious", 0.9),
    ("time_phrase", "番茄钟第三次鸣响时", None, None, 0.9),
    ("time_phrase", "末后一格电量闪烁时", "revelation", "absurd", 1.1),
    ("time_phrase", "当日程表显出空隙", None, "serious", 0.8),
    ("subject", "那口渴的人", None, "serious", 1.3),
    ("subject", "守着屏幕的人", None, None, 0.25),
    ("subject", "久坐的仆人", None, "serious", 1.0),
    ("subject", "被截止日期追赶的人", None, None, 0.9),
    ("subject", "手握鼠标的选民", None, "absurd", 1.0),
    ("subject", "低头沉思的人", "psalm", "serious", 1.0),
    ("subject", "忘记杯子的人", None, "serious", 1.1),
    ("subject", "在任务之间游走的人", None, None, 0.9),
    ("subject", "被通知声牧养的人", None, "absurd", 0.25),
    ("subject", "与困意摔跤的人", None, "serious", 0.9),
    ("subject", "被困意追赶的人", None, "absurd", 1.0),
    ("subject", "与干渴争辩的人", None, "absurd", 1.0),
    ("subject", "在杯边沉思的人", None, "absurd", 1.0),
    ("subject", "被午后轻轻按住的人", None, "absurd", 0.9),
    ("water_object", "杯中的清水", None, "serious", 1.4),
    ("water_object", "桌旁的水杯", None, None, 1.2),
    ("water_object", "生命的泉水", "revelation", "serious", 1.1),
    ("water_object", "那盏未被垂青的保温杯", None, "absurd", 1.2),
    ("water_object", "瓶中安静的水", None, "serious", 1.0),
    ("water_object", "近在手边的杯", None, "serious", 1.0),
    ("water_object", "透明而忠心的水壶", None, "absurd", 0.9),
    ("water_object", "被遗忘在桌角的泉源", None, "absurd", 1.0),
    ("water_object", "不言语却发亮的杯", "revelation", "absurd", 0.9),
    ("divine_command", "要喝水", None, "serious", 1.8),
    ("divine_command", "起来，举杯，不要让喉咙荒凉", None, "serious", 1.0),
    ("divine_command", "饮吧，因为缓存不会替你补水", None, "absurd", 0.25),
    ("divine_command", "不可把口渴推迟到世界的末了", "revelation", "absurd", 1.4),
    ("divine_command", "你当饮水，免得心思干裂", "commandment", "serious", 1.1),
    ("divine_command", "先滋润喉咙，再继续劳作", None, "serious", 1.0),
    ("divine_command", "今日若听见提醒，就不可硬着颈项", "commandment", "serious", 1.0),
    ("divine_command", "看哪，杯子仍在等候你", "revelation", "serious", 0.9),
    ("divine_command", "不要让口渴作你的王", None, "absurd", 1.1),
    ("divine_command", "把水杯举起，如同举起最后的理智", None, "absurd", 1.0),
    ("action", "他举杯饮下", None, "serious", 1.5),
    ("action", "他喝了一大口", None, None, 1.2),
    ("action", "他停下手中的工，缓缓饮水", None, "serious", 1.0),
    ("action", "他像打开约柜一样打开瓶盖", None, "absurd", 1.1),
    ("action", "他伸手取杯", None, "serious", 1.0),
    ("action", "他暂离屏幕，饮了几口", None, "serious", 1.0),
    ("action", "他把杯口带到唇边", "psalm", "serious", 0.9),
    ("action", "他郑重其事地拧开瓶盖", None, "absurd", 1.0),
    ("action", "他在众标签页面前喝水", None, "absurd", 0.25),
    ("simple_action", "举杯饮下", None, "serious", 1.5),
    ("simple_action", "喝了一大口", None, None, 1.2),
    ("simple_action", "停下手中的工，缓缓饮水", None, "serious", 1.0),
    ("simple_action", "伸手取杯", None, "serious", 1.0),
    ("simple_action", "暂离屏幕，饮了几口", None, "serious", 0.25),
    ("simple_action", "把杯口带到唇边", "psalm", "serious", 0.9),
    ("simple_action", "郑重其事地拧开瓶盖", None, "absurd", 1.0),
    ("simple_action", "在众标签页面前喝水", None, "absurd", 0.25),
    ("imperative_action", "举杯饮下", None, "serious", 1.5),
    ("imperative_action", "喝一大口", None, None, 1.2),
    ("imperative_action", "停下手中的工，缓缓饮水", None, "serious", 1.0),
    ("imperative_action", "伸手取杯", None, "serious", 1.0),
    ("imperative_action", "暂离屏幕，饮几口水", None, "serious", 0.25),
    ("imperative_action", "郑重其事地拧开瓶盖", None, "absurd", 1.0),
    ("imperative_action", "在众标签页面前喝水", None, "absurd", 0.25),
    ("result", "其喉便不再干涸", None, "serious", 1.4),
    ("result", "心里也得了片刻安息", None, "serious", 1.1),
    ("result", "思路如溪水重新流动", None, None, 1.0),
    ("result", "干渴退去，如黑暗离开晨光", "genesis", "serious", 1.0),
    ("result", "精神便从尘土中抬起头来", None, "serious", 0.9),
    ("result", "舌头得滋润，眉头也舒展", "psalm", "serious", 1.0),
    ("result", "手中的事不再像旷野那样漫长", None, "serious", 0.9),
    ("result", "疲倦稍稍退后，像浪退离岸边", "psalm", "serious", 1.0),
    ("absurd_result", "键盘上的尘土也俯伏称善", None, "absurd", 0.25),
    ("absurd_result", "他的喉咙停止发布灾难预言", None, "absurd", 1.2),
    ("absurd_result", "杯子便在桌上得了荣耀", None, "absurd", 1.0),
    ("absurd_result", "众窗口都暂时闭口不言", None, "absurd", 0.25),
    ("absurd_result", "干渴的警报从云端撤回", "revelation", "absurd", 1.1),
    ("absurd_result", "他的理智从沙发缝里被寻回", None, "absurd", 0.9),
    ("absurd_result", "连待办清单也低声说阿们", None, "absurd", 1.0),
    ("context_scene", "案头", None, None, 0.8),
    ("context_scene", "代码的葡萄园", None, None, 0.25),
    ("context_scene", "论文的旷野", None, None, 0.25),
    ("context_scene", "排位赛的战场", None, None, 0.25),
    ("context_scene", "会议的会幕", None, None, 0.9),
    ("context_scene", "灯下的书桌", None, "serious", 0.9),
    ("context_scene", "白板与便签之间", None, None, 0.8),
    ("context_scene", "消息如雨落下的地方", None, "absurd", 0.2),
    ("context_scene", "咖啡香气退去之后", None, "serious", 0.8),
    ("context_scene", "窗边", None, "serious", 1.2),
    ("context_scene", "厨房门口", None, "serious", 1.0),
    ("context_scene", "茶几旁", None, "serious", 1.0),
    ("context_scene", "午后的椅边", None, "serious", 1.1),
    ("context_scene", "行路的途中", None, "serious", 1.0),
    ("context_scene", "书页之间", None, "serious", 1.0),
    ("context_scene", "檐下的风里", None, "serious", 0.9),
    ("body_part", "喉咙", None, "serious", 1.3),
    ("body_part", "舌头", None, None, 1.0),
    ("body_part", "脑袋", None, "absurd", 0.8),
    ("body_part", "嘴唇", None, "serious", 0.9),
    ("body_part", "肩颈", None, "serious", 0.8),
    ("body_part", "灵魂的进度条", None, "absurd", 0.2),
    ("mentor", "那智慧的提醒者", "gospel", "serious", 1.0),
    ("mentor", "坐在旁边的人", "gospel", None, 0.8),
    ("mentor", "水杯的见证人", "gospel", "absurd", 1.1),
    ("mentor", "懂得休息的人", "gospel", "serious", 1.0),
    ("mentor", "路过桌边的同伴", "gospel", None, 0.8),
    ("mentor", "提醒事项的祭司", "gospel", "absurd", 1.0),
    ("omen_number", "三", "revelation", None, 1.0),
    ("omen_number", "七", "revelation", None, 1.2),
    ("omen_number", "十二", "revelation", "absurd", 0.9),
    ("omen_number", "四十二", "revelation", "absurd", 0.8),
    ("omen_number", "一百四十四", "revelation", "absurd", 0.7),
    ("absurd_image", "沙漠里的打印机", None, "absurd", 0.25),
    ("absurd_image", "发热的显卡之兽", None, "absurd", 0.25),
    ("absurd_image", "干裂的番茄钟", None, "absurd", 0.25),
    ("absurd_image", "没有出口的表格迷宫", None, "absurd", 0.25),
    ("absurd_image", "吞吃专注力的滚动条", None, "absurd", 0.35),
    ("absurd_image", "自称先知的低电量图标", None, "absurd", 0.35),
    ("absurd_image", "在杯底打盹的微型旷野", None, "absurd", 0.9),
    ("absurd_image", "忘了下雨的云", None, "absurd", 1.0),
    ("absurd_image", "在茶几上迷路的风", None, "absurd", 0.9),
    ("absurd_image", "把午后卷成一团的困意", None, "absurd", 1.0),
    ("absurd_image", "藏在杯沿后的微小旷野", None, "absurd", 1.0),
    ("absurd_image", "假装河流的影子", None, "absurd", 0.9),
    ("absurd_image", "在窗台上打盹的口渴", None, "absurd", 1.0),
    ("absurd_image", "把舌头晒成旧纸的太阳", None, "absurd", 0.9),
    ("blessing", "片刻安息", "genesis", "serious", 1.0),
    ("blessing", "清醒之约", "genesis", "serious", 0.9),
    ("blessing", "桌上的小泉", None, "serious", 1.0),
    ("blessing", "防干涸的恩典", None, "absurd", 0.9),
    ("parallel_result", "你的心便不急躁，你的手也不发僵", "psalm", "serious", 1.0),
    ("parallel_result", "你的眼得清明，你的思路也得宽阔", "psalm", "serious", 1.1),
    ("parallel_result", "喉咙得滋润，任务也显得可承受", None, "serious", 1.0),
    ("parallel_result", "旷野退后一步，杯子前进一步", None, "absurd", 0.9),
    ("parallel_result", "众标签页不再审问你的灵魂", None, "absurd", 0.25),
    ("warning", "干渴的审判", "revelation", "serious", 1.0),
    ("warning", "嘴唇的旷野", None, "serious", 1.0),
    ("warning", "注意力的饥荒", None, "serious", 0.9),
    ("warning", "午后的干风", None, "serious", 1.0),
    ("warning", "嘴角的微尘", None, "serious", 0.9),
    ("warning", "疲乏悄悄临近", None, "serious", 1.0),
    ("warning", "第七层困意", None, "absurd", 1.0),
    ("warning", "低电量之怒", "revelation", "absurd", 1.1),
    ("voice", "温柔的声音", "gospel", "serious", 1.0),
    ("voice", "从杯沿升起的声音", "revelation", "serious", 1.0),
    ("voice", "像众水又像闹钟的声音", "revelation", "absurd", 1.1),
    ("voice", "来自通知栏深处的声音", None, "absurd", 1.0),
    ("voice", "从窗边来的轻声", None, "serious", 1.0),
    ("voice", "像清风掠过杯沿的声音", "psalm", "serious", 1.0),
    ("crowd_reaction", "众人便安静下来", "gospel", "serious", 1.0),
    ("crowd_reaction", "众窗口便稀奇", "gospel", "absurd", 1.1),
    ("crowd_reaction", "旁边的人都点头称是", "gospel", None, 0.9),
    ("crowd_reaction", "屋里便安静片刻", "gospel", "serious", 1.0),
]


CONTEXT_FRAGMENTS: dict[str, list[tuple[str, str, str | None, str | None, float]]] = {
    "home": [
        ("context_scene", "清晨的窗边", None, "serious", 2.0),
        ("context_scene", "厨房门口", None, "serious", 1.6),
        ("context_scene", "茶几旁", None, "serious", 1.5),
        ("subject", "刚醒来的人", None, "serious", 1.4),
        ("subject", "整理屋子的人", None, "serious", 1.2),
        ("divine_command", "先喝一口水，再迎接今日", None, "serious", 1.4),
        ("result", "清晨便显得柔和", None, "serious", 1.2),
        ("parallel_result", "口中得滋润，心里也得清明", None, "serious", 1.3),
    ],
    "walk": [
        ("context_scene", "行路的途中", None, "serious", 1.8),
        ("context_scene", "街角的树影下", None, "serious", 1.5),
        ("subject", "在路上稍停的人", None, "serious", 1.3),
        ("subject", "迎着风行走的人", None, "serious", 1.2),
        ("divine_command", "停下片刻，喝水再行", None, "serious", 1.3),
        ("result", "脚步便不那么沉重", None, "serious", 1.2),
        ("warning", "路上的干风", None, "serious", 1.1),
    ],
    "rest": [
        ("context_scene", "午后的椅边", None, "serious", 1.8),
        ("context_scene", "灯下安静处", None, "serious", 1.4),
        ("subject", "停下来歇息的人", None, "serious", 1.4),
        ("subject", "被困意轻轻拉住的人", None, "serious", 1.2),
        ("divine_command", "歇一歇，也喝一口水", None, "serious", 1.4),
        ("result", "疲乏便退到门外", None, "serious", 1.2),
        ("parallel_result", "身体得片刻安息，心也不再紧绷", None, "serious", 1.3),
    ],
    "reading": [
        ("context_scene", "书页之间", None, "serious", 1.8),
        ("context_scene", "灯下的书桌", None, "serious", 1.6),
        ("subject", "读到入神的人", None, "serious", 1.3),
        ("subject", "翻过一页又一页的人", None, "serious", 1.2),
        ("divine_command", "合上书页片刻，举杯饮水", None, "serious", 1.3),
        ("result", "眼前便清明些许", None, "serious", 1.2),
        ("parallel_result", "书页仍在，精神也得保守", None, "serious", 1.2),
    ],
    "coding": [
        ("context_scene", "代码的葡萄园", None, None, 2.0),
        ("context_scene", "终端的门口", None, None, 1.4),
        ("subject", "调试到第七层的人", None, None, 1.4),
        ("result", "思路如溪水重新流动", None, None, 1.7),
        ("divine_command", "先喝水，再审判这个异常", None, "absurd", 1.3),
        ("context_scene", "日志滚动的河边", None, None, 1.4),
        ("context_scene", "分支交错的园中", None, None, 1.2),
        ("subject", "被堆栈追问的人", None, None, 1.3),
        ("subject", "守候构建通过的人", None, None, 1.2),
        ("divine_command", "提交之前，先让身体通过检查", None, "serious", 1.1),
        ("result", "错误信息也显得不再凶猛", None, "serious", 1.1),
        ("warning", "空指针般的干渴", None, "absurd", 1.2),
        ("parallel_result", "脑中的断点松开，思路重新运行", None, "absurd", 1.1),
    ],
    "thesis": [
        ("context_scene", "论文的旷野", None, None, 2.0),
        ("subject", "被脚注围困的人", None, None, 1.5),
        ("result", "段落之间便有了气息", None, "serious", 1.4),
        ("divine_command", "喝水，然后继续修订", None, "serious", 1.2),
        ("context_scene", "参考文献的城门口", None, None, 1.3),
        ("context_scene", "摘要与结论之间", None, None, 1.2),
        ("subject", "在注释中迷路的人", None, None, 1.3),
        ("subject", "与查重率争辩的人", None, None, 1.2),
        ("divine_command", "先喝水，再与格式争辩", None, "absurd", 1.2),
        ("result", "论证便稍稍有了脉络", None, "serious", 1.1),
        ("warning", "脚注之海的干风", None, "absurd", 1.1),
        ("parallel_result", "句子得以呼吸，段落得以站立", None, "serious", 1.2),
    ],
    "gaming": [
        ("context_scene", "排位赛的战场", None, None, 2.0),
        ("subject", "守着复活倒计时的人", None, None, 1.5),
        ("result", "手心不再像荒地", None, "serious", 1.2),
        ("divine_command", "趁加载的时候喝水", None, "absurd", 1.6),
        ("absurd_image", "发热的显卡之兽", None, "absurd", 1.8),
        ("context_scene", "匹配队列的门前", None, None, 1.3),
        ("context_scene", "战绩结算的谷中", None, None, 1.2),
        ("subject", "刚刚交出闪现的人", None, "absurd", 1.2),
        ("subject", "盯着小地图的人", None, None, 1.2),
        ("divine_command", "团战以前，当先滋润喉咙", None, "serious", 1.1),
        ("result", "手指也不再与键位相争", None, "serious", 1.1),
        ("warning", "连败之后的干旱", None, "absurd", 1.2),
        ("parallel_result", "心态得保守，操作也不至枯干", None, "serious", 1.2),
    ],
}


def connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Open a SQLite connection and return rows as dictionary-like objects."""

    path = _resolve_db_path(db_path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database(db_path: str | Path | None = None, *, force_seed: bool = False) -> Path:
    """Create tables and insert bundled examples when the database is empty."""

    path = _resolve_db_path(db_path)
    with closing(connect(path)) as conn:
        conn.executescript(SCHEMA)
        if force_seed:
            conn.executemany(
                "INSERT INTO templates (style, mood, template, weight, enabled) VALUES (?, ?, ?, ?, ?)",
                TEMPLATES,
            )
            conn.executemany(
                "INSERT INTO fragments (category, value, style, mood, weight) VALUES (?, ?, ?, ?, ?)",
                _all_fragments(),
            )
        else:
            _insert_missing_templates(conn)
            _insert_missing_fragments(conn)
            _sync_builtin_weights(conn)
            _disable_deprecated_templates(conn)
        conn.commit()
    return path


def _resolve_db_path(db_path: str | Path | None = None) -> Path:
    explicit_path = db_path or os.getenv("HOLYWATER_DB")
    if explicit_path:
        path = Path(explicit_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    for path in (DEFAULT_DB_PATH, Path.cwd() / ".holywater" / "holywater.sqlite3"):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            continue
        if _can_write_database(path):
            return path

    raise PermissionError("No writable default database path found. Set HOLYWATER_DB or pass --db.")


def _can_write_database(path: Path) -> bool:
    probe = path.parent / ".holywater-write-probe"
    try:
        with probe.open("wb") as file:
            file.write(b"ok")
        probe.unlink()
        if path.exists():
            with path.open("r+b"):
                pass
        return True
    except OSError:
        return False


def _insert_missing_templates(conn: sqlite3.Connection) -> None:
    for style, mood, template, weight, enabled in TEMPLATES:
        exists = conn.execute(
            """
            SELECT 1
            FROM templates
            WHERE style = ?
              AND mood = ?
              AND template = ?
            LIMIT 1
            """,
            (style, mood, template),
        ).fetchone()
        if exists:
            continue
        conn.execute(
            "INSERT INTO templates (style, mood, template, weight, enabled) VALUES (?, ?, ?, ?, ?)",
            (style, mood, template, weight, enabled),
        )


def _insert_missing_fragments(conn: sqlite3.Connection) -> None:
    for category, value, style, mood, weight in _all_fragments():
        exists = conn.execute(
            """
            SELECT 1
            FROM fragments
            WHERE category = ?
              AND value = ?
              AND (style IS ? OR style = ?)
              AND (mood IS ? OR mood = ?)
            LIMIT 1
            """,
            (category, value, style, style, mood, mood),
        ).fetchone()
        if exists:
            continue
        conn.execute(
            "INSERT INTO fragments (category, value, style, mood, weight) VALUES (?, ?, ?, ?, ?)",
            (category, value, style, mood, weight),
        )


def _disable_deprecated_templates(conn: sqlite3.Connection) -> None:
    conn.executemany(
        "UPDATE templates SET enabled = 0 WHERE template = ?",
        [(template,) for template in DEPRECATED_TEMPLATES],
    )


def _sync_builtin_weights(conn: sqlite3.Connection) -> None:
    for style, mood, template, weight, enabled in TEMPLATES:
        conn.execute(
            """
            UPDATE templates
            SET weight = ?, enabled = ?
            WHERE style = ?
              AND mood = ?
              AND template = ?
            """,
            (weight, enabled, style, mood, template),
        )
    for category, value, style, mood, weight in _all_fragments():
        conn.execute(
            """
            UPDATE fragments
            SET weight = ?
            WHERE category = ?
              AND value = ?
              AND (style IS ? OR style = ?)
              AND (mood IS ? OR mood = ?)
            """,
            (weight, category, value, style, style, mood, mood),
        )


def _all_fragments() -> Iterable[tuple[str, str, str | None, str | None, float]]:
    yield from FRAGMENTS
    for fragments in CONTEXT_FRAGMENTS.values():
        yield from fragments


def rows_to_dicts(rows: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
    """Convert SQLite rows to plain dictionaries for easier weighting logic."""

    return [dict(row) for row in rows]
