---

layout: post

title: 招手即停，响应式公交车

date: 2015-12-19 18:12

categories: Android

tags: [eventbus, android, java]

published: false

---

以下代码直接拿去执行肯定是不能保证编译通过的，因为大部分代码是脱离IDE用文本编辑器直接敲的，而且细节部分比如多线程同步和空指针处理并没有写到很细致。

话说要用的话直接去用官方库啦。

闲话少叙，总之按照使用的顺序来。

## # 初始化

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

Poster结构很简单，就是使用线程池依次执行队列，主线程使用的Poster原理也类似，不过继承的是Handler，然后向自身发送消息并处理。

然后进入EventQueue里看一看。

```java

    private static List<Object> queue;
    
    synchronized void enqueue(Object event) {
        if (!queue.contains(event)) {
            queue.add(event);
        }
    }
    
    synchronized Object dequeue() {
        Object event = queue.remove(queue.size()-1);
        return event;
    }

```

一个入列方法一个出列方法。

EventBus原代码中还有事件优先级的概念，实现方式是在插入队列时用同步的for循环逐个判断优先级大小做排序，原理很简单，就不写具体代码了。

是不是觉得发报器的设计有种微妙的既视感？

这不就是Android自带的Handler+MessageQueue+Message+Looper的事件分发机制嘛。

没错，EventBus的一大使用场景就是替代自带的Handler，使用EventBus可以做到更彻底的解耦，代码量也可以大大降低，同样是处理事件：

```java

    private Handler handler = new Handler(new Handler.Callback() {
        @Override
        public void handlerMessage(Message msg) {
            switch(msg.what) {
                // ...
            }
        }
    });

```

换成EventBus则变成了：

```java

    EventBus.getDefault().register(this);
    
    public void onEvent(SomeEvent event) {
        // ...
    }

```

而且还可以为不同事件重载不同方法，结构更加清晰了。

至于发送事件部分：

```java

    Message message = Message.obtain(WHAT);
    someClass.getHandler().sendEmptyMessage(message);

```

用EventBus则写作：

```java

    SomeEvent event = new SomeEvent();
    eventBus.post(event);

```

看起来代码复杂度差不多，但是实际上由于事件类可以自描述，所以不需要声明一大堆常量来做事件类型的区分了。

为每个事件创建类也便于管理，想必很多人都在实际项目里见过乱七八糟的常量管理，有的事件常量写在Activity里，有的写在全局常量类里，甚至有的直接写成魔法数字。

另一方面，事件分发由EventBus统一管理，就不需要想办法去拿不知道是在Application类还是BaseActivity类里的Handler实例了。

好处多多。

那么代码继续。

##注册

首先注册要接收广播的对象，比如在Activity里调用：

```java

    EventBus.getDefault().register(this);

```

表示this就是一个订阅者。

就从注册方法写起。

简要概括一个EventBus的工作原理？就是：

    通过反射保存所有订阅者及其回调方法的实例，并在广播时根据事件对象的类型找出所有对应的回调方法，使用反射直接调用。
    
那么显而易见，这个注册方法里要做的就是拆解参数的类结构了，先写个伪代码：

```java

    不让用的修饰符 = "private|abstract|bridge|synthesizer"
    常量 指定前缀 = "onEvent"

    方法 注册(Object 订阅者) {
        所有方法 = 订阅者.类.所有方法();
        遍历 所有方法 {
            如果 方法.包含(不让用的修饰符) { 跳过; }
            如果 方法.不开始于(指定前缀) { 跳过; }
            
            方法名体 = 方法名.去掉前缀();
            // 根据方法名体指定的线程类型分类
            
            方法参数[] = 方法.所有参数();
            // 根据方法参数指定的事件类型分类
        }
        
        如果 找到了方法 {
            缓存<订阅者类， 方法列表>.缓存起来;
            缓存<事件类型， 订阅者>.缓存起来;
        }
    }

```

够清楚了，我有点不想写实现了……
