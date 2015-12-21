---

layout: post

title: 汤一个

date: 2015-12-16 10:49

categories: CATEGORY

tags: [tumblr]

---

Tumblr官方都给了客户端我还傻×呵呵地写爬虫……

官方文档在这:

	https://www.tumblr.com/docs/en/api/v2

也可以从首页页脚里的Developer项进入。

### 创建应用

多数开发者平台这个都是第一步。

	https://www.tumblr.com/oauth/apps

首先在这里创建应用。

- 应用名
- 应用网址
- 应用描述
- 默认回调URL

是必填项，默认回调URL我也不知道是啥，就随便给了博客地址……

创建应用还需要做人机验证，需要翻墙。

### 口令

应用创建完成后会回到先前的页面，可以看到`OAuth Consumer Key`，点击`Show secret key`还可以得到`Secret Key`，这两个在初始化客户端的时候会用到。