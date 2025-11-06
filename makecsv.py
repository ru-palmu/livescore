#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ライブギフト集計結果の JSON ファイル群から CSV ファイルを作成する。
また，散布図も作成できる。
"""

import csv
import sys
import io
import math
import operator
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from common import is_excluded, ru_model, ru_model_x, readJsons, limitedJsons
from common import set_ru_model, comma_formatter
import re
from typing import Callable

plt.switch_backend('Agg')
plt.rcParams["font.family"] = "Noto Sans CJK JP"


def row_append_float(row, v: float, m: int = 1):
  if m == 3:
    row.append(f'{v:.3f}')
  elif m == 2:
    row.append(f'{v:.2f}')
  elif m == 1:
    row.append(f'{v:.1f}')
  elif m == 0:
    row.append(int(v))
  else:
    raise Exception(f"invalid m: {m}")


def write_csv_file(fp, jsons: dict):
  writer = csv.writer(fp)
  if True:
    writer.writerow(['label', 'gift', 'livescore', '3xgift', '(ru)',
                     'score/gift', '(ru)/gift',
                     'rank', 'following', 'followers',
                     'max', '>= 1k', '>= 100', '>= 10', '>= 1', '>= 0',
                     'avg>=5', 'avg>=0',
                     'median>=5', 'median>=0',
                     'top1_ratio', 'top3_ratio', 'top5_ratio',
                     'top5%_ratio', 'top10%_ratio'])

  for dirname, data_list in jsons.items():
    for data in data_list:
      write_csv_row(writer, data)


def write_csv_row(writer, data: dict):
  gifts = np.array(data.get('gift', []))
  livescore = int(data.get('livescore', 0))
  total_gift = data.get('total_gift', np.sum(gifts))
  if total_gift == 0:
    raise Exception(f"0 total_gift: {data}")

  ru_score = ru_model(total_gift)
  row = [data.get('label', data['filename']),
         total_gift,
         livescore,
         total_gift * 3,
         ru_score,
         f'{livescore / total_gift:.3f}',
         f'{ru_score / total_gift:.3f}',
         ]

  for k in ['user_rank', 'following', 'followers']:
    row.append(data.get(k, ''))
  row.append(max(gifts))
  # p コイン以上のギフト人数
  for p in [1000, 100, 10, 1, 0]:
    row.append(np.sum(gifts >= p))

  # 5コイン以上のギフト平均
  gifts5 = gifts[gifts >= 5]
  row_append_float(row, np.sum(gifts5) / len(gifts5), 1)
  # 0コイン以上のギフト平均
  row_append_float(row, np.sum(gifts) / len(gifts), 1)

  # 5コイン以上のギフト中央値
  row.append(int(np.median(gifts5)))
  row.append(int(np.median(gifts)))

  # 1位のギフト割合
  for n in [1, 3, 5]:
    row_append_float(row, 100 * np.sum(gifts[:n]) / total_gift, 1)

  # top5%
  gifts_top5 = gifts[:math.ceil(len(gifts) * .05)]
  gifts_top10 = gifts[:math.ceil(len(gifts) * .10)]

  row_append_float(row, 100 * np.sum(gifts_top5) / total_gift, 1)
  row_append_float(row, 100 * np.sum(gifts_top10) / total_gift, 1)

  writer.writerow(row)


def get_sorted_xy(jsons: dict, slicer: Callable) -> list:
  """(total_gift, livescore) のリストを取得し，
  total_gift でソートして返す。
  """
  xy = []
  for dirname, data_list in jsons.items():
    for data in data_list:
      livescore = int(data.get('livescore', 0))
      total_gift = data.get('total_gift', 0)
      if total_gift == 0:
        continue
      xy.append((total_gift, livescore, data, slicer(data)))

  # x でソートする
  xy = sorted(xy, key=lambda v: v[0])
  return xy


def _get_operator(dimension: str):
  compares = {'<': operator.lt,
              '>': operator.gt,
              '=': operator.eq}
  if dimension[0] not in compares:
    return operator.eq, dimension
  return compares[dimension[0]], dimension[1:]


def slice_dimension(dimension) -> Callable:
  """はねていないデータ群

  returns func(json_data) -> bool

  >>> f = slice_dimension("rankS")
  >>> f({'user_rank': 'S'})
  True
  """

  if not dimension:
    return lambda d: True
  elif dimension == "exclude":
    return lambda d: not is_excluded(d['total_gift'], d['livescore'])
  elif not isinstance(dimension, str):
    raise Exception(f"invalid dimension type: {type(dimension)}")

  compare, dimension = _get_operator(dimension)

  f = lambda d: True
  ctype = int
  if re.fullmatch(r'20\d\d[01]\d[0-3]\d', dimension):
    key = 'date'
    value = int(dimension)
  elif re.fullmatch(r'score\d+', dimension):
    key = 'livescore'
    value = int(dimension[5:])
  elif re.fullmatch(r'100(coin|gift)\d+', dimension):
    key = '100coin'
    value = int(dimension[7:])
  elif re.fullmatch(r'10(coin|gift)\d+', dimension):
    key = '10coin'
    value = int(dimension[6:])
  elif re.fullmatch(r'100(coin|gift)\d+-\d+', dimension):
    key = '10coin'
    value = int(dimension.split('-')[1])
    value2 = int(dimension.split('-')[0][7:])
    f = lambda d: d['100coin'] == value2
  elif re.fullmatch(r'20\d\d[01]\d[0-3]\d-\d+', dimension):
    key = 'rank'
    value = int(dimension.split('-')[1])
    value2 = int(dimension.split('-')[0])
    f = lambda d: int(d.get('date', 0)) == value2
  elif re.fullmatch(r'rank[ABCDS][12345S]?', dimension):
    ctype = str
    key = 'user_rank'
    value = dimension[4:]
  else:
    raise Exception(f"invalid dimension: {dimension}")

  return lambda d: (compare(ctype(d.get(key, 0)), value) and f(d))


def get_xyinvalid(xy: list) -> set:
  xinvalid = set()
  for i, (total_gift, livescore, _) in enumerate(xy):
    if is_excluded(total_gift, livescore):
      # 無効データ
      xinvalid.add(i)
    elif livescore / total_gift < 3 and total_gift < 20_000:
      print(f"#invalid: gift={total_gift}, livescore={livescore}")
      print("total_gift=", total_gift)
      print("livescore=", livescore)
      print("livescore / totalgift =", livescore / total_gift,)
      print("-3*total_gift/130000 + 3 =",
            -3 * total_gift / 130_000 + 3)
  return xinvalid


def get_ylim_ax1(xlim):
  if xlim < 200_00:
    ylim = 3 * xlim
  elif xlim < 300_00:
    ylim = 2.9 * xlim
  else:
    ylim = 2.8 * xlim


def set_xylim_ax1(ax1, xlim, ylim):
  """左軸の x/y 軸範囲を設定する。
  """
  if xlim:
    ax1.set_xlim(0, xlim)
    if not ylim:
      ylim = get_ylim_ax1(xlim)
  else:
    ax1.set_xlim(0, None)
  if ylim:
    ax1.set_ylim(0, ylim)
  else:
    ax1.set_ylim(0, None)
  return ylim


def plot_rank_zones(ax2, xlim, ymin: float, zorder=0):
  assert isinstance(ymin, float), ymin
  obi = {
      # (min_+2, max_+6, color, max_+2, max_+4, xlim_max)
      'SS': (1, 300_000, 810_000, 1_800_000),
      'S': (0, 174_000, 430_000, 900_000),
      'A5': (4, 130_000, 340_000, 730_000),
      'A4': (3, 90_000, 220_000, 510_000),
      'A3': (2, 70_000, 170_000, 360_000),
      'A2': (1, 60_000, 120_000, 250_000),
      'A1': (0, 45_000, 80_000, 160_000),
      'B3': (4, 20_000, 50_000, 90_000),
      'B2': (3, 12_000, 35_000, 80_000, 101_000),
      'B1': (2, 12_000, 30_000, 65_000, 101_000),
      'C3': (1, 4_000, 10_000, 15_000, 61_000),
      'C2': (0, 1600, 4200, 10_000, 61_000),
      'C1': (4, 600, 1500, 4200, 51_000),
  }

  colors = ['#FFB6C1', '#FFD700', '#B0E0E6', '#98FB98', '#DDA0DD']

  for rank, border in obi.items():
    if len(border) == 4:
      i, s2, s4, s6 = border
      xlim_max = None
    else:
      i, s2, s4, s6, xlim_max = border
    x2 = s2 / 3
    x4 = s4 / 3
    x6 = s6 / 3
    color = colors[i]
    y1 = ymin + 0.01 + i * 0.02
    y2 = y1 + 0.01

    if xlim_max and xlim >= xlim_max:
      continue
    if xlim <= x2:
      continue

    ax2.fill_betweenx(
        [y1, y2],
        x2, x4,
        color=color,
        alpha=0.8,
        zorder=zorder,
    )
    ax2.fill_betweenx(
        [y1, y2],
        x4, x6,
        color=color,
        alpha=0.4,
        zorder=zorder,
    )

    if x6 > xlim:
      x6 = xlim
    xx = x2 + (x6 - x2) / 2

    # ラベル
    ax2.text(
        x=xx,
        y=y1 + 0.005,
        s=rank,
        color='black',
        fontsize=10,
        fontweight='bold',
        horizontalalignment='center',
        verticalalignment='center',
        zorder=zorder,
    )


def write_scatter(fname: str, jsons: dict,
                  plot_livescore: bool = True,
                  plot_rate: bool = True,
                  plot_model: bool = True,
                  plot_3xmodel: bool = True,
                  xlim=None, ylim=None, title: str = '',
                  ymin: float = 2.4, ymax: float = 3.5,
                  dimension=None):

  fig, ax1 = plt.subplots()

  ax2 = ax1.twinx()

  # カンマ区切りフォーマット
  ax1.yaxis.set_major_formatter(FuncFormatter(comma_formatter))
  ax1.xaxis.set_major_formatter(FuncFormatter(comma_formatter))

  ax1.set_xlabel('Gift (Coin)')
  ax1.set_ylabel('Live Score')
  ax2.set_ylabel('Live Score / Gift')

  slicer = slice_dimension(dimension)
  xy = get_sorted_xy(jsons, slicer)
  assert len(xy) > 0

  # ==================================
  # 散布図
  # ==================================

  xinvalid = [v[0] for v in xy if not v[3]]
  if plot_livescore:
    # 左軸：gift - livescore の散布図を描画する
    y_livescore = [v[1] for v in xy if not v[3]]
    ax1.scatter(xinvalid, y_livescore,
                color='#1f77b4', alpha=0.8, s=2, zorder=8,
                marker='.')

  if plot_rate:
    # 右軸：livescore / gift の散布図を描画する
    y_livescore_per_gift_invalid = [v[1] / v[0] for v in xy if not v[3]]
    ax2.scatter(xinvalid, y_livescore_per_gift_invalid,
                color='#FFCC00', alpha=0.8, s=2, zorder=8,
                marker='.')

  xvalid = [v[0] for v in xy if v[3]]
  edgecolors = 'face'
  linewidths = None
  s = 2
  if len(xinvalid) > 0:
    edgecolors = 'black'
    if len(xvalid) < 10:
      s = 20
    else:
      s = 5

  if plot_livescore:
    # 左軸：gift - livescore の散布図を描画する
    y_livescore = [v[1] for v in xy if v[3]]
    ax1.scatter(xvalid, y_livescore,
                label='Real score',
                color='#1f77b4', alpha=0.3, s=s, marker="o",
                edgecolors=edgecolors, linewidths=linewidths,
                zorder=10)
  if plot_rate:
    # 右軸：livescore / gift の散布図を描画する
    y_livescore_per_gift = [v[1] / v[0] for v in xy if v[3]]
    label = 'Real score / gift'
    if dimension:
      label += f' ({dimension})'
    if len(xvalid) != len(xy):
      label += f' [{len(xvalid)}/{len(xy)}]'
    else:
      label += f' [{len(xy)} samples]'

    ax2.scatter(xvalid, y_livescore_per_gift, label=label,
                color='#FFCC00', alpha=0.3, s=s, marker='o',
                edgecolors=edgecolors, linewidths=linewidths,
                zorder=10)

  # ==================================
  # モデル線
  # ==================================
  x = [v[0] for v in xy]
  xmin = 0
  xmax = x[-1] * 1.05
  if plot_livescore and plot_3xmodel:
    # 左軸：gift - livescore のモデル線を描画する

    # 旧モデル (３倍）
    x_3 = [xmin, xmax]
    y = [3 * v for v in x_3]
    ax1.plot(x_3, y, label='3x gift',
             color='#d62728', linestyle='dashed',
             zorder=3, alpha=0.3)

  if plot_livescore and plot_model:
    # 新モデル
    x_r = ru_model_x(xmin, xmax)
    y = [ru_model(v) for v in x_r]
    ax1.plot(x_r, y, label='(ru) model',
             color='#2ca02c',
             zorder=3, alpha=0.3)

  if plot_rate and plot_model:
    # 右軸：livescore / gift のモデル線を描画する
    x_r = ru_model_x(xmin, xmax)
    y = [ru_model(v) / v for v in x_r]
    ax2.plot(x_r, y, label='(ru) model score / gift',
             color='#2ca02c', linestyle='-.',
             zorder=3, alpha=0.3)

  # x/y 軸を原点交差
  # ax1.spines['left'].set_position('zero')
  # ax1.spines['bottom'].set_position('zero')
  # ax2.spines['bottom'].set_color('none')
  # ax2.spines['left'].set_color('none')

  # ==================================
  # ランク帯塗りつぶし
  # ==================================
  set_xylim_ax1(ax1, xlim or xmax, ylim)
  xlim2 = xlim if xlim else xmax
  plot_rank_zones(ax2, xlim2, ymin, zorder=1)

  ax2.set_ylim(ymin, ymax)

  yticks = np.arange(0.8, 4, 0.2)
  ax2.set_yticks([v for v in yticks if ymin < v < ymax])

  ax1.set_zorder(2)
  ax2.set_zorder(1)
  ax1.patch.set_visible(False)

  ax1.set_title(title)
  fig.legend(loc='upper center', bbox_to_anchor=(0.5, 0.93), ncol=1)

  if not plot_rate:
    plt.draw()  # 自動スケーリング

    x_ticks = ax1.get_xticks()
    y_ticks = 3 * x_ticks
    ax1.set_yticks(y_ticks)
    ax1.grid(True, color='#DDDDDD', linestyle='-', alpha=0.3)

  ax1.grid(not plot_rate)
  ax2.grid(plot_rate)
  fig.tight_layout()
  fig.savefig(fname)
  plt.close(fig)


def main():
  import argparse

  parser = argparse.ArgumentParser(description='')
  parser.add_argument('args', nargs='+', help="input json files")
  parser.add_argument('-f', help="output csv file; default STDOUT")
  parser.add_argument('--scatter', help="output scatter.png file")
  parser.add_argument('--dimension', help="dimension to slice",
                      default="", type=str)
  parser.add_argument('-x', '--xlim', type=int,
                      help="Maximum value for the x-axis limit")
  parser.add_argument('-y', '--ylim', type=int,
                      help="Maximum value for the y-axis limit (left)")
  parser.add_argument('--ymin', type=float, default=2.4,
                      help="Minimum value for the y-axis limit (right)")
  parser.add_argument('--ymax', type=float, default=3.5,
                      help="Maximum value for the y-axis limit (right)")
  parser.add_argument('-t', '--title',
                      help="title for scatter plot")
  parser.add_argument('--enc', choices=['utf-8', 'shift_jis'],
                      default='shift_jis',
                      help="output file encoding; default shift_jis")
  parser.add_argument('--no-livescore', action='store_true',
                      help="do not plot live score")
  parser.add_argument('--no-rate', action='store_true',
                      help="do not plot live score / gift rate")
  parser.add_argument('--no-model', action='store_true',
                      help="do not plot model")
  parser.add_argument('--no-3x', action='store_true',
                      help="do not plot 3x gift model")
  parser.add_argument('--ru-model', type=int, choices=[0, 1, 2, 3],
                      default=0)
  parser.add_argument('--doctest', action='store_true')

  args = parser.parse_args()

  if args.doctest:
    import doctest
    doctest.testmod()
    return 0

  set_ru_model(args.ru_model)
  if args.f:
    fp = open(args.f, 'w', encoding=args.enc, newline='')
  else:
    fp = io.TextIOWrapper(sys.stdout.buffer, encoding=args.enc, newline='')

  # #############################
  # 引数解析
  # #############################
  jsons = readJsons(args.args)
  if len(jsons) == 0:
    print("no valid json data")
    return 1

  # #############################
  # csv 出力
  # #############################
  write_csv_file(fp, jsons)

  if args.scatter:
    # 描画に不要なデータは先に削除
    jsons = limitedJsons(jsons, None, args.xlim, args.ymin, args.ymax)

    write_scatter(args.scatter, jsons,
                  plot_livescore=not args.no_livescore,
                  plot_rate=not args.no_rate,
                  plot_model=not args.no_model,
                  plot_3xmodel=not args.no_3x,
                  xlim=args.xlim, ylim=args.ylim,
                  ymin=args.ymin, ymax=args.ymax,
                  title=args.title if args.title else '',
                  dimension=args.dimension)


if __name__ == '__main__':
  main()


# vim:set et ts=2 sts=2 sw=2 tw=80:
