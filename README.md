# Holy Water

[GitHub](https://github.com/Surager/holywater) | [Corpus notes](docs/corpus_sources.md)

一个圣经风格喝水提醒文案生成器。它会从内置语料里随机组合出一段庄严、诗性或荒诞的提醒，并附上一条伪经文引用，例如 `《晨杯记》4:10`。

不传参数时，Holy Water 会生成一条完全随机的文案。你也可以指定风格、语气、强度和场景。

## Features

- 支持 `genesis`、`psalm`、`proverb`、`revelation`、`gospel`、`commandment` 等子风格
- 支持严肃和荒诞两种语气
- 支持从温和提醒到启示录式夸张表达的强度调节
- 默认偏向中性、日常生活语料
- 可用 seed 复现同一条生成结果
- 每条文案都有伪经文引用
- 内置近期去重，避免短时间内反复生成同一句
- 可作为命令行工具、Python 库或 FastAPI 服务使用

## Install and run

### Run with uv

```bash
uv sync
uv run holywater generate
```

### Install with pip

```bash
pip install -e .
holywater generate
```

## Quick start

### Generate a random reminder

```console
$ holywater generate
院门半开之时，看云的旅人见手边的凉水，便说：“让清水先到喉中。”于是他把杯口带到唇边，干渴退到门外，如晨光临到窗前。 《晨杯记》4:10
```

### Generate JSON

```console
$ holywater generate --json --seed 42
{
  "content": "我听见从窗边来的轻声自咖啡香气退去之后传来，说：“让杯中水先到口中，不必急忙。”忘记杯盏的旅人便将温水送入口中，一日的劳碌轻了些，如晨光临到窗前。",
  "reference": "《启杯录》2:4",
  "style": "revelation",
  "mood": "serious",
  "seed": 42
}
```

### Pick a style

```bash
holywater generate --style psalm
holywater generate --style proverb --mood serious
holywater generate --style revelation --mood absurd --intensity 5
```

### Pick a scene

```bash
holywater generate --context home
holywater generate --context reading
holywater generate --context garden
```

现代场景不会默认出现，需要显式指定：

```bash
holywater generate --context coding
holywater generate --context thesis
holywater generate --context gaming
```

### Daily text

```bash
holywater daily
```

同一天、同一组参数会返回固定文案。

## Python

```python
from holywater import generate

text = generate(style="psalm", mood="serious", seed=20260624)

print(text.content)
print(text.reference)
```

## API

```bash
uv run uvicorn holywater.api:app --reload
```

```text
GET /generate
GET /daily
GET /generate?style=revelation&mood=absurd&intensity=5&context=garden&seed=42
```

## Usage

```console
$ holywater generate --help
```

```console
$ holywater daily --help
```

常用参数：

- `--style`: `random`、`genesis`、`psalm`、`proverb`、`revelation`、`gospel`、`commandment`
- `--mood`: `random`、`serious`、`absurd`
- `--intensity`: `1` 到 `5`
- `--context`: `random`、`home`、`walk`、`rest`、`reading`、`meal`、`garden`、`coding`、`thesis`、`gaming`、`none`
- `--seed`: 复现生成结果
- `--json`: 输出 JSON

## Corpus

内置模板和词块是项目原创或人工改写短句，不直接复制现代圣经译本、注释、灵修材料或其他版权文本。

语料扩充建议见 [docs/corpus_sources.md](docs/corpus_sources.md)。

## License

MIT
