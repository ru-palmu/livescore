#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
"""

from common import readJsons
import re


def is_target(data: dict, conds: list) -> bool:
  for cond in conds:
    key, op, value = cond
    if key not in data:
      return False
    if op == '<':
      if not data[key] < value:
        return False
    elif op == '=':
      if not data[key] == value:
        return False
    elif op == '>':
      if not data[key] > value:
        return False
    else:
      raise ValueError(f'Invalid operator: {op}')
  return True


def print_data(data: dict, keys: list):
  out = []
  for k in keys:
    v = data.get(k, '')
    if isinstance(v, float):
      out.append(f'{v:.3f}')
    else:
      out.append(str(v))
  print(','.join(out))


def parse_cond(cond: str) -> list:
  # <, =, > のいずれかで分割する
  m = re.match(r'^(.*?)([<=>]+)(.*)$', cond)
  if not m:
    raise ValueError(f'Invalid condition: {cond}')
  key, op, value = m.groups()
  if re.fullmatch(r'\d+', value):
    return [key, op, int(value)]
  else:
    return [key, op, float(value)]


def main():
  import argparse

  parser = argparse.ArgumentParser(description='')
  parser.add_argument('args', nargs='+')
  parser.add_argument('--cond', action='append')
  parser.add_argument('--key', action='append')
  parser.add_argument('--order', default="livescore")
  args = parser.parse_args()

  if args.key is None:
    args.key = ['date', 'rank', 'date', 'user_rank',
                'total_gift', 'livescore', 'rate',
                'max_coin', '100coin', '10coin', '0coin']

  jsons = readJsons(args.args)

  conds = [parse_cond(c) for c in args.cond or []]

  print(','.join(args.key))


  ret = []
  for data_list in jsons.values():
    for data in data_list:
      if is_target(data, conds):
        ret.append(data)

  if args.order:
    if args.order[0] == '-':
      args.order = args.order[1:]
      reverse = False
    else:
      reverse = True
    ret.sort(key=lambda x: x.get(args.order, 0), reverse=reverse)

  for data in ret:
    print_data(data, args.key)


if __name__ == '__main__':
  main()


# vim:set et ts=2 sts=2 sw=2 tw=80:
