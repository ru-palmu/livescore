#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
"""

from pathlib import Path
import json
import numpy as np
import re


def limitedJsons(jsons: dict, xmin, xmax, y2min, y2max) -> dict:
  ret = {}
  y2mind = y2min
  y2maxd = y2max
  n = 0
  for dirname, json_list in jsons.items():
    for data in json_list:
      if xmin is not None and data['total_gift'] < xmin:
        continue
      elif xmax is not None and data['total_gift'] > xmax:
        continue
      v = data['livescore'] / data['total_gift']
      if y2max is not None and v > y2max:
        y2maxd = max(y2maxd, v)
        continue
      if y2min is not None and v < y2min:
        y2mind = min(y2mind, v)
        continue
      if dirname not in ret:
        ret[dirname] = []
      ret[dirname].append(data)
      n += 1
  print(f"excluded by y2: {y2mind} .. {y2maxd}, #={n}")
  return ret


def readJsons(fnames: list) -> dict:
  return _readJsons(fnames, {})


def _readJsons(fnames: list, ret: dict) -> dict:
  for fname in fnames:
    # ディレクトリなら再帰する
    if Path(fname).is_dir():
      sub_fnames = [str(p) for p in Path(fname).iterdir()]
      _readJsons(sub_fnames, ret)
      continue
    if not Path(fname).is_file():
      continue
    if not re.fullmatch(r'[0-9]+-[0-9]+\.json', Path(fname).name):
      continue
    with open(fname, 'r', encoding='utf-8') as f:
      data = json.load(f)
    data['filename'] = fname
    data['livescore'] = int(data.get('livescore', 0))
    if 'date' not in data:
      # ファイル名から日付を取得する
      path = Path(fname)
      date_str = path.parent.name
      data['date'] = date_str

    gifts = np.array(data.get('gift', []))
    data['total_gift'] = gifts.sum()
    data['max_coin'] = gifts.max()
    data['1000coin'] = (gifts >= 1000).sum()
    data['100coin'] = (gifts >= 100).sum()
    data['10coin'] = (gifts >= 10).sum()
    data['0coin'] = len(gifts)
    data['rate'] = data['livescore'] / data['total_gift']
    data['class'] = classify(data)
    assert data['rate'] > 1.6, data
    assert 'followers' in data or data['date'] <= "20251022", data

    # if xlim and data['total_gift'] > xlim:
    #   continue

    # ディレクトリ名をキーにする
    path = Path(fname)
    key = path.parent.name
    if key not in ret:
      ret[key] = []
    ret[key].append(data)
  return ret


def is_excluded(total_gift, livescore):
  """跳ねていない"""
  return livescore / total_gift <= -0.6 * total_gift / 130_000 + 3


def set_ru_model(idx: int):
  global __RU_MODEL
  if idx == 1:
    print("default model (2025-09-28 ..)")
    __RU_MODEL = [(0, 3),
                  (17299.15066, 2.675280793)]
  else:
    # separator [50000, 180000] 2025-11-06
    __RU_MODEL = [
      (0, 3),  # 0..50K  1814 samples, 0
      (15531.441501008434, 2.6950897058012684),  # 50K..180K  671 samples, 50937.74069459752
      (41958.68833499996, 2.5483011271896387),  # 180K..100M  79 samples, 180036.12463550194
    ]
  # 交点を計算する
  for i in range(len(__RU_MODEL) - 1):
    b1, a1 = __RU_MODEL[i]
    b2, a2 = __RU_MODEL[i + 1]
    x = (b2 - b1) / (a1 - a2)
    y = a1 * x + b1
    print(f"ru_model seg {i}: P({x:9.2f}, {y:9.2f})  F(a={a2}, b={b2})")


def ru_model_x(xmin, xmax) -> list:
  # ru_model を描画するために必要な x を返す.
  # 直線のところは疎でいい.
  ret = []
  d = xmax - xmin

  # 0 割するから， 0が使えない
  if xmin <= 0:
    xmin = 0.01
  for xr in range(101):
    ret.append(xmin + xr / 100 * d)
  return ret


def ru_model(total_gift: int) -> float:
  return min([total_gift * k[1] + k[0] for k in __RU_MODEL])


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
    value_str = f"{value:.1f}"
  else:
    value_str = f"{value:.2f}"
  return f"{value_str}{suffix}"


def classify_geq(sep: list, d: dict) -> bool:
  x = d['total_gift']
  y = d['rate']
  for i in range(len(sep) - 1):
    x1, y1 = sep[i]
    x2, y2 = sep[i + 1]

    # 2点を結ぶ直線より上にあるか．
    if (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1) < 0:
      return False
  return True


def classify(d: dict) -> int:
  """どのグループに属するか.

  0: 跳ねている
  1: 跳ねていない A
  2: 跳ねていない B
  ...

  Z: (0, 3.1)..(40k, 2.8)..(140k, 2.6)
  A: (0, 2.8)..(20k, 2.6)..(120k, 2.3)
  B: (0, 2.4)..(20k, 2.3)..( 60k, 2.1)

  >>> classify({'total_gift': 20_000, 'rate': 3.1})
  0
  >>> classify({'total_gift': 40_000, 'rate': 3.0})
  0
  >>> classify({'total_gift': 80_000, 'rate': 2.9})
  0
  >>> classify({'total_gift': 20_000, 'rate': 2.8})
  1
  >>> classify({'total_gift': 100_000, 'rate': 2.5})
  1
  >>> classify({'total_gift': 80_000, 'rate': 2.3})
  2
  """
  if classify_geq([[0, 3.1], [40000, 2.8], [140000, 2.6]], d):
    return 0
  if classify_geq([[0, 2.8], [20000, 2.6], [120000, 2.3]], d):
    return 1
  if classify_geq([[0, 2.4], [20000, 2.3], [60000, 2.1]], d):
    return 2
  return 3


if __name__ == "__main__":
  import doctest
  doctest.testmod()

# vim:set et ts=2 sts=2 sw=2 tw=80:
