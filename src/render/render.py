# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: © 2024 Brett Smith <xbcsmith@gmail.com>
# SPDX-License-Identifier: Apache-2.0


import json
import yaml
import logging
import os

import sys
import commonmark



logger = logging.getLogger(__name__)


def debug_except_hook(type, value, tb):
    print(f"epr python hates {type.__name__}")
    print(str(type))
    import pdb
    import traceback

    traceback.print_exception(type, value, tb)
    pdb.post_mortem(tb)


debug = os.environ.get("EPR_DEBUG")
if debug:
    sys.excepthook = debug_except_hook
    logger.setLevel(logging.DEBUG)


parser = commonmark.Parser()

with open(sys.argv[1]) as f:
    ast = parser.parse(f.read())

model = json.loads(commonmark.dumpJSON(ast))

out = yaml.dump(model, sort_keys=False, default_flow_style=False)
with open(sys.argv[2], "w") as f:
    f.write(out)

for subnode, entered in ast.walker():
    if subnode.t == "heading":
        import pdb;pdb.set_trace()


import pdb;pdb.set_trace()
