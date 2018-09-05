#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
@Author: $Author$
@Date: $Date$
@version: $Revision$

Description:
    Web启动
"""
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.insert(0, 'server_common')
sys.path.insert(0, './mahjong')
sys.path.insert(0, '.')
import bottle
import mahjong.main

if __name__ == '__main__':
    bottle.run(server='paste', host='0.0.0.0', port=9790, reloader=False, debug=True)
else:
    application = bottle.default_app()
