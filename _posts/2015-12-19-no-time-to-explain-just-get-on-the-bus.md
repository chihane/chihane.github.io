---

layout: post

title: 招手即停，响应式公交车

date: 2015-12-19 13:16

categories: Android

tags: [eventbus, android, java]

published: false

---

总之按照使用的顺序来。

##初始化

需要在Application里初始化吗？好像也没什么好初始化的。EventBus默认使用全局单例，也可以手动创建，咱这里暂时简化一下，只做单例。

单例模式谁都会写，直接上代码：

```java
private static EventBus defaultInstance;

public static EventBus getDefault() {
    if (defaultInstance == null) {
        synchronize (EventBus.class) {
            if (defaultInstance == null) {
                defaultInstance = new EventBus();
            }
        }
    }
    
    return defaultInstance;
}
```

暂时先忽略初始化用的builder什么的。

这里用了同步的二次验证来做单例的初始化以避免多线程下多次初始化的问题。另外由于只有第一次调用这个方法需要考虑同步问题，所以先用第一次判断来提高性能，如果已经被初始化了就直接返回单例。

然后处理一下构造方法：

```java
EventBus() {
    mainThreadPoster = new MainThreadPoster(Looper.getMainLooper());
    backgroundPoster = new BackgroundPoster();
}
```

里面先只创建两个发报器，顾名思义一个用来在主线程广播事件，一个用来在后台广播事件。这里进入后台的Poster来细讲讲。

Poster内部维护了一个静态队列，每当有事件被发送出来，就根据线程的不同进入不同的Poster的队列，由Poster逐个取出并广播。

EventBus原代码中还有事件优先级的概念，实现方式是在插入队列时用同步的for循环排序，原理很简单，就不写具体代码了。

```java
class BackgroundPoster implement Runnable() {
    private EventBus eventBus;
    private EventQueue eventQueue;
    
    BackgroundPoster(EventBus eventBus) {
        this.eventBus = eventBus;
    }
    
    @Override
    public void run() {
        while (True) {
            Object event = eventQueue.next();
            eventBus.getExecutorService().execute(this, event);
        }
    }
}
```
