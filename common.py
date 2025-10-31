#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
"""

from pathlib import Path
import json
import numpy as np


def limitedJsons(jsons: dict, xmin, xmax, y2min, y2max) -> dict:
  ret = {}
  y2mind = y2min
  y2maxd = y2max
  for dirname, json_list in jsons.items():
    for data in json_list:
      if xmin is not None and data['total_gift'] < xmin:
        continue
      elif xmax is not None and data['total_gift'] > xmax:
        continue
      if dirname not in ret:
        ret[dirname] = []
      v = data['livescore'] / data['total_gift']
      if y2max is not None and v > y2max:
        y2maxd = max(y2maxd, v)
        continue
      if y2min is not None and v < y2min:
        y2mind = min(y2mind, v)
        continue
      ret[dirname].append(data)
  print(f"#excluded by y2: {y2mind} .. {y2maxd}")
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
    if not fname.endswith('.json'):
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
    # 70k, 200k で分ける
    __RU_MODEL = [(0, 3),
                  [1.76776625e+04, 2.67770487e+00],  # 70k..200k 236samples
                  [4.10767576e+04, 2.54909051e+00],  # 200k..     50samples
                  ]
  elif idx == 2:
    # 70k, 180k で分ける
    __RU_MODEL = [(0, 3),
                  [1.74743010e+04, 2.67966743e+00],  # 70k..180k 232samples
                  [4.08872106e+04, 2.54960537e+00],  # 180k..     54samples
                  ]
  else:
    __RU_MODEL = [(0, 3),
                  (17299.15066, 2.675280793)]


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


# vim:set et ts=2 sts=2 sw=2 tw=80:
