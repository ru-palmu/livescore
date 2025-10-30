#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
"""

from pathlib import Path
import json
import numpy as np


def readJsons(fnames: list) -> dict:
  ret = {}
  for fname in fnames:
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


__RU_MODEL = [(3, 0),
              (2.675280793, 17299.15066)]


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
  return min([total_gift * k[0] + k[1] for k in __RU_MODEL])


# vim:set et ts=2 sts=2 sw=2 tw=80:
