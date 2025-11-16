#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
"""

from common import readJsons
import re
import operator


def is_target(data: dict, conds: list) -> bool:
  for cond in conds:
    key, op, value = cond
    if key not in data:
      return False
    if not op(data[key], value):
      return False
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
  """ <, =, > のいずれかで分割する

  >>> a = parse_cond('rank>1000')
  >>> a[0] == "rank"
  True
  >>> a[1](1500, 1000)
  True
  >>> a[1](500, 1000)
  False
  >>> a[2] == 1000
  True
  >>> a = parse_cond('  rank   < 1000  ')
  >>> a[0] == "rank"
  True
  >>> a[1](1500, 1000)
  False
  >>> a[1](500, 1000)
  True
  >>> a[2] == 1000
  True
  """
  m = re.fullmatch(r'\s*(\S+)\s*(=~|[<=>]|>=|<=)\s*(\S+)\s*', cond)
  if not m:
    raise ValueError(f'Invalid condition: {cond}')
  key, op, value = m.groups()
  print([key, op, value])
  compares = {'<': operator.lt,
              '>': operator.gt,
              '>=': operator.ge,
              '<=': operator.le,
              '=': operator.eq}
  if op == '=~':
    # 正規表現マッチ
    return [key, lambda a, b: re.search(b, a) is not None, value]

  if op not in compares:
    raise ValueError(f'Invalid operator: {op}')
  if re.fullmatch(r'\d+', value):
    value = int(value)
  else:
    value = float(value)

  if key in ["gift"]:
    key = 'total_gift'

  return [key, compares[op], value]


def main():
  import argparse

  parser = argparse.ArgumentParser(description='')
  parser.add_argument('args', nargs='+')
  parser.add_argument('--cond', action='append',
                      help='絞り込み条件を追加する. "key op cond" 形式.'
                      ' e.g., --cond rank>1000')
  parser.add_argument('--key', action='append',
                      help='SELECT 文の列を追加する.'
                      ' e.g, --key date --key rank')
  parser.add_argument('--order', default="livescore")
  parser.add_argument('--doctest', action='store_true',
                      help='Run doctest and exit.')
  args = parser.parse_args()

  if args.doctest:
    import doctest
    doctest.testmod()
    return

  if args.key is None:
    args.key = ['date', 'rank', 'user_rank',
                'total_gift', 'livescore', 'rate',
                'max_coin', '1000coin',
                '100coin', '10coin', '0coin']

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
