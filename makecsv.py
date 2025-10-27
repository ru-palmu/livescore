#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ライブギフト集計結果の JSON ファイル群から CSV ファイルを作成する。
また，散布図も作成できる。
"""

import csv
import json
import sys
import io
import math
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from common import is_excluded, ru_model
import re


def comma_formatter(x, pos):
  if x < 10000:
    return f"{int(x):,}"
  elif x < 1_000_000:  # K 表示
    suffix = 'K'
    value = x / 1000
  else:
    suffix = 'M'
    value = x / 1_000_000

  if value > 100:
    value_str = f"{int(value)}"
  elif value > 10:
    value_str = f"{value:.1f}".rstrip('0').rstrip('.')
  else:
    value_str = f"{value:.2f}".rstrip('0').rstrip('.')
  return f"{value_str}{suffix}"


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


def readJsons(fnames: list, xlim) -> dict:
  ret = {}
  for fname in fnames:
    if not fname.endswith('.json'):
      continue
    with open(fname, 'r', encoding='utf-8') as f:
      data = json.load(f)
    data['filename'] = fname
    if 'date' not in data:
      # ファイル名から日付を取得する
      path = Path(fname)
      date_str = path.parent.name
      data['date'] = date_str

    gifts = np.array(data.get('gift', []))
    data['total_gift'] = gifts.sum()
    if xlim and data['total_gift'] > xlim:
      continue

    # ディレクトリ名をキーにする
    path = Path(fname)
    key = path.parent.name
    if key not in ret:
      ret[key] = []
    ret[key].append(data)
  return ret


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
  total_gift = np.sum(gifts)
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


def get_sorted_xy(jsons: dict) -> list:
  """(total_gift, livescore) のリストを取得し，
  total_gift でソートして返す。
  """
  xy = []
  for dirname, data_list in jsons.items():
    for data in data_list:
      gifts = np.array(data.get('gift', []))
      livescore = int(data.get('livescore', 0))
      total_gift = np.sum(gifts)
      if total_gift == 0:
        continue
      xy.append((total_gift, livescore, data,))

  # x でソートする
  xy = sorted(xy, key=lambda v: v[0])
  return xy


def slice_dimension_xy(xy: list, dimension) -> set:
  """はねていないデータ群"""
  xinvalid = set()
  if not dimension:
    return xinvalid
  if dimension == "exclude":
    return get_xyinvalid(xy)
  if not isinstance(dimension, str):
    raise Exception(f"invalid dimension type: {type(dimension)}")

  if re.fullmatch(r'20\d\d[01]\d[0-3]\d', dimension):
    # 日付で区切る
    slicer = lambda d: d['date'] == dimension
  elif re.fullmatch(r'>20\d\d[01]\d[0-3]\d', dimension):
    date_limit = dimension[1:]
    slicer = lambda d: d['date'] > date_limit
  elif re.fullmatch(r'>=20\d\d[01]\d[0-3]\d', dimension):
    date_limit = dimension[2:]
    slicer = lambda d: d['date'] >= date_limit
  elif re.fullmatch(r'score\d+', dimension):
    score_limit = int(dimension[6:])
    slicer = lambda d: int(d.get('livescore', 0)) == score_limit
  elif re.fullmatch(r'>score\d+', dimension):
    score_limit = int(dimension[6:])
    slicer = lambda d: int(d.get('livescore', 0)) > score_limit
  elif re.fullmatch(r'<score\d+', dimension):
    score_limit = int(dimension[6:])
    slicer = lambda d: int(d.get('livescore', 0)) < score_limit
  elif re.fullmatch(r'[><=]?20\d\d[01]\d[0-3]\d-\d+', dimension):
    parts = dimension.split('-')
    if len(parts) != 2:
      date_limit = int(parts[0][1:])
    else:
      date_limit = int(parts[0])
    rank_limit = int(parts[1])
    if dimension[0] == '>':
      slicer = lambda d: (int(d['date']) == date_limit and
                          d.get('rank', 0) > rank_limit)
    elif dimension[0] == '<':
      slicer = lambda d: (int(d['date']) == date_limit and
                          d.get('rank', 0) < rank_limit)
    else:  # '='
      slicer = lambda d: (int(d['date']) == date_limit and
                          d.get('rank', 0) == rank_limit)
  else:
    raise Exception(f"invalid dimension: {dimension}")

  for i, (_, _, d) in enumerate(xy):
    if 'date' not in d:
      print(d)
    if not slicer(d):
      xinvalid.add(i)

  return xinvalid


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


def set_xylim_ax1(ax1, xlim, ylim, xmax):
  """左軸の x/y 軸範囲を設定する。
  """
  if xlim:
    ax1.set_xlim(0, xlim)
    if not ylim:
      ylim = 3 * xlim
  else:
    ax1.set_xlim(0, None)
  if ylim:
    ax1.set_ylim(0, ylim)
  else:
    ax1.set_ylim(0, None)
    xlim = xmax
  return xlim


def plot_rank_zones(ax2, xlim):
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
    y1 = 2.41 + i * 0.02
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
    )
    ax2.fill_betweenx(
        [y1, y2],
        x4, x6,
        color=color,
        alpha=0.4,
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
    )


def write_scatter(fname: str, jsons: dict,
                  plot_livescore: bool = True,
                  plot_rate: bool = True,
                  xlim=None, ylim=None, title: str = '',
                  dimension=None):

  fig, ax1 = plt.subplots()

  ax2 = ax1.twinx()

  # カンマ区切りフォーマット
  ax1.yaxis.set_major_formatter(FuncFormatter(comma_formatter))
  ax1.xaxis.set_major_formatter(FuncFormatter(comma_formatter))

  ax1.set_xlabel('Gift (Coin)')
  ax1.set_ylabel('Live Score')
  ax2.set_ylabel('Live Score / Gift')

  xy = get_sorted_xy(jsons)
  assert len(xy) > 0

  xinvalid = slice_dimension_xy(xy, dimension)

  # 散布図
  x = [v[0] for v in xy]
  y_livescore = [v[1] for v in xy]
  if plot_livescore:
    # 左軸：gift - livescore の散布図を描画する
    ax1.scatter(x, y_livescore,
                label='Real data (' + str(len(xy)) + ' samples)',
                color='#1f77b4', alpha=0.5, s=5)

  if plot_rate:
    # 右軸：livescore / gift の散布図を描画する
    xx = [xy[i][0] for i in xinvalid]
    y_livescore_per_gift_invalid = [xy[i][1] / xy[i][0] for i in xinvalid]
    ax2.scatter(xx, y_livescore_per_gift_invalid,
                color='#888888', alpha=0.5, s=3)

    xvalid = [xy[i] for i, v in enumerate(xy) if i not in xinvalid]
    xx = [v[0] for v in xvalid]
    y_livescore_per_gift = [v[1] / v[0] for v in xvalid]

    label = 'Real score / gift'
    if dimension:
      label += f' ({dimension})'

    if len(xx) < 10:
      ax2.scatter(xx, y_livescore_per_gift, label=label,
                  color='#FFCC00', alpha=0.9, s=10, marker='*')
    else:
      ax2.scatter(xx, y_livescore_per_gift, label=label,
                  color='#FFCC00', alpha=0.5, s=3)

  # 旧モデル
  xmax = x[-1]
  x = [0.1] + x + [xmax * 1.1]
  if plot_livescore:
    # 左軸：gift - livescore のモデル線を描画する
    y = [3 * v for v in x]
    ax1.plot(x, y, label='3x gift',
             color='#d62728', linestyle='dashed')

    # 新モデル
    y = [ru_model(v) for v in x]
    ax1.plot(x, y, label='(ru) model',
             color='#2ca02c')

  y = [ru_model(v) / v for v in x]
  if plot_rate:
    # 右軸：livescore / gift のモデル線を描画する
    ax2.plot(x, y, label='(ru) model score / gift',
             color='#2ca02c', linestyle='-.')

  # x/y 軸を原点交差
  # ax1.spines['left'].set_position('zero')
  # ax1.spines['bottom'].set_position('zero')
  # ax2.spines['bottom'].set_color('none')
  # ax2.spines['left'].set_color('none')

  xlim = set_xylim_ax1(ax1, xlim, ylim, xmax)

  ax2.set_ylim(2.4, 3.5)
  ax2.set_yticks([2.6, 2.8, 3.0, 3.2, 3.4])

  # ==================================
  # ランク帯塗りつぶし
  # ==================================
  plot_rank_zones(ax2, xlim)

  ax1.set_title(title)
  fig.legend(loc='upper center', bbox_to_anchor=(0.5, 0.93), ncol=1)
  ax1.grid(False)
  ax2.grid(True)
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
                      help="Maximum value for the y-axis limit")
  parser.add_argument('-t', '--title',
                      help="title for scatter plot")
  parser.add_argument('--enc', choices=['utf-8', 'shift_jis'],
                      default='shift_jis',
                      help="output file encoding; default shift_jis")
  parser.add_argument('--no-livescore', action='store_true',
                      help="do not plot live score")
  parser.add_argument('--no-rate', action='store_true',
                      help="do not plot live score / gift rate")

  args = parser.parse_args()

  if args.f:
    fp = open(args.f, 'w', encoding=args.enc, newline='')
  else:
    fp = io.TextIOWrapper(sys.stdout.buffer, encoding=args.enc, newline='')

  # #############################
  # 引数解析
  # #############################
  jsons = readJsons(args.args, args.xlim)
  if len(jsons) == 0:
    print("no valid json data")
    return 1

  # #############################
  # csv 出力
  # #############################
  write_csv_file(fp, jsons)

  if args.scatter:
    write_scatter(args.scatter, jsons,
                  plot_livescore=not args.no_livescore,
                  plot_rate=not args.no_rate,
                  xlim=args.xlim, ylim=args.ylim,
                  title=args.title if args.title else '',
                  dimension=args.dimension)


if __name__ == '__main__':
  main()


# vim:set et ts=2 sts=2 sw=2 tw=80:
