#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
scat-score.html に掲載する表を生成する．
"""

import sys
import re
from common import readJsons


def filters(jsons, num, coin):
  return [data for data in jsons
          if len([d for d in data['gift'] if d >= coin]) == num]


def print_text(jsons: list):
  print('|  N | gift |total |    Z |   A |   B |   C |')
  print('+----+------+------+------+-----+-----+-----+')
  for num in range(1, 21):
    for coin in [10, 100, 1000]:
      vals = filters(jsons, num, coin)
      cls = [len([d for d in vals if d['class'] == c]) for c in range(4)]
      print(f'| {num:2d} | {coin:4d} | {len(vals):4d} |'
            f' {" |".join([f"{c:4d}" for c in cls])} |'
            f' {" |".join([f" {c/len(vals):.3f}" for c in cls])} |')


def print_html(jsons: list):
  print('<table class="scatter-table">')
  print('  <thead><tr>')
  for k in ['N', 'gift', 'total',
            'Z数', 'A数', 'B数', 'CDE数',
            'Z率', 'A率', 'B率', 'CDE率']:
    print(f'    <th class="scatter-header">{k}</th>')
  print('  </tr></thead>')
  print('  <tbody>')

  for num in range(1, 21):
    for coin in [10, 100, 1000]:
      vals = filters(jsons, num, coin)
      cls = [len([d for d in vals if d['class'] == c]) for c in range(4)]
      print(f'    <tr class="coin{coin}">')
      for v in [num, coin, len(vals)] + cls + [f'{c/len(vals):.3f}' if len(vals) > 0 else '' for c in cls]:
        print(f'      <td class="scatter-cell">{v}</td>')
      print('    </tr>')
  print('  </tbody>')
  print('</table>')


def print_html_img(jsons: list):
  coins = [10, 100, 1000]
  colspan = 4
  print('<table class="scatter-table">')
  print('  <thead>')
  print('    <tr>')
  print('      <th class="scatter-header" rowspan=3>人数</th>')
  print(f'      <th class="scatter-header" colspan={colspan}>10コイン</th>')
  print(f'      <th class="scatter-header" colspan={colspan}>100コイン</th>')
  print(f'      <th class="scatter-header" colspan={colspan}>1000コイン</th>')
  print('    </tr>')
  print('    <tr>')
  for i in range(len(coins)):
    print('      <th class="scatter-header">Z数</th>')
    print('      <th class="scatter-header">A数</th>')
    print('      <th class="scatter-header">B数</th>')
    print('      <th class="scatter-header">C数</th>')
  print('    </tr>')
  print('    <tr>')
  for i in range(len(coins)):
    print('      <th class="scatter-header">Z率</th>')
    print('      <th class="scatter-header">A率</th>')
    print('      <th class="scatter-header">B率</th>')
    print('      <th class="scatter-header">C率</th>')
  print('    </tr>')
  print('  </thead>')
  print('  <tbody>')

  if True:
    num = "NN"
    print('    <tr>')
    print(f'      <td class="scatter-cell">{num}</td>')
    for coin in coins:
      print(f'      <td class="scatter-cell" colspan={colspan}>', end='')
      print('<img class="scatter-img"', end='')
      print(f' src="img/livescore/{coin}coin-{num}gifters.png"></td>')
    print('    </tr>')

  for num in range(1, 21):
    print('    <tr>')
    print(f'      <td class="scatter-cell" rowspan=3>{num}</td>')
    for coin in coins:
      print(f'      <td class="scatter-cell" colspan={colspan}>', end='')
      print('<img class="scatter-img"', end='')
      print(f' src="img/livescore/{coin}coin-{num}gifters.png"></td>')
    print('    </tr>')

    print('    <tr>')
    for coin in coins:
      vals = filters(jsons, num, coin)
      cls = [len([d for d in vals if d['class'] == c]) for c in range(4)]
      for v in cls:
        print(f'      <td class="scatter-cell">{v}</td>')
    print('    </tr>')

    print('    <tr>')
    for coin in coins:
      vals = filters(jsons, num, coin)
      cls = [len([d for d in vals if d['class'] == c]) for c in range(4)]
      for v in cls:
        val = v / len(vals)
        print(f'      <td class="scatter-cell">{val:.3f}</td>')
    print('    </tr>')
  print('  </tbody>')
  print('</table>')


def main() -> int:
  import argparse

  parser = argparse.ArgumentParser(description='')
  parser.add_argument('args', nargs='*')
  args = parser.parse_args()

  jsons = readJsons(args.args if args.args else ['.'])
  jsons = sum([v for k, v in jsons.items()
               if isinstance(v, list) and re.fullmatch(r'20\d{6}', k)], [])

  # print_text(jsons)
  # print_html(jsons)
  print_html_img(jsons)

  return 0


if __name__ == '__main__':
  sys.exit(main())


# vim:set et ts=2 sts=2 sw=2 tw=80:
