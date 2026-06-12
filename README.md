# Holy Water

圣经风格喝水提醒文案生成器，支持 library mode、CLI mode 和 FastAPI API mode。项目使用 SQLite 存储句式模板、词块和生成历史。

## 功能

- 子风格：`genesis`、`psalm`、`proverb`、`revelation`、`gospel`、`commandment`
- mood：`serious`、`absurd`
- intensity：`1` 到 `5`，从普通提醒逐步偏向强烈、荒诞、启示录式表达
- context：内置 `coding`、`thesis`、`gaming` 的权重增强
- seed：传入相同 seed 可复现生成结果
- 引用：每条文案返回伪经文引用，例如 `《饮水记》2:7`
- 去重：`generation_history` 会记录近期生成内容，短时间内尽量避免重复
- daily：使用日期和参数生成每日固定文案

## 安装

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

默认数据库路径是 `~/.holywater/holywater.sqlite3`。API 可通过环境变量 `HOLYWATER_DB` 指定数据库文件。

## Library Mode

```python
from holywater import generate

text = generate(
    style="psalm",
    mood="serious",
    intensity=2,
    context="coding",
    seed=20260612,
)

print(text.content)
print(text.reference)
print(text.seed)
```

也可以运行示例：

```powershell
python examples/example_usage.py
```

## CLI Mode

初始化数据库：

```powershell
holywater init-db
```

生成一条文案：

```powershell
holywater generate --style revelation --mood absurd --intensity 5 --context gaming
```

输出 JSON：

```powershell
holywater generate --style proverb --mood serious --intensity 3 --context thesis --seed 42 --json
```

每日固定文案：

```powershell
holywater daily --style genesis --mood serious --context coding
```

未安装时也可从源码运行：

```powershell
$env:PYTHONPATH="src"
python -m holywater generate --style genesis --mood serious --intensity 3
```

## API Mode

启动服务：

```powershell
uvicorn holywater.api:app --reload
```

如果从源码树运行且尚未安装：

```powershell
$env:PYTHONPATH="src"
uvicorn holywater.api:app --reload
```

生成接口：

```text
GET /generate?style=revelation&mood=absurd&intensity=5&context=gaming&seed=42
```

每日固定接口：

```text
GET /daily?style=psalm&mood=serious&intensity=2&context=coding
GET /daily?style=psalm&mood=serious&intensity=2&context=coding&day=2026-06-12
```

响应示例：

```json
{
  "content": "到了第三时辰，那口渴的人见杯中的清水，便说：“要喝水。”于是他举杯饮下，其喉便不再干涸。",
  "reference": "《饮水记》2:7",
  "style": "genesis",
  "mood": "serious",
  "seed": 42
}
```

## SQLite Schema

`templates`

- `id`
- `style`
- `mood`
- `template`
- `weight`
- `enabled`

`fragments`

- `id`
- `category`
- `value`
- `style`
- `mood`
- `weight`

`generation_history`

- `id`
- `text`
- `style`
- `mood`
- `created_at`

## 开发验证

```powershell
$env:PYTHONPATH="src"
python -m compileall src examples tests
python tests/test_generator.py
```
