# AGENTS.md — pixel-demo 交接合約

呢份文件係寫俾**任何**接手呢個項目嘅 AI agent 或人類。目標：就算原本嘅 agent 冇咗，都可以繼續生成、修改、擴充同一套 pixel 動畫系統。

## 目的

由代碼生成遊戲／網頁兩用嘅 pixel 動畫 sprite sheet。核心概念：**骨架驅動**（定義骨骼層級同關節角度，用正向運動學計出每帧畫面），唔係逐格手畫。

## 硬規則（唔准破）

1. **依賴上限**：生成只准 `python3` + `Pillow`。網頁只准靜態 HTML/CSS/vanilla JS。不准 framework、不准 npm、不准額外 build 工具。
2. **永遠唔好手改生成出嚟嘅 PNG/GIF**。要改嘢就改生成器參數，再跑 `./build.sh`。
3. **每個新動畫必須交齊**：
   - `make_<name>.py` → 輸出 `<name>_sheet.png`（RGBA 透明橫向 strip）
   - `<name>_sheet@8x.png`（最近鄰整數倍預放大，網頁直接用）
   - `<name>.json`：至少包含 `frameSize:[w,h]`、`frameCount`、`fps`、`loop:true`
   - GIF 預覽可選但建議
4. **完工前必須跑 `./build.sh`，要見到 `ALL PASS`** 先可以話搞掂。`verify.py` 會驗：(a) 動畫真係有郁（peak motion ≥ 20px）(b) 循環無縫（wrap diff 唔超標）。
5. **網頁播放慣例**：`.sprite` class + CSS 變數 `--logical`（邏輯像素）/ `--frames` / `--z`（整數倍縮放）；`image-rendering: pixelated`；`steps(N)` 逐格跳。參考 `index.html` 入面 slime/walker 兩個現成例子。
6. **所有路徑必須係相對路徑**。呢個資料夾隨時要可以直接做 static site root 部署。

## 點加一個新動畫（示例流程）

1. 抄 `make_walker.py` 做模板（佢有完整骨架 rig：骨盆→大腿→小腿、脊柱→頭、肩→上臂→前臂）。
2. 改 `pose(phase)` 入面嘅關節角度函數——呢個係唯一需要藝術判斷嘅位。
3. 跑 `./build.sh` 直到 ALL PASS。
4. 喺 `index.html` 加一張卡：copy 現有 card 結構，改 `.sprite <name>` 同 `--logical`/`--frames`。

## 環境筆記

- 呢個項目住喺 OpenClaw workspace 入面（WSL2 主機）。但佢**唔依賴 OpenClaw**——搬去任何 Linux/macOS 機，裝咗 Pillow 就跑得。
- 預覽 server：`python3 -m http.server 8090`（純方便，唔係必需，任何 static server 都得）。
