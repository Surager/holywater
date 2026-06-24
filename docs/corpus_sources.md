# Corpus Sources

这个项目生成的是“圣经风格喝水提醒”，不应该把整段经文直接拼进去。更稳妥的方式是从公开语料里抽取句法、节奏、意象类别和连接词，再人工改写成喝水提醒模板与 fragment。

当前仓库内置模板和 fragment 为项目原创或人工改写短句，随项目以 MIT License 发布；不得提交直接复制的现代译本、注释、灵修材料或其他版权文本。

## 推荐来源

### 1. King James Version, Project Gutenberg

- URL: https://www.gutenberg.org/ebooks/10
- 用途：提取英文圣经风格的句法结构，再转写成中文模板。
- 授权要点：Project Gutenberg 页面标注 KJV 在美国为 public domain。
- 适合抽取：
  - `And it came to pass...` 对应“到了……的时候”
  - “behold / verily / blessed / woe unto” 对应启示、训诫、祝福、警告语气
  - genealogy、commandment、gospel dialogue、psalm parallelism 等结构

建议只把它当“结构语料”，不要把大量英文句子直接塞进数据库。

### 2. Open English Bible

- URL: https://github.com/openenglishbible/Open-English-Bible
- 用途：现代英文圣经语体参考，适合补 gospel、proverb、psalm 的柔和表达。
- 授权要点：仓库标注 CC0-1.0。
- 适合抽取：
  - 比 KJV 更现代的劝勉句
  - 简短对话和叙事转场
  - 更自然的祝福/警醒结构

### 3. World English Bible

- URL: https://worldenglish.bible/
- 用途：现代英文公共领域译本，适合补充可读性更强的结构。
- 授权要点：官方说明其文本开放供使用；使用前仍建议保留来源记录。
- 适合抽取：
  - “You shall...” 式命令
  - “Blessed is...” 式格言
  - 诗篇式平行句

### 4. 中文和合本 1919 相关公开版本

- 可查入口：
  - https://zh.wikisource.org
  - https://en.wikipedia.org/wiki/Chinese_Union_Version
- 用途：中文圣经腔最直接的参考。
- 授权注意：
  - 1919 年初版和合本通常更适合作为公版候选。
  - 1988 年新标点和合本、2010 年和合本修订版属于后续修订，不能默认当作可自由复制的语料。
  - 不同地区版权期限不同，正式发布前需要再次核实使用地和分发地的版权状态。
- 适合抽取：
  - “到了……，……便……”
  - “你们要……，不可……”
  - “有福了，因为……”
  - “我又看见……”

建议只人工抽象模板，不批量内置整句经文。

### 5. Wikisource 公版中文古文/译文

- URL: https://zh.wikisource.org
- 用途：补中文古雅语感，不只局限于圣经文本。
- 授权要点：Wikisource 收录公有领域或自由授权文本，但每个页面仍要看版权标记。
- 适合抽取：
  - 文言/半文言连接词
  - 训诫、箴言、诏令式短句
  - “于是、乃、必、不可、当、若”等功能词搭配

## 不建议直接使用

- 现代中文圣经译本，例如当代译本、新译本、和合本修订版。
- Bible app、网页平台上的现代译文，除非页面明确允许再分发和改作。
- 带注释、研读本、灵修材料。这些通常比经文本身更容易有版权限制。

## 落地方法

1. 先从语料中人工整理“句型”，而不是复制句子。
2. 把句型改成项目模板，例如 `{time_phrase}，{subject}见{water_object}，便说：“{divine_command}。”`
3. 把意象拆成 fragment：
   - `time_phrase`：到了第三时辰、日头正高的时候、夜尽天明的时候
   - `divine_command`：要喝水、不可藐视杯中的清水、起来举杯
   - `result`：其喉便不再干涸、思路如溪水重新流动
4. 每个 fragment 加上 `style`、`mood`、`weight`，不要所有风格共用一套词。
5. 每次新增语料，在 PR 或提交说明里记录来源 URL、授权判断和是否为人工改写。

## 风格扩充方向

- `genesis`：叙事、起初、看见、命名、分开、于是。
- `psalm`：呼告、平行句、安慰、赞美、身体感受。
- `proverb`：对比句、智慧人/愚昧人、宁可/不可。
- `revelation`：异象、数字、声音、灾变、夸张意象。
- `gospel`：人物来到某处、对话、递给、众人稀奇。
- `commandment`：你当、不可、第一条诫命、凡……都要……。
