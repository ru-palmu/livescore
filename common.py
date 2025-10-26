#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
"""


def is_excluded(total_gift, livescore):
  """跳ねていない"""
  return livescore / total_gift <= -0.6 * total_gift / 130_000 + 3


def ru_model(total_gift: int) -> float:
  return min([total_gift * 3,
              total_gift * 2.675280793 + 17299.15066])


# vim:set et ts=2 sts=2 sw=2 tw=80:
