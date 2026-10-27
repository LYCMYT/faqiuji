#!/usr/bin/env python3
"""Draw the reviewed nominal CAD contact geometry; no generated product imagery.

Run with matplotlib, numpy and PyMuPDF available:
    python figures/create_cradle_diagram.py
"""
from pathlib import Path
import tempfile
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Circle, Polygon, Rectangle
import fitz

target = Path(__file__).resolve().parent
font_file = Path(tempfile.gettempdir()) / 'bm1-review-cjk-font.ttf'
font_file.write_bytes(fitz.Font('china-s').buffer)
font_manager.fontManager.addfont(str(font_file))
plt.rcParams.update({
    'font.family': font_manager.FontProperties(fname=str(font_file)).get_name(),
    'axes.unicode_minus': False,
    'font.size': 11,
    'figure.facecolor': '#f7f9fc',
    'axes.facecolor': 'white',
    'text.color': '#182a3a',
    'axes.labelcolor': '#3e5062',
})
navy, blue, teal, red, slate = '#193d5b', '#dcebf5', '#188d81', '#c74942', '#8395a5'
fig, axes = plt.subplots(1, 2, figsize=(14.5, 7.0), gridspec_kw={'width_ratios': [1, 1.18]})
fig.subplots_adjust(top=.78, bottom=.22, left=.06, right=.97, wspace=.28)
fig.text(.06, .94, 'R3 开夹接球：无相交，仍缺少稳定承托', fontsize=21, color=navy)
fig.text(.06, .88, 'ST03 名义参考几何  |  当前审查提交 c8c52514  |  单位：mm', fontsize=11, color='#526579')

ax = axes[0]
r, offset = 13.25, 5.5
ax.add_patch(Circle((0, 0), r, facecolor=blue, edgecolor=navy, linewidth=1.8))
ys = np.linspace(-np.sqrt(r*r-offset*offset), np.sqrt(r*r-offset*offset), 300)
xs = np.sqrt(r*r-ys*ys)
poly = np.vstack([np.column_stack((xs, ys)), [offset, ys[-1]], [offset, ys[0]]])
ax.add_patch(Polygon(poly, closed=True, facecolor=teal, alpha=.85, edgecolor=teal))
ax.plot([offset, offset], [ys[0], ys[-1]], color=teal, lw=2)
ax.plot([0, 0], [-15, 15], linestyle=':', lw=1, color=slate)
ax.plot([-15, 15], [0, 0], linestyle=':', lw=1, color=slate)
ax.scatter([0], [0], s=45, color=red, zorder=5)
ax.annotate('球心轴投影', xy=(0, 0), xytext=(-14, 7), fontsize=11,
            arrowprops=dict(arrowstyle='->', color=red), color=red)
ax.annotate('底部接触区\n134.324 mm²', xy=(9.1, -4.7), xytext=(-13.3, -10.5),
            fontsize=10.5, arrowprops=dict(arrowstyle='->', color=teal), color=teal)
ax.annotate('', xy=(offset, 3), xytext=(0, 3),
            arrowprops=dict(arrowstyle='<->', color=red, lw=1.4))
ax.text(offset/2, 4.4, '5.5', color=red, ha='center', fontsize=12)
ax.set_title('A  球底俯视：轴投影在接触区外', loc='left', pad=15, fontsize=13, color=navy)
ax.set_xlim(-18, 18); ax.set_ylim(-17, 17); ax.set_aspect('equal')
ax.set_xlabel('相对球心轴 X'); ax.set_ylabel('Y')
ax.set_xticks([-13.25, 0, 5.5, 13.25]); ax.set_yticks([-13.25, 0, 13.25])

ax = axes[1]
ax.add_patch(Rectangle((-r, -13), 2*r, 26, facecolor=blue, edgecolor=navy, lw=1.7))
# Cradle section shown in the central notch; left remote platform omitted.
ax.add_patch(Polygon([(-23,-18),(15,-18),(15,-13),(5.5,-13),(5.5,-16),(-23,-16)],
                     closed=True, facecolor='#c4d0da', edgecolor=slate, lw=1.6))
ax.add_patch(Rectangle((-16.5,-13),3,12,facecolor='#9bacbb',edgecolor=slate,lw=1.2))
ax.plot([5.5,13.25],[-13,-13],color=teal,lw=4,solid_capstyle='butt')
ax.plot([0,0],[-15,14],linestyle=':',color=red,lw=1.2)
ax.annotate('',xy=(0,-10),xytext=(0,5),arrowprops=dict(arrowstyle='-|>',color=red,lw=2))
ax.text(1.1,4,'重力方向',color=red,fontsize=11)
ax.text(-9,10,'名义球头剖面',fontsize=11,color=navy)
ax.annotate('后推头\n间隙 0.25',xy=(-13.4,-3.5),xytext=(-25.5,4),
            fontsize=10,arrowprops=dict(arrowstyle='->',color=slate))
ax.annotate('托体中央槽底 -16',xy=(-7,-16),xytext=(-20,-23.5),
            fontsize=10,arrowprops=dict(arrowstyle='->',color=slate))
ax.annotate('支撑台阶 -13',xy=(10,-13),xytext=(11,-5),
            fontsize=10,arrowprops=dict(arrowstyle='->',color=teal),color=teal)
ax.scatter([5.5],[-13],color=teal,s=24,zorder=5)
ax.set_title('B  轴向剖面：中央槽低于球底 3 mm',loc='left',pad=15,fontsize=13,color=navy)
ax.set_xlim(-27,27); ax.set_ylim(-27,17); ax.set_aspect('equal')
ax.set_xlabel('相对球心轴 X'); ax.set_ylabel('Z')
ax.set_xticks([-13.25,0,5.5,13.25]); ax.set_yticks([-16,-13,0,13])
for axis in axes:
    axis.spines[['top','right']].set_visible(False)
    axis.spines[['left','bottom']].set_color('#b9c8d3')
    axis.tick_params(colors='#526579',labelsize=9)

fig.text(.06,.13,'几何含义：当前直立参考姿态缺少稳定的底部承托，接球基准需要重新设计。',fontsize=13,color=navy)
fig.text(.06,.085,'证据边界：示意图省略羽裙与其他零件；完整小扰动探针包含球头、羽裙和 155 个台架实例。',fontsize=10.5,color='#526579')
fig.text(.06,.052,'这里不预测实球最终倾斜角度、卡球或损伤；真实曲面、摩擦、质量分布与冲击仍需测量。',fontsize=10.5,color='#526579')
fig.savefig(target/'cradle_support_review.png',dpi=170,facecolor=fig.get_facecolor())
fig.savefig(target/'cradle_support_review.svg',facecolor=fig.get_facecolor())
plt.close(fig)
print(target/'cradle_support_review.png')
