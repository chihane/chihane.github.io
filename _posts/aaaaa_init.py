#encoding:utf-8
import os, time

localtime = time.localtime()

filename = time.strftime('%Y-%m-%d-TITLE.md', localtime)
date = time.strftime('%Y-%m-%d %H:%M', localtime)

if not os.path.exists(filename):
    with open(filename, 'w') as f:
        f.writelines(['---\n\n',
                      'layout: post\n\n',
                      'title: TITLE\n\n',
                      'date: %s\n\n' % date,
                      'categories: CATEGORY\n\n',
                      'tags: [TAG]\n\n',
					  '---\n\n'])
        f.close()
