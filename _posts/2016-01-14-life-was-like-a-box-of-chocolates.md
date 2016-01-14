---

layout: post

title: 单例模式 V2.0.1.2016.1.14.11.10.8527-dev-alpha1(build 0008)

date: 2016-01-14 11:10

categories: Java

tags: [singleton, java, design pattern]

---

## 1. 随手写一个

``` java
public class Foo {
    private static final Foo instance = new Foo();
    private Foo() {}
    public static Foo getInstance() {
        return instance;
    }
}
```

问题显而易见，没有使用懒加载，在程序启动时被`static`关键字修饰的`instance`就被初始化了，存在影响程序性能的可能。

不过还是附上一条参考消息：

> 我怎么记得jvm现在对静态已经lazy了。没碰到那个类时静态部分根本没动。——@[石富贵](http://www.zhihu.com/people/rockace1)



## 2. 于是改成 Lazy-load

``` java
public class Foo {
    private static Foo instance;
    private Foo() {}
    public static Foo getInstance() {
        if (instance == null) {
            instance = new Foo();
        }
        return instance;
    }
}
```

第一次调用`getInstance()`的时候单例才会被初始化。

单线程是没问题了，多线程下还是不行。

存在着前一个线程还在初始化对象，后一个线程就通过了`if (instance == null)`的可能，结果就是对象被多次初始化，多次初始化还叫什么单例模式，改。



## 3. 同步方法

``` java
public class Foo {
    private static Foo instance;
    private Foo() {}
    public synchronized static Foo getInstance() {
        if (instance == null) {
            instance = new Foo();
        }
        return instance;
    }
}

```

倒是简单极了，把`getInstance()`声明成了同步方法，再多线程同时调用也得一个一个来。

……

慢着，一个一个来？

即使实例已经被初始化了也得等别人判断完了我才能拿？

太慢了，改。



## 4. 同步字节码

``` java
public class Foo {
    private static Foo instance;
    private Foo() {}
    public static Foo getInstance() {
        if (instance == null) {
            synchronized (Foo.class) {
                instance = new Foo();
            }
        }
        return instance;
    }
}
```

判断后同步住整个类，如果实例已经初始化了就不需要进同步块，直接拿了实例走人，没初始化才排队初始化。

……

慢着，排队初始化？

所有访问`getInstance()`方法时实例还没初始化的线程都在`synchronized (Foo.class)`前排队，轮流初始化实例。



明显不对啊，改。



## 5. 二次验证

``` java
public class Foo {
    private static Foo instance;
    private Foo() {}
    public static Foo getInstance() {
        if (instance == null) {
            synchronized (Foo.class) {
                if (instance == null) {
                    instance = new Foo();
                }
            }
        }
        return instance;
    }
}
```

嵌套已经有点瞎狗眼的迹象了……



总之这下似乎是没问题了，所有线程排队等待初始化，排到自己的时候多加一次空值判断，如果实例已经被前面的线程初始化了就拿了实例走人。

此策略名唤`Double-check`。



然而真的没问题了吗？

真的还有。



问题在于`new Foo()`这句话并非原子操作，多线程并发的情况下可能出现对象未初始化完成就被使用的问题。



## 5.1. 那怎么叫 Atomic 呢

原子是化学元素可分割的最小单元，原子操作是操作可分割的最小单元。



日文维基将原子操作称为[不可分操作](https://ja.wikipedia.org/wiki/%E4%B8%8D%E5%8F%AF%E5%88%86%E6%93%8D%E4%BD%9C)，不可分操作满足以下两个条件：

1. 在完成操作之前，其他进程无法观测它进行中的状态。
2. 部分操作失败会导致一系列操作的整体失败，系统状态回归原子操作前的状态。



对象初始化并非原子操作，根据 JVM 实现的不同，就有可能出现第5节最后提到的问题。

英文维基的`Double-checked locking`词条中描述了这种情况：

> Thread *B* notices that the shared variable has been initialized (or so it appears), and returns its value. Because thread *B* believes the value is already initialized, it does not acquire the lock. If *B* uses the object before all of the initialization done by *A* is seen by *B* (either because *A* has not finished initializing it or because some of the initialized values in the object have not yet percolated to the memory *B* uses ([cache coherence](https://en.wikipedia.org/wiki/Cache_coherence))), the program will likely crash.



> 线程 B 注意到共享变量已经被初始化（或者看起来是这么回事）并被返回。由于线程 B 相信变量的值已经初始化完成，就没有请求锁。如果 B 在 A 完成所有初始化之前使用了 B 看到的那个对象（无论是由于 A 没有完成初始化还是对象中有些初始化了的值还没有分配到 B 使用的那部分内存），程序就有可能崩溃。



不过解决起来倒是也简单。



## 6. volatile

``` java
public class Foo {
    private static volatile Foo instance;
    private Foo() {}
    public static Foo getInstance() {
        if (instance == null) {
            synchronized (Foo.class) {
                if (instance == null) {
                    instance = new Foo();
                }
            }
        }
        return instance;
    }
}
```

和之前的区别只有在`instance`前加上了`volatile`关键字。

volatile 翻译为不稳定的，可见其性质。

变量被 volatile 关键字修饰相当于告诉 JVM 这个变量可能被多个线程并发修改，因此每次读写此变量都直接到主内存处理，不要使用线程本地的缓存。

另一个特性是每次对此变量的访问都都会等到它自身离开同步块之后才会执行。

参考 http://www.javamex.com/tutorials/synchronization_volatile.shtml 。



第二个特性使得其中一个线程执行单例初始化时其他线程都要等到初始化完成后才能访问单例。



就为避免多次初始化你说费多大劲……



## 7. 那少费点劲成不成啊

吼啊吼啊。

``` java
public class Foo {
    private static class Singleton {
        private static final Foo INSTANCE = new Foo();
    }
    private Foo() {}
    public static Foo getInstance() {
        return Singleton.INSTANCE;
    }
}
```

1. 内部类在第一次访问时才会装载，类装载又是自带同步锁的，所以`INSTANCE`初始化是同步的。
2. `static`变量又是自带锁的，于是`INSTANCE`的访问也是同步的。
3. 声明为`final`进一步使得`INSTANCE`不可修改。

于是，一个内部类就完美搞定了，跟之前比起来好看多了是不是。



## 8. Q: 怎么不早说呢？

A: 早说我博客还写不写了。



## 9. 能再给力点吗，老师

以上单例防得住君子防不住小人，私有化的构造函数还可以用反射加`Constructor.setAccessible(true)`轻松破解。

尽管我至今都没有想通为什么有人非要反射攻击。

``` java
public enum Foo {
    INSTANCE;
    public void bar() {
        // foobar
    }
}
```

调用起来就更加轻松了：

``` java
Foo.INSTANCE.bar();
```

即可。



如果有人非要反射实例化呢？比如这样：

``` java
Constructor<Foo> constructor = Foo.class.getConstructor();
Foo foo = constructor.newInstance();
foo.bar();
```

写是能写出来，但是执行起来就会报错：

``` 
java.lang.NoSuchMethodException: Foo.<init>()
	at java.lang.Class.getConstructor0(Class.java:3082)
	at java.lang.Class.getConstructor(Class.java:1825)
	at Foo.main(Foo.java:13)
```



等一下，反编译的时候好像发现编译器创建了一个构造函数，能用这个不？

``` java
private Foo(string s, int i) {
	super(s, i);
}
```

试一下：

``` java
Constructor<Foo> constructor = Foo.class.getConstructor(String.class, Integer.class);
constructor.setAccessible(true);
Foo foo = constructor.newInstance("INSTANCE", 0);
foo.bar();
```

结果还是一样的：

``` 
java.lang.NoSuchMethodException: Foo.<init>(java.lang.String, java.lang.Integer)
	at java.lang.Class.getConstructor0(Class.java:3082)
	at java.lang.Class.getConstructor(Class.java:1825)
	at Foo.main(Foo.java:12)
```



看来足够靠谱了，而且只需要一行就可以实现单例，比上面任何一个都要简单。



## 10. 完

我本来就是查查synchronized关键字的，结果看起单例模式来了，世事难料啊。
