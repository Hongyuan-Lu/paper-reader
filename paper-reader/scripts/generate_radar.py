#!/usr/bin/env python3
"""生成论文多维雷达评分图（中文版）"""
import matplotlib.pyplot as plt
import numpy as np
import json
import sys
import matplotlib
import os

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

def generate_radar_chart(scores, output_path='radar_score.png'):
    """生成中文雷达评分图"""
    categories = [
        '期刊/会议等级',
        '创新性',
        '实验充分性',
        '方法严谨性',
        '复现友好度'
    ]

    values = [
        scores.get('journal_level', 5),
        scores.get('innovativeness', 5),
        scores.get('experimental_rigor', 5),
        scores.get('methodological_rigor', 5),
        scores.get('reproducibility', 5)
    ]

    total = sum(values)
    overall_rating = round(total / 10, 1)
    stars_full = int(overall_rating)
    stars_half = 1 if (overall_rating - stars_full) >= 0.5 else 0
    stars_empty = 5 - stars_full - stars_half
    stars = '★' * stars_full + '☆' * stars_empty

    values += values[:1]
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))

    # 绘制雷达区域和边界
    ax.plot(angles, values, 'o-', linewidth=2.5, color='#2196F3', markersize=8)
    ax.fill(angles, values, alpha=0.25, color='#2196F3')

    # 设置中文标签
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, size=13, fontweight='bold')

    # 设置径向刻度
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(['2', '4', '6', '8', '10'], color='grey', size=10)

    # 在每个点上显示数值
    for angle, val in zip(angles[:-1], values[:-1]):
        ax.text(angle, val + 0.4, str(int(val)), ha='center', va='center',
                fontsize=12, fontweight='bold', color='#1565C0')

    # 标题
    ax.set_title(f'论文综合评级  {stars}  {overall_rating}/5\n五维评分详情',
                 size=16, fontweight='bold', pad=30)

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    return overall_rating

if __name__ == '__main__':
    if len(sys.argv) < 2:
        # 默认测试评分
        scores = {
            'journal_level': 7,
            'innovativeness': 8,
            'experimental_rigor': 8,
            'methodological_rigor': 7,
            'reproducibility': 6
        }
    else:
        scores = json.loads(sys.argv[1])

    output = sys.argv[2] if len(sys.argv) > 2 else 'radar_score.png'
    rating = generate_radar_chart(scores, output)
    print(f"雷达图已生成: {output} (综合评级: {rating}/5)")