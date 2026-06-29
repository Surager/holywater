(function () {
  "use strict";

  const corpus = globalThis.__HOLYWATER_CORPUS__;
  if (!corpus) {
    return;
  }

  const ALLOWED_STYLES = new Set(corpus.allowedStyles);
  const ALLOWED_MOODS = new Set(corpus.allowedMoods);
  const RANDOM_VALUE = "random";
  const PLACEHOLDER_RE = /\{([a-zA-Z_][a-zA-Z0-9_]*)\}/g;

  function u32(value) {
    return Number(BigInt.asUintN(32, BigInt(value)));
  }

  function mtMult(previous, multiplier) {
    return u32(
      Number((BigInt(multiplier) * BigInt(previous ^ (previous >>> 30))) & 0xffffffffn)
    );
  }

  class Random {
    constructor(seed) {
      this.mt = new Uint32Array(624);
      this.index = 624;
      this.seedFromKey([Number(seed) >>> 0]);
    }

    seedFromKey(key) {
      this.mt[0] = 19650218;
      for (let i = 1; i < 624; i++) {
        this.mt[i] = u32(mtMult(this.mt[i - 1], 1812433253) + i);
      }

      let i = 1;
      let j = 0;
      let k = Math.max(624, key.length);
      for (; k; k--) {
        this.mt[i] = u32((this.mt[i] ^ mtMult(this.mt[i - 1], 1664525)) + (key[j] >>> 0) + j);
        i += 1;
        j += 1;
        if (i >= 624) {
          this.mt[0] = this.mt[623];
          i = 1;
        }
        if (j >= key.length) {
          j = 0;
        }
      }

      for (k = 623; k; k--) {
        this.mt[i] = u32((this.mt[i] ^ mtMult(this.mt[i - 1], 1566083941)) - i);
        i += 1;
        if (i >= 624) {
          this.mt[0] = this.mt[623];
          i = 1;
        }
      }

      this.mt[0] = 0x80000000;
      this.index = 624;
    }

    genrandUint32() {
      const mag01 = [0, 0x9908b0df];
      if (this.index >= 624) {
        let kk;
        for (kk = 0; kk < 624 - 397; kk++) {
          const y = (this.mt[kk] & 0x80000000) | (this.mt[kk + 1] & 0x7fffffff);
          this.mt[kk] = this.mt[kk + 397] ^ (y >>> 1) ^ mag01[y & 1];
        }
        for (; kk < 623; kk++) {
          const y = (this.mt[kk] & 0x80000000) | (this.mt[kk + 1] & 0x7fffffff);
          this.mt[kk] = this.mt[kk + (397 - 624)] ^ (y >>> 1) ^ mag01[y & 1];
        }
        const y = (this.mt[623] & 0x80000000) | (this.mt[0] & 0x7fffffff);
        this.mt[623] = this.mt[396] ^ (y >>> 1) ^ mag01[y & 1];
        this.index = 0;
      }

      let y = this.mt[this.index++];
      y ^= y >>> 11;
      y ^= (y << 7) & 0x9d2c5680;
      y ^= (y << 15) & 0xefc60000;
      y ^= y >>> 18;
      return y >>> 0;
    }

    random() {
      const a = this.genrandUint32() >>> 5;
      const b = this.genrandUint32() >>> 6;
      return (a * 67108864.0 + b) * (1.0 / 9007199254740992.0);
    }

    uniform(a, b) {
      return a + (b - a) * this.random();
    }

    randint(a, b) {
      return a + this._randbelow(b - a + 1);
    }

    getrandbits(k) {
      if (k <= 0) {
        return 0;
      }
      if (k <= 32) {
        return this.genrandUint32() >>> (32 - k);
      }
      const words = Math.floor((k - 1) / 32) + 1;
      let result = 0n;
      const extraBits = words * 32 - k;
      for (let index = words - 1; index >= 0; index -= 1) {
        result = (result << 32n) | BigInt(this.genrandUint32());
      }
      return Number(result >> BigInt(extraBits));
    }

    _randbelow(n) {
      if (n <= 0) {
        throw new Error("n must be positive");
      }
      const bits = n.toString(2).length;
      let value = this.getrandbits(bits);
      while (value >= n) {
        value = this.getrandbits(bits);
      }
      return value;
    }

    choice(items) {
      return items[this._randbelow(items.length)];
    }
  }

  function stableSeed(value) {
    const hex = sha256(value);
    return parseInt(hex.slice(0, 12), 16) % 2147483647;
  }

  function sha256(ascii) {
    const mathPow = Math.pow;
    const maxWord = mathPow(2, 32);
    let result = "";
    const words = [];
    const asciiBitLength = ascii.length * 8;
    let hash = [];
    const k = [];
    let primeCounter = 0;
    const isComposite = {};
    for (let candidate = 2; primeCounter < 64; candidate++) {
      if (!isComposite[candidate]) {
        for (let i = 0; i < 313; i += candidate) {
          isComposite[i] = candidate;
        }
        hash[primeCounter] = (mathPow(candidate, 0.5) * maxWord) | 0;
        k[primeCounter++] = (mathPow(candidate, 1 / 3) * maxWord) | 0;
      }
    }
    ascii += "\x80";
    while ((ascii.length % 64) - 56) {
      ascii += "\x00";
    }
    for (let i = 0; i < ascii.length; i++) {
      const j = ascii.charCodeAt(i);
      words[i >> 2] |= j << ((3 - (i % 4)) * 8);
    }
    words[words.length] = (asciiBitLength / maxWord) | 0;
    words[words.length] = asciiBitLength;
    for (let j = 0; j < words.length; ) {
      const w = words.slice(j, (j += 16));
      const oldHash = hash.slice(0);
      for (let i = 0; i < 64; i++) {
        const w15 = w[i - 15];
        const w2 = w[i - 2];
        const a = hash[0];
        const e = hash[4];
        const temp1 =
          hash[7] +
          (rightRotate(e, 6) ^ rightRotate(e, 11) ^ rightRotate(e, 25)) +
          ((e & hash[5]) ^ (~e & hash[6])) +
          k[i] +
          (w[i] =
            i < 16
              ? w[i]
              : (w[i - 16] +
                  (rightRotate(w15, 7) ^ rightRotate(w15, 18) ^ (w15 >>> 3)) +
                  w[i - 7] +
                  (rightRotate(w2, 17) ^ rightRotate(w2, 19) ^ (w2 >>> 10))) |
                0);
        const temp2 =
          (rightRotate(a, 2) ^ rightRotate(a, 13) ^ rightRotate(a, 22)) +
          ((a & hash[1]) ^ (a & hash[2]) ^ (hash[1] & hash[2]));
        hash = [(temp1 + temp2) | 0].concat(hash);
        hash[4] = (hash[4] + temp1) | 0;
        hash.pop();
      }
      for (let i = 0; i < 8; i++) {
        hash[i] = (hash[i] + oldHash[i]) | 0;
      }
    }
    for (let i = 0; i < 8; i++) {
      for (let j = 3; j + 1; j--) {
        const b = (hash[i] >> (j * 8)) & 255;
        result += (b < 16 ? "0" : "") + b.toString(16);
      }
    }
    return result;
  }

  function rightRotate(value, amount) {
    return (value >>> amount) | (value << (32 - amount));
  }

  function templateFields(template) {
    const fields = [];
    let match;
    PLACEHOLDER_RE.lastIndex = 0;
    while ((match = PLACEHOLDER_RE.exec(template))) {
      if (!fields.includes(match[1])) {
        fields.push(match[1]);
      }
    }
    return fields;
  }

  function formatTemplate(template, values) {
    return template.replace(PLACEHOLDER_RE, (_, key) => values[key] ?? "");
  }

  function weightedChoice(items, rng) {
    const total = items.reduce((sum, [, weight]) => sum + Math.max(weight, 0.001), 0);
    let needle = rng.uniform(0, total);
    let upto = 0;
    for (const [item, weight] of items) {
      upto += Math.max(weight, 0.001);
      if (upto >= needle) {
        return item;
      }
    }
    return items[items.length - 1][0];
  }

  function filterContextRows(rows, context, modernContextKeywords) {
    if (corpus.modernContexts.includes(context)) {
      return rows;
    }
    const filtered = rows.filter(
      (row) =>
        !modernContextKeywords.some((keyword) =>
          (row.value || row.template || "").includes(keyword)
        )
    );
    if (context) {
      const contextKeywords = corpus.contextKeywords[context] || [context];
      const matched = filtered.filter((row) =>
        contextKeywords.some((keyword) => (row.value || row.template || "").includes(keyword))
      );
      if (matched.length) {
        return matched;
      }
    }
    return filtered.length ? filtered : rows;
  }

  function adjustWeight(row, style, mood, intensity, context, modernContextKeywords, isTemplate) {
    let weight = Number(row.weight || 1);
    const rowStyle = row.style;
    const rowMood = row.mood;
    const text = row.value || row.template || "";

    if (rowStyle === style) {
      weight *= 1.35;
    }
    if (rowMood === mood) {
      weight *= 1.25;
    }
    if (mood === "absurd") {
      weight *= 0.8 + intensity * 0.22;
    }
    if (style === "revelation" || style === "commandment") {
      weight *= 0.9 + intensity * 0.12;
    }
    if (["不可", "起来", "第七", "末了", "兽", "诫命"].some((token) => text.includes(token))) {
      weight *= 0.85 + intensity * 0.16;
    }
    if (context) {
      if (!corpus.modernContexts.includes(context) && modernContextKeywords.some((k) => text.includes(k))) {
        weight *= 0.01;
      }
      for (const [otherContext, keywords] of Object.entries(corpus.contextKeywords)) {
        if (otherContext === context) {
          continue;
        }
        if (keywords.some((keyword) => text.includes(keyword))) {
          weight *= 0.12;
          break;
        }
      }
      const contextKeywords = corpus.contextKeywords[context] || [context];
      for (const keyword of contextKeywords) {
        if (keyword && text.includes(keyword)) {
          weight *= 2.25;
          break;
        }
      }
      if (isTemplate && text.includes("context_scene")) {
        weight *= 1.0 + intensity * 0.05;
      }
    } else if (modernContextKeywords.some((keyword) => text.includes(keyword))) {
      weight *= 0.01;
    }
    return weight;
  }

  function normalizeSeed(seed) {
    if (seed === null || seed === undefined || seed === "") {
      return Math.floor(Math.random() * 2147483646) + 1;
    }
    if (typeof seed === "number") {
      return seed;
    }
    if (/^\d+$/.test(String(seed))) {
      return Number(seed);
    }
    return stableSeed(String(seed));
  }

  function resolveOptions(style, mood, intensity, context, rng) {
    let resolvedStyle = String(style).toLowerCase();
    let resolvedMood = String(mood).toLowerCase();
    if (resolvedStyle === RANDOM_VALUE) {
      resolvedStyle = rng.choice([...ALLOWED_STYLES].sort());
    }
    if (resolvedMood === RANDOM_VALUE) {
      resolvedMood = rng.choice(corpus.defaultMoodChoices);
    }
    let resolvedIntensity = intensity;
    if (resolvedIntensity === null || resolvedIntensity === undefined || resolvedIntensity === 0) {
      resolvedIntensity = rng.choice(corpus.defaultIntensityChoices);
    }
    let resolvedContext = context;
    const contextMarker =
      typeof context === "string" ? context.toLowerCase() : context;
    if (contextMarker === RANDOM_VALUE) {
      resolvedContext = rng.choice(corpus.defaultContextChoices);
    } else if (contextMarker === "" || contextMarker === "none" || contextMarker === "null") {
      resolvedContext = null;
    }
    return [resolvedStyle, resolvedMood, resolvedIntensity, resolvedContext];
  }

  function makeReference(style, intensity, rng) {
    const books = corpus.referenceBooks[style];
    const [book, maxChapter, maxVerse] = rng.choice(books);
    const chapterLimit = Math.min(maxChapter, Math.max(2, intensity + 3));
    const verseLimit = Math.min(maxVerse, 8 + intensity * 6);
    const chapter = rng.randint(1, chapterLimit);
    const verse = rng.randint(1, verseLimit);
    return `\u300a${book}\u300b${chapter}:${verse}`;
  }

  function sortById(rows) {
    return rows.slice().sort((left, right) => left.id - right.id);
  }

  function chooseTemplate(style, mood, intensity, context, rng) {
    let rows = corpus.templates.filter((row) => row.style === style && row.mood === mood);
    if (!rows.length) {
      rows = corpus.templates.slice();
    }
    rows = sortById(filterContextRows(rows, context, corpus.modernContextKeywords));
    const weighted = rows.map((row) => [
      row,
      adjustWeight(row, style, mood, intensity, context, corpus.modernContextKeywords, true),
    ]);
    return weightedChoice(weighted, rng);
  }

  function chooseFragment(category, style, mood, intensity, context, rng) {
    let rows = corpus.fragments.filter(
      (row) =>
        row.category === category &&
        (row.style === null || row.style === style) &&
        (row.mood === null || row.mood === mood)
    );
    if (!rows.length) {
      rows = corpus.fragments.filter((row) => row.category === category);
    }
    rows = sortById(filterContextRows(rows, context, corpus.modernContextKeywords));
    const weighted = rows.map((row) => [
      row,
      adjustWeight(row, style, mood, intensity, context, corpus.modernContextKeywords, false),
    ]);
    return weightedChoice(weighted, rng).value;
  }

  function generateOnce(style, mood, intensity, context, seedValue, rng) {
    const template = chooseTemplate(style, mood, intensity, context, rng);
    const categories = templateFields(template.template);
    const values = {};
    for (const category of categories) {
      values[category] = chooseFragment(category, style, mood, intensity, context, rng);
    }
    const content = formatTemplate(template.template, values);
    const reference = makeReference(style, intensity, rng);
    return { content, reference, style, mood, seed: seedValue };
  }

  function generate(options) {
    const seedValue = normalizeSeed(options.seed);
    const rng = new Random(seedValue);
    const [style, mood, intensity, context] = resolveOptions(
      options.style ?? RANDOM_VALUE,
      options.mood ?? RANDOM_VALUE,
      options.intensity ?? null,
      options.context ?? RANDOM_VALUE,
      rng
    );
    return generateOnce(style, mood, intensity, context, seedValue, rng);
  }

  function daily(options) {
    const day = options.date || todayIso();
    const style = options.style ?? RANDOM_VALUE;
    const mood = options.mood ?? RANDOM_VALUE;
    const intensity = options.intensity ?? null;
    const context = options.context ?? RANDOM_VALUE;
    const intensityPart = intensity === null || intensity === undefined ? "None" : intensity;
    const contextPart = context === null || context === undefined ? "" : context;
    const seed = stableSeed(`${day}:${style}:${mood}:${intensityPart}:${contextPart}`);
    return generate({ style, mood, intensity, context, seed });
  }

  function todayIso() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const day = String(now.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  function formatLine(text) {
    return `${text.content} ${text.reference}`;
  }

  function render(text) {
    const contentEl = document.getElementById("verse-content");
    const referenceEl = document.getElementById("verse-reference");
    const metaEl = document.getElementById("verse-meta");
    const copyStatus = document.getElementById("copy-status");
    if (!contentEl || !referenceEl) {
      return;
    }
    contentEl.textContent = text.content;
    referenceEl.textContent = text.reference;
    if (metaEl) {
      metaEl.innerHTML = "";
      for (const label of [text.style, text.mood]) {
        const tag = document.createElement("span");
        tag.className = "tag";
        tag.textContent = label;
        metaEl.appendChild(tag);
      }
    }
    if (copyStatus) {
      copyStatus.textContent = "";
    }
  }

  function readOptions() {
    return {
      style: document.getElementById("opt-style")?.value || RANDOM_VALUE,
      mood: document.getElementById("opt-mood")?.value || RANDOM_VALUE,
      intensity: (() => {
        const value = document.getElementById("opt-intensity")?.value;
        return value ? Number(value) : null;
      })(),
      context: document.getElementById("opt-context")?.value || RANDOM_VALUE,
    };
  }

  function refreshDaily() {
    render(daily(readOptions()));
  }

  function refreshRandom() {
    render(generate(readOptions()));
  }

  async function copyCurrent() {
    const contentEl = document.getElementById("verse-content");
    const referenceEl = document.getElementById("verse-reference");
    const copyStatus = document.getElementById("copy-status");
    if (!contentEl || !referenceEl) {
      return;
    }
    const line = `${contentEl.textContent} ${referenceEl.textContent}`;
    try {
      await navigator.clipboard.writeText(line);
      if (copyStatus) {
        copyStatus.textContent = "已复制，可以去水群了。";
      }
    } catch (_error) {
      if (copyStatus) {
        copyStatus.textContent = "复制失败，请手动选中复制。";
      }
    }
  }

  globalThis.HolyWater = { generate, daily, stableSeed, Random };

  if (typeof document === "undefined") {
    return;
  }

  document.getElementById("btn-daily")?.addEventListener("click", refreshDaily);
  document.getElementById("btn-random")?.addEventListener("click", refreshRandom);
  document.getElementById("btn-copy")?.addEventListener("click", copyCurrent);
  ["opt-style", "opt-mood", "opt-intensity", "opt-context"].forEach((id) => {
    document.getElementById(id)?.addEventListener("change", refreshDaily);
  });

  refreshDaily();
})();
