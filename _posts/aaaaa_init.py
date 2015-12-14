#encoding:utf-8
import os, time

localtime = time.localtime()

filename = time.strftime('%Y-%m-%d-TITLE.md', localtime)
date = time.strftime('%Y-%m-%d %H:%M', localtime)

if not os.path.exists(filename):
    with open(filename, 'w') as f:
        f.writelines(['---\n',
                      'layout: post\n',
                      'title: TITLE\n',
                      'date: %s\n' % date,
                      'categories: CATEGORY\n',
                      'tags: [TAG]\n', '---\n\n'])
        f.close()
