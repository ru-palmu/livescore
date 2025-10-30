#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
"""


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
