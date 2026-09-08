"""Rectify the DJI overhead into plan view (100 px/m). Corner pixels picked on DJI_20260907184453_0183_D.JPG."""
import numpy as np, re, sys
from PIL import Image, ImageDraw, ImageFont
src_txt = open('plan.py').read()
W = 22.8; LEFT_H = 10.2; H = 10.2 - 0.53 + 5.7
PX = 100
src = Image.open('photo/dji/DJI_20260907184453_0183_D.JPG')
pairs = [((W, 0), (776, 2137)), ((0, 0), (3326, 2132)), ((W, H), (687, 504)), ((0, LEFT_H), (3305, 975))]
A, b = [], []
for (X, Y), (u, v) in pairs:
    x, y = X * PX, Y * PX
    A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.append(u)
    A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); b.append(v)
coef = np.linalg.solve(np.array(A, float), np.array(b, float))
out = src.transform((int(W * PX), int(H * PX + 150)), Image.PERSPECTIVE, tuple(coef), Image.BICUBIC)
out.save('photo/base_rectified.jpg', quality=82)
g = out.copy(); d = ImageDraw.Draw(g); font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 34)
for m in range(0, int(W) + 1):
    x = m * PX; d.line([(x, 0), (x, g.height)], fill=(255, 255, 0) if m % 5 else (255, 80, 0), width=2 if m % 5 else 4); d.text((x + 4, 4), str(m), fill=(255, 255, 0), font=font)
for m in range(0, int(H) + 2):
    y = m * PX; d.line([(0, y), (g.width, y)], fill=(255, 255, 0) if m % 5 else (255, 80, 0), width=2 if m % 5 else 4); d.text((4, y + 4), str(m), fill=(255, 255, 0), font=font)
g.save('photo/base_grid.jpg', quality=85)
print('rectified', out.size)
