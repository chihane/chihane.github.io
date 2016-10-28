---
layout: post

title: LruCache 是怎样实现 LRU 算法的？

date: 2016-10-28 15:23

categories: Source code analyzing

tags: [lrucache, android]

---

LruCache 内部使用 `LinkedHashmap` 存储数据以实现 LRU 算法。

LinkedHashmap 可以使用两种模式初始化，当 `accessOrder` 为 `false` 时，其中的元素按插入顺序排序，为 `true` 时则按访问顺序排序。元素顺序保存在 LinkedHashmap 内部另外维护的一个双向链表中。

在访问顺序排序模式下，每次 `get()` 元素时，LinkedHashmap 都会把当前元素移动到链表的尾部，如此一来，排在链表前端的自然就是最近一次被访问时间最远（Least Recently Used）的元素了。

当 LruCache 执行 trim 时，逐个取出 LinkedHashmap 中最 `eldest()` 的元素并移除，直到指定 `size` 就可以了。

### trim策略？

1. 每次 `put(K, V)` 时
2. 当 `create` 方法（用于预先创建缓存值）被重写，其返回的对象被首次放置到 LinkedHashmap  中时
3. `resize(maxSize)` 被调用，重新分配缓存大小时
4. `evictAll()` 被调用，释放所有缓存时

### 双向链表？

`LinkedHashmap` 中额外维护了一个 `LinkedEntry` ，继承自 `Hashmap` 中的 `HashmapEntry` ，并额外添加了 `nxt` 和 `prv` 两个指针属性以实现正反双向查找。头尾两端元素的 `prv` 和 `nxt` 互相指向对方，使得整个双向链表头尾相接。

### 一句话总结

Q: LruCache 怎样实现了 LRU 算法？

A: 它用于存储数据的 LinkedHashmap 使用了 LRU 方式来排列元素

### 怎么看着像废话（