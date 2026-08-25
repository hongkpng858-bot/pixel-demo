# B4 Creature Engine — Spec v1（俾文字 AI 讀）

任何語言模型都可以驅動呢個引擎：將用戶嘅自然語言譯做一份 JSON spec，
行一條命令，就攞到 web-ready 動畫資產。純數學渲染，免費、離線、確定性。

## 命令

```bash
python3 generate.py '{"creature":"cat","seed":"mochi"}'
python3 generate.py --spec spec.json --out mypet   # 由檔案讀＋自訂輸出目錄
```

## Spec 格式（全部可選，除咗 creature 建議填）

```json
{
  "creature": "cat",              // 關鍵字，見下方詞表
  "action":   "walk",             // 該家族支援嘅動作；唔填用預設
  "seed":     "auto",             // "auto"=每次新隻 | 固定值（任何字串/數字）=永遠重現同一隻
  "speed":    "normal",           // slow | normal | fast
  "palette":  {"body": "#56c466"},// 可選 hex 覆寫（body）
  "bg":       "night"             // night=夜景底 | none=全透明 GIF
}
```

**Seed 規則（核心契約）：**
- `seed:"auto"` 或省略 → 每次運行生成全新外觀（新隻）
- `seed` 固定 → 同一隻角色永遠零偏差重現；sprite sheet 內 16 帧外觀一致
- 想用戶可以「再要返嗰隻」→ 將 seed 回傳俾佢記低

## 關鍵字詞表 creature → 家族

| 關鍵字 | 家族 | 預設動作 |
|---|---|---|
| slime/jelly/blob/goo | blob | hop |
| ghost/spirit/wraith | ghost | float |
| cat/kitten/neko | quad | walk |
| dog/puppy/shiba | quad | walk |
| wolf | quad | walk |
| fox | quad | walk |
| bird/parrot/chick | bird | fly |
| fish/goldfish | fish | swim |
| bug/beetle/spider | bug | walk |
| snake/serpent | serpent | slither |
| dragon | serpent | slither |
| knight/soldier/hero | biped | walk |
| human/person/walker | biped | walk |
| robot/mech/bot | biped | walk |

## 各家族動作

- blob: `hop`(預設) `bounce` `idle`
- ghost: `float`(預設) `drift` `haunt`
- quad: `walk`(預設) `run` `stroll`
- bird: `fly`(預設) `soar` `flutter`
- fish: `swim`(預設) `dart` `drift`
- bug: `walk`(預設) `scuttle`
- serpent: `slither`(預設) `hunt` `laze`
- biped: `walk`(預設) `march` `run`

動作唔存在時自動跌返預設，唔會報錯。

## 自然語言 → spec 翻譯指引（俾 LLM）

1. 抓生物關鍵字 → `creature`（中文都得：「貓」→cat、「龍」→dragon）
2. 動詞／動作描述 → 最接近嘅 action；「慢慢」→ speed slow、「快速」→ fast
3. 顏色詞 → palette.body hex（「紫色」→ #9b7fd4）；毛色風格詞留俾 seed 處理
4. 用戶冇指定 seed 就用 auto；有「同之前一樣」就填返之前個 seed
5. 幽靈類背景建議 none；地面生物預設 night 有落地感

例：
- 「一隻好慢嘅白色鬼魂」→ `{"creature":"ghost","action":"drift","palette":{"body":"#f0f0f5"},"bg":"none"}`
- 「橙貓跑得好快」→ `{"creature":"cat","action":"run","speed":"fast","seed":"auto"}`

## 輸出合約（同手造生成器完全一致）

`out/<name>/` 入面四件嘢：
- `<name>.gif` — 16 帧循環 GIF 預覽
- `<name>_sheet.png` — 透明橫向 sprite strip，16 × 32×32
- `<name>_sheet@8x.png` — 同 strip 放大 8x（web 直接用）
- `<name>.json` — metadata：fps/frameCount/resolvedSeed/files

`<name>` 格式：`<species>-<action>-<tag>`；auto seed 嘅 tag 含流水號，固定 seed 嘅 tag 係 seed hash 前 6 位。
stdout 一行總結含 seed 同 QA（motion peak/avg，PASS/FAIL）。

## 品質保證（已驗證 2026-08-25）

- 14 個物種全部 QA PASS（peak≥20px、avg≥5px、循環無跳帧）
- 固定 seed 重跑：0 像素差異（數學上可重現）
- auto seed：每次運行外觀必然唔同（1734 px 差異實測）
