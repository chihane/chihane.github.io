---
layout: post

title: 闭门造公交车

date: 2016-06-19 02:05

categories: Android

tags: [eventbus, android, java]
---

事件总线的核心是事件的收发，收发中的收又可以进一步分为订阅和处理两部分，【订阅事件】【发送事件】【处理事件】这三个部分构成了事件总线框架的基础，其余内容都算是锦上添花。

那么我们先搭建起基本框架，之后再慢慢细化。

## 1. 起！

```java
public class SchoolBus {
    public static final SchoolBus defaultInstance = new SchoolBus();
    public void register(Object subscriber) {}
    public void post(Object event) {}
    private void postEvent(Subscription subscription, Object event) {}
}
```

```java
public class MainActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        // 订阅事件
        SchoolBus.defaultInstance.register(this);
    }

    public void onClick(View view) {
        // 发送事件
        SchoolBus.defaultInstance.post(new DefaultEvent("testtesttest"));
    }

    @Subscribe
    public void onEvent(DefaultEvent event) {
        // 处理事件
        Toast.makeText(this, event.message, Toast.LENGTH_SHORT).show();
    }
}
```

以上代码不消多说，简单地定义了三大核心的声明和调用，以后的代码编写便在前者基础上徐徐展开。

### 2. Subscription（订阅） 是个什么东西？

一句话回答： **Subscription 是【订阅】的单元** 。

另外， *Event（事件）* 是【处理】的单元。

【发送】则连接了【订阅】和【处理】。

事件总线的整个使用流程可以概括为：

>  通过【订阅】找到所有 *Subscription* ，保存起来，再通过【发送】将 *Event* 派送给 *Subscription* 进行【处理】。

了解了这个基本概念之后，我们就可以开始着手写代码了。

## 3. 注册订阅器

根据前面总结的使用流程，首先我们可以提出两个问题：

1. 怎么找 Subscription？
2. 找到了之后怎么保存？
3. 不是说好叫【订阅】的，方法名怎么变成 `register` 了？
4. `@Subscribe` 是哪里冒出来的？
5. 为什么双层吉士堡越来越小？
6. 说好提两个问题，怎么提了六个？

第二个问题我们暂且搁置，首先解决第一个。

### a. MethodFinder

编写原型最重要的就是短平快，要在一个类里找东西，最符合直觉的方式是什么？

当然是运行时注解+反射的方式。

把『影响运行效率』什么的教条抛到脑后，马上来写一个标记：

```java
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface Subscribe {}
```

一分钟都不用。

于是第四个问题就得到了答案。

<img src="img/2016-06-19-no-time-to-explain-just-get-on-the-bus/1.jpg" />

*『你不是说先解决第一个问题吗？』*

这个注解用来标记要接收事件的方法，接下来只要遍历订阅器的方法声明，找出所有被标记的方法就可以了。

```java
public static List<Method> find(Object subscriber) {
    List<Method> result = new ArrayList<>();

    Class clazz = subscriber.getClass();
    Method[] methods = clazz.getDeclaredMethods();
    // 遍历类中的所有方法
    for (Method method : methods) {
        Annotation[] annotations = method.getDeclaredAnnotations();
        for (Annotation annotation : annotations) {
            // 找出包含 @Subscribe 注解的方法
            if (annotation.annotationType() == Subscribe.class) {
                result.add(method);
            }
        }
    }

    if (result.size() == 0) {
        throw new SchoolBusException("No @Subscriber method found in registered subscriber");
    }

    return result;
}
```

这样我们只要在需要的时候用反射调用方法就可以了——

**且慢！**

我们是找到了所有方法没错，可是如果有很多个 `@Subscribe` 方法，我怎么知道要调用哪一个呢？

想想八戒临终前所说的话吧。

订阅器订阅的是事件，那么订阅方法自然应该按照事件类型来区分，事件类型则声明在方法参数中。

于是我们在这里引入前面提到的概念。

### b. SubscriptionFinder

我们把整个订阅方法连带订阅器自身抽象为一个 *订阅* 实例，将它们封装进 `Subscription` 类：

```java
public class Subscription {
    Object subscriber;
    Method method;
    Class eventType;
}
```

同时把 a 小节中的 `MethodFinder` 升级为二代目 `SubscriptionFinder` ，代码也稍作修改：

```java
public static List<Subscription> find(Object subscriber) {
    List<Subscription> result = new ArrayList<>();

    Class clazz = subscriber.getClass();
    Method[] methods = clazz.getDeclaredMethods();
    // 遍历类中的所有方法
    for (Method method : methods) {
        Annotation[] annotations = method.getDeclaredAnnotations();
        for (Annotation annotation : annotations) {
            // 找出被 @Subscribe 注解标记的方法
            if (annotation.annotationType() == Subscribe.class) {
                Class[] parameterTypes = method.getParameterTypes();
                if (parameterTypes.length == 0) {
                    throw new SchoolBusException("Event type must declared as @Subscriber methods' parameter");
                }
                // 和它的参数类型
                Class eventType = parameterTypes[0];
                // 连同 subscriber 一起封装起来
                result.add(new Subscription(subscriber, method, eventType));
            }
        }
    }

    if (result.size() == 0) {
        throw new SchoolBusException("No @Subscriber method found in registered subscriber");
    }

    return result;
}
```

相比前面的方法增加了 `subscriber` 和 `eventType` 的封装，把 `register(subscriber)` 方法的参数和被 `@Subscribe` 标记的事件处理方法中的参数类型都封装进 `Subscription` 实例中，返回值也变成了 `Subscription` 列表。

现在得到了订阅对象，再结合 a 小节中得到的结论，我们可以知道将来肯定会需要用事件类型来找对应的订阅对象，那不妨就先把它们保存起来。

于是添加一个事件类型到订阅对象的一对多映射，

```java
private static final Map<Class, List<Subscription>> typeToSubscriptions = new HashMap<>();
```

把 `SubscriptionFinder` 找到的订阅保存进去：

```java
public void register(Object subscriber) {
    List<Subscription> subscriptions = SubscriptionFinder.find(subscriber);

    for (Subscription subscription : subscriptions) {
        List<Subscription> subscriptionsByType = typeToSubscriptions.get(subscription.eventType);

        if (subscriptionsByType == null) {
            subscriptionsByType = new ArrayList<>();
            typeToSubscriptions.put(subscription.eventType, subscriptionsByType);
        }

        subscriptionsByType.add(subscription);
    }
}
```

这样 `register` 方法就初步完成了。

从另一个角度来说，找寻订阅器中的订阅对象并加以保存，以便事件到来的时候检索使用，这个过程就可以理解为订阅器向事件总线的注册。

这也就是第三个问题的答案。

<img src="img/2016-06-19-no-time-to-explain-just-get-on-the-bus/2.jpg" />

*『什么时候跳到第三个问题的？』*

## 4. 发送事件

有了前面的铺垫，剩下的都是顺水推舟。

发送的过程根据前面的讨论，就是使用事件的类型找到相应的订阅，并把事件实例推送过去。

```java
public void post(Object event) {
    Class eventType = event.getClass();
    List<Subscription> subscriptions = typeToSubscriptions.get(eventType);

    for (Subscription subscription : subscriptions) {
        postEvent(subscription, event);
    }
}
```

简单地调用订阅方法：

```java
private void postEvent(Subscription subscription, Object event) {
    try {
        subscription.method.invoke(subscription.subscriber, event);
    } catch (IllegalAccessException e) {
        e.printStackTrace();
    } catch (InvocationTargetException e) {
        e.printStackTrace();
    }
}
```

一个最简单的事件总线就完成了。

## 5. 跑一个

回到 Activity 中，按照约定的规则，首先注册订阅器：

```java
SchoolBus.defaultInstance.register(this);
```

写一个按钮，作用是发送一个自己写的事件，里面携带着一个滚键盘写出来的消息：

```
SchoolBus.defaultInstance.post(new DefaultEvent("testtesttest"));
```

最后写上订阅方法，把消息作为内容弹一个提示：

```
@Subscribe
public void onEvent(DefaultEvent event) {
    Toast.makeText(MainActivity.this, event.message, Toast.LENGTH_SHORT).show();
}
```

<img src="img/2016-06-19-no-time-to-explain-just-get-on-the-bus/3.png" />

*——丁仪 [?-2212]*

## 效果

<img src="img/2016-06-19-no-time-to-explain-just-get-on-the-bus/4.png" />

看，它依然在正常地运作！

> 本文中所有代码参见 <https://github.com/chihane/SchoolBus>