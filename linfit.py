#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
"""

import json
import numpy as np
from common import is_excluded
# import os


def vif(X):
  # X: 説明変数行列（切片列を含めないで渡すことを推奨）
  X = np.asarray(X)[:, 1:]
  n_vars = X.shape[1]
  vifs = []
  for j in range(n_vars):
    X_j = X[:, j]
    X_others = np.delete(X, j, axis=1)
    # 回帰 X_j ~ X_others
    beta, *_ = np.linalg.lstsq(np.column_stack((np.ones(len(X_j)), X_others)), X_j, rcond=None)
    yhat = np.column_stack((np.ones(len(X_j)), X_others)) @ beta
    ssr = np.sum((X_j - yhat)**2)
    sst = np.sum((X_j - X_j.mean())**2)
    r2 = 1 - ssr / sst if sst != 0 else 0.0
    vif_j = 1.0 / (1.0 - r2) if (1.0 - r2) != 0 else float('inf')
    vifs.append(vif_j)
  return np.array(vifs)


def linfit(X, Y, aic=False):
  if len(X) != len(Y):
    raise ValueError("len(X) != len(Y): {} != {}".format(len(X), len(Y)))
  if (len(X) == 0):
    print("X is empty")
    return
  a = np.linalg.lstsq(X, Y, rcond=-1)
  y_pred = []
  for i in range(len(Y)):
    y_pred.append(np.dot(a[0], X[i]))
  y_pred = np.array(y_pred)
  rss = np.sum((y_pred - Y)**2)
  tss = np.sum((Y - np.mean(Y))**2)
  assert tss > 0, (X.shape, Y.shape)
  r2 = 1 - rss / tss

  print("# coeff #=", len(a[0]), ", ", a)
  print("min/max estimation error", np.min(y_pred - Y), np.max(y_pred - Y))
  print("R^2 =", r2)   # 1 に近い（大きい）ほど良い
  if aic:
    aic = len(Y) * np.log(rss / len(Y)) + 2 * len(a[0])
    _vif = vif(X[:, :len(a[0])])
    print("aic =", aic)  # 小さいほど良い
    print("vif =", _vif)  # 小さいほど良い
  print()


def main():
  import argparse

  parser = argparse.ArgumentParser(description='')
  parser.add_argument('args', nargs='+')
  parser.add_argument('--xmin', default=0, type=int)
  parser.add_argument('--xmax', default=100000000, type=int)
  parser.add_argument('--exclude', action='store_true')
  # parser.add_argument('-f', required=True)
  # parser.add_argument('-f', required=True)
  args = parser.parse_args()

  xs = []
  ys = []
  n = [0] * 4
  for fn in args.args:
    if not fn.endswith('.json'):
      continue

    with open(fn, 'r') as f:
      data = json.load(f)

    gift = np.array(data['gift'])
    gift_sum = gift.sum()
    if not (args.xmin <= gift_sum <= args.xmax):
      continue

    livescore = int(data['livescore'])
    if args.exclude and is_excluded(gift_sum, livescore):
      continue

    ys.append(livescore)

    x = [1]
    x.append(gift_sum)
    n[0] = len(x)

    # 100 以上の人数
    n100 = (gift >= 100).sum()
    # x.append(1 if n100 == 1 else 0)
    # x.append(1 if n100 == 2 else 0)
    # x.append(1 if n100 == 3 else 0)
    # x.append(1 if n100 == 4 else 0)
    # x.append(1 if 5 <= n100 < 10 else 0)
    # x.append(1 if 10 <= n100 else 0)
    # n[1] = len(x)

    x.append(len(gift))
    n[1] = len(x)

    x.append(n100)
    n[2] = len(x)

    n5 = (gift >= 5).sum()
    x.append(n5)
    n[3] = len(x)

    xs.append(x)

  xs = np.array(xs, dtype=np.float64)
  ys = np.array(ys, dtype=np.float64)

  print("@@  #data=", len(ys))
  for i in range(len(n)):
    xx = xs[:, :n[i]]
    linfit(xx, ys, aic=True)

  print("  - aic: 小さいほど良い. 比較に使う")
  print("  - vif: 小さいほど良い. 5より大きいパラメータは多重共線性の疑いあり")
  print("        2=total_gift, 3= >=0coin, 4= >=100coin, 5= >=5coin")
  print()


if __name__ == '__main__':
  main()


# vim:set et ts=2 sts=2 sw=2 tw=80:
