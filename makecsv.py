#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
"""

import csv
import json
import sys
import io
import numpy as np


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
                     'max', '>= 1k', '>= 100', '>= 10', '>= 1', '>= 0'])

  for fname in args.args:
    if not fname.endswith('.json'):
      continue
    print(fname, file=sys.stderr)
    with open(fname, 'r', encoding='utf-8') as f:
      data = json.load(f)

    gifts = np.array(data.get('gift', []))
    livescore = int(data.get('livescore', 0))
    gift = np.sum(gifts)

    row = [data.get('label', fname),
           gift,
           livescore,
           gift * 3,
           livescore / gift,
           max(gifts),
           np.sum(gifts >= 1000),
           np.sum(gifts >= 100),
           np.sum(gifts >= 10),
           np.sum(gifts >= 1),
           np.sum(gifts >= 0),
          ]
    writer.writerow(row)


if __name__ == '__main__':
  main()


# vim:set et ts=2 sts=2 sw=2 tw=80:
