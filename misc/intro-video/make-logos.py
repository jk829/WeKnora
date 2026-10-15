"""根据 docs/images/logo.png 生成 assets/ 中的透明标志。

logo-light.png 保留原色，适合浅色背景；logo-dark.png 将海军蓝文字
改为奶油色，保留金色波纹，适合海军蓝背景。裁剪区域与首页一致：
x=0、y=208、宽 945、高 238。
"""
from pathlib import Path

from PIL import Image

here = Path(__file__).resolve().parent
src = Image.open(here.parents[1] / "docs/images/logo.png").convert("RGB").crop((0, 208, 945, 446))
w, h = src.size
light, dark = Image.new("RGBA", (w, h)), Image.new("RGBA", (w, h))
sp, lp, dp = src.load(), light.load(), dark.load()

for y in range(h):
    for x in range(w):
        r, g, b = sp[x, y]
        a = 255 - min(r, g, b)  # 计算相对于白色背景的覆盖率。
        if a < 4:
            lp[x, y] = dp[x, y] = (0, 0, 0, 0)
            continue
        f = a / 255
        rr, gg, bb = (int(max(0, min(255, (c - 255 * (1 - f)) / f))) for c in (r, g, b))
        lp[x, y] = (rr, gg, bb, a)
        dp[x, y] = (rr, gg, bb, a) if rr > bb + 40 else (246, 241, 232, a)

light.save(here / "assets/logo-light.png")
dark.save(here / "assets/logo-dark.png")
