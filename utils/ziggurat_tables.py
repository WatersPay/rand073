#!/usr/bin/env python
#
# Copyright 2018 Developers of the Rand project.
# Copyright 2013 The Rust Project Developers.
#
# Licensed under the Apache License, Version 2.0 <LICENSE-APACHE or
# https://www.apache.org/licenses/LICENSE-2.0> or the MIT license
# <LICENSE-MIT or https://opensource.org/licenses/MIT>, at your
# option. This file may not be copied, modified, or distributed
# except according to those terms.

# This creates the tables used for distributions implemented using the
# ziggurat algorithm in `rand073::distributions;`. They are
# (basically) the tables as used in the ZIGNOR variant (Doornik 2005).
# They are changed rarely, so the generated file should be checked in
# to git.
#
# It creates 3 tables: X as in the paper, F which is f(x_i), and
# F_DIFF which is f(x_i) - f(x_{i-1}). The latter two are just cached
# values which is not done in that paper (but is done in other
# variants). Note that the adZigR table is unnecessary because of
# algebra.
#
# It is designed to be compatible with Python 2 and 3.

from math import exp, sqrt, log, floor
import random

# The order should match the return value of `tables`
TABLE_NAMES = ['X', 'F']

# The actual length of the table is 1 more, to stop
# index-out-of-bounds errors. This should match the bitwise operation
# to find `i` in `zigurrat` in `libstd/rand/mod.rs`. Also the *_R and
# *_V constants below depend on this value.
TABLE_LEN = 256

# equivalent to `zigNorInit` in Doornik2005, but generalised to any
# distribution. r = dR, v = dV, f = probability density function,
# f_inv = inverse of f
def tables(r, v, f, f_inv):
    # compute the x_i
    xvec = [0]*(TABLE_LEN+1)

    xvec[0] = v / f(r)
    xvec[1] = r

    for i in range(2, TABLE_LEN):
        last = xvec[i-1]
        xvec[i] = f_inv(v / last + f(last))

    # cache the f's
    fvec = [0]*(TABLE_LEN+1)
    for i in range(TABLE_LEN+1):
        fvec[i] = f(xvec[i])

    return xvec, fvec

# Distributions
# N(0, 1)
def norm_f(x):
    return exp(-x*x/2.0)
def norm_f_inv(y):
    return sqrt(-2.0*log(y))

NORM_R = 3.6541528853610088
NORM_V = 0.00492867323399

NORM = tables(NORM_R, NORM_V,
              norm_f, norm_f_inv)

# Exp(1)
def exp_f(x):
    return exp(-x)
def exp_f_inv(y):
    return -log(y)

EXP_R = 7.69711747013104972
EXP_V = 0.0039496598225815571993

EXP = tables(EXP_R, EXP_V,
             exp_f, exp_f_inv)


# Output the tables/constants/types

def render_static(name, type, value):
    # no space or
    return 'pub static %s: %s =%s;\n' % (name, type, value)

# static `name`: [`type`, .. `len(values)`] =
#     [values[0], ..., values[3],
#      values[4], ..., values[7],
#      ... ];
def render_table(name, values):
    rows = []
    # 4 values on each row
    for i in range(0, len(values), 4):
        row = values[i:i+4]
        rows.append(', '.join('%.18f' % f for f in row))

    rendered = '\n    [%s]' % ',\n     '.join(rows)
    return render_static(name, '[f64, .. %d]' % len(values), rendered)


with open('ziggurat_tables.rs', 'w') as f:
    f.write('''// Copyright 2018 Developers of the Rand project.
// Copyright 2013 The Rust Project Developers.
//
// Licensed under the Apache License, Version 2.0 <LICENSE-APACHE or
// https://www.apache.org/licenses/LICENSE-2.0> or the MIT license
// <LICENSE-MIT or https://opensource.org/licenses/MIT>, at your
// option. This file may not be copied, modified, or distributed
// except according to those terms.

// Tables for distributions which are sampled using the ziggurat
// algorithm. Autogenerated by `ziggurat_tables.py`.

pub type ZigTable = &\'static [f64, .. %d];
'''  % (TABLE_LEN + 1))
    for name, tables, r in [('NORM', NORM, NORM_R),
                            ('EXP', EXP, EXP_R)]:
        f.write(render_static('ZIG_%s_R' % name, 'f64', ' %.18f' % r))
        for (tabname, table) in zip(TABLE_NAMES, tables):
            f.write(render_table('ZIG_%s_%s' % (name, tabname), table))
