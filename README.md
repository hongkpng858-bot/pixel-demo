# Pixel Animation Lab

自足式 pixel 動畫生成項目：Python 骨架運動學 → sprite sheet → 靜態網頁。
**唔依賴任何特定 AI / 平台 / framework。**

## 快速開始

```bash
pip install Pillow        # 唯一依賴
./build.sh                # 重新生成全部動畫 + QA 驗收
python3 -m http.server 8090   # 本地預覽（可選）
```

## 檔案

| 檔案 | 說明 |
|---|---|
| `index.html` | 動畫展示頁（Pause / Zoom / 速度控制） |
| `make_slime.py` | 史萊姆跳跳 generator |
| `make_walker.py` | 骨架小人行路 generator（FK rig 範本） |
| `verify.py` | QA：驗證有郁 + 循環無縫 |
| `*_sheet.png` | 遊戲引擎用 sprite strip（透明 RGBA，邏輯尺寸） |
| `*_sheet@8x.png` | 網頁用預放大版本 |
| `*.json` | 每個動畫嘅帧數／尺寸／fps 元數據 |

## 部署去你自己個 domain

呢個資料夾就係一個完整 static site root。三種常見做法：

**A. 免費靜態 hosting（最快）**
1. 將成個資料夾 push 上 GitHub
2. GitHub Pages / Netlify / Cloudflare Pages 揀個資料夾做 root
3. Domain 加一條 CNAME 指去佢俾你嘅網址，完成

**B. 自己 VPS**
```bash
rsync -av --exclude='*.py' --exclude='build.sh' pixel-demo/ user@server:/var/www/pixel/
# nginx server block: root /var/www/pixel;
```

**C. 純 CDN**：其實淨係上 `index.html` + `*_sheet@8x.png` 都得，其他檔案係生成用。

## 之後想加動畫？

睇 [`AGENTS.md`](AGENTS.md)——無論邊個 AI agent 接手，照住份合約做就得。人類都啱讀。
