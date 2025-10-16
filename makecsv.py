#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
"""

import csv
import json
import sys
import io
import math
import numpy as np


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


def main():
  import argparse

  parser = argparse.ArgumentParser(description='')
  parser.add_argument('args', nargs='+', help="input json files")
  parser.add_argument('-f', help="output file; default STDOUT")
  parser.add_argument('--enc', choices=['utf-8', 'shift_jis'],
                      default='shift_jis',
                      help="output file encoding; default shift_jis")
  args = parser.parse_args()

  if args.f:
    fp = open(args.f, 'w', encoding=args.enc, newline='')
  else:
    fp = io.TextIOWrapper(sys.stdout.buffer, encoding=args.enc, newline='')

  writer = csv.writer(fp)
  if True:
    writer.writerow(['label', 'gift', 'livescore', '3xgift', 'score/gift',
                     'max', '>= 1k', '>= 100', '>= 10', '>= 1', '>= 0',
                     'avg>=5', 'avg>=0',
                     'median>=5', 'median>=0',
                     'top1_ratio', 'top3_ratio', 'top5_ratio',
                     'top5%_ratio', 'top10%_ratio'])

  for fname in args.args:
    if not fname.endswith('.json'):
      continue
    print(fname, file=sys.stderr)
    with open(fname, 'r', encoding='utf-8') as f:
      data = json.load(f)

    gifts = np.array(data.get('gift', []))
    livescore = int(data.get('livescore', 0))
    total_gift = np.sum(gifts)
    if total_gift == 0:
      raise Exception(f"0 total_gift: {data}")

    row = [data.get('label', fname),
           total_gift,
           livescore,
           total_gift * 3,
           f'{livescore / total_gift:.3f}',
           max(gifts),
           ]
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


if __name__ == '__main__':
  main()


# vim:set et ts=2 sts=2 sw=2 tw=80:
