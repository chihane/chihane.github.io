---

layout: post

title: [译] Dagger 2 官方指南

date: 2016-01-29 11:34

categories: Translation

tags: [dagger2, translation, tutorial, google]

---

应用中最好的类是那些用来做实事的类：`BarcodeDecoder`，`KoopaPhysicsEngine`，`AudioStreamer`什么的。这些类拥有着依赖：比如`BarcodeCameraFinder`，`DefaultPhysicsEngine`，以及`HttpStreamer`。

反过来说，最糟的类就要数占了地方又没做多少事的那些了：比如`BarcodeDecoderFactory`工厂，`CameraServiceLoader`加载器，`MutableContextWrapper`包装器之类。这些类就像胶带一样把真正有用的东西缠成臃肿的一团。

Dagger 作为那些`工厂的工厂`的替代，实现了依赖注入的设计模式，又避免了总要写模板代码的困扰。它让你可以专注于『有用』的那些类。只需要声明依赖，再指明如何满足(satisfy)依赖，就可以让你的应用跑起来了。

用标准的`javax.inject`注解（[JSR 330](https://jcp.org/en/jsr/detail?id=330)）来构建代码使得每一个类都**很容易测试**。你用不着就为了把`RpcCreditCardService`服务换成`FakeCreditCardService`服务而写上一堆模板代码。

而且依赖注入不止能用于测试。**重用和替换模块**也会变得很轻松。你可以在整个应用中共享`AuthenticationModule`模块，还可以在开发环境中使用`DevLoggingModule`而在发布后使用`ProdLoggingModule`，在不同的情况下得到不同的表现。

## Dagger 2 为何如此不同

[依赖注入](https://en.wikipedia.org/wiki/Dependency_injection)框架已经存在了很多年，拥有着许多种 API 来完成配置和注入。那么，我们为什么要重新发明轮子呢？Dagger 2 率先使用了**编译时生成代码实现完整调用堆栈**的技术。指导原则就是使生成的代码尽可能模仿用户手动编写的代码，让依赖注入简单，可追踪，而且尽可能地高性能。想要了解更多设计背后的故事，请看来自[+Gregory Kick](https://google.com/+GregoryKick/)的[这段演讲](https://www.youtube.com/watch?v=oK_XtfXPkqw)（[幻灯片见此](https://docs.google.com/presentation/d/1fby5VeGU9CN8zjw4lAb2QPPsKRxx6mSwCe9q7ECNSJQ/pub?start=false&loop=false&delayms=3000)）。

## 使用 Dagger

我们通过编写一个咖啡机（coffee maker）来介绍依赖注入和 Dagger。如果需要可编译运行的完整代码，请看 Dagger 的 [coffee example](https://github.com/google/dagger/tree/master/examples/simple/src/main/java/coffee)。

### 声明依赖

Dagger 可以为你应用程序中的类构建实例并且满足依赖。使用`javax.inject.Inject`注解来指明哪个构造方法和属性是需要交给它来处理的。

在需要 Dagger 来创建实例的类的构造器上添加`@Inject`注解。当请求新实例时，Dagger 会获取请求的参数并调用构造器。

``` java
class Thermosiphon implements Pump {
  private final Heater heater;

  @Inject
  Thermosiphon(Heater heater) {
    this.heater = heater;
  }

  ...
}
```

Dagger 可以直接注入类属性。在这个例子里，它会为`heater`属性获取一个`Heater`实例，为`pump`属性获取一个`Pump`实例。

``` java
class CoffeeMaker {
  @Inject Heater heater;
  @Inject Pump pump;

  ...
}
```

如果你的类拥有被`@Inject`注解的属性但没有被`@Inject`注解的构造器，Dagger 会在得到请求的时候注入那些属性，但不会创建类的新实例。如果也需要 Dagger 创建实例的话，就添加一个无参构造器并用`@Inject`注解起来。

Dagger 也支持方法注入，虽然一般来说还是首选构造器和属性注入。

没有`@Inject`注解的类无法被 Dagger 构建。

### 满足依赖

默认情况下，Dagger 会通过构建上述类型的实例来满足每个依赖。当你请求一个`CoffeeMaker`时，它会调用`new CoffeeMaker()`并设置好里面可以注入的属性来拿到一个实例。

但是`@Inject`也不是在哪里都能用：

- 接口(interface)不能被实例化。
- 第三方的类不能添加注解。
- 可以配置的对象必须被配置！

在这些`@Inject`不能用或者用起来很尴尬的情况下，就要用`@Provides`注解的方法来满足依赖了。方法返回值的类型定义了它满足哪个依赖。

比如说，当请求`Heater`时`provideHeater()`就会被调用：

``` java
@Provides Heater provideHeater() {
  return new ElectricHeater();
}
```

`@Provides`方法是可以依赖自身的。比如，当请求`Pump`的时候这个方法就会返回一个`Thermosiphon`：

``` java
@Provides Pump providePump(Thermosiphon pump) {
  return pump;
}
```

所有的`@Provides`方法都必须归属于一个模块（module），也就是被`@Module`注解的类。

``` java
@Module
class DripCoffeeModule {
  @Provides Heater provideHeater() {
    return new ElectricHeater();
  }

  @Provides Pump providePump(Thermosiphon pump) {
    return pump;
  }
}
```

按照惯例，`@Provides`方法使用`provide`作为前缀，模块类则使用`Module`作为后缀。

### 构建图谱（Graph）

所有拥有`@Inject`和`@Provides`注解的类组成了一张对象的图谱，并通过它们之间的依赖彼此链接。调用了诸如应用程序的`main`方法或是 Android 的`Application`类等代码时，也就通过一系列职责明确的根节点来访问了这张图谱。在 Dagger 2 中，这一系列根节点由一个接口来定义，这个接口中包含着无参并能够返回需要的类型的方法。通过在这个接口上使用`@Component`注解，并且把[模块](http://google.github.io/dagger/api/latest/dagger/Module.html)类型作为`modules`参数的值，Dagger 2 就能够自动生成协议的所有实现。

``` java
@Component(modules = DripCoffeeModule.class)
interface CoffeeShop {
  CoffeeMaker maker();
}
```

生成的实现类名称和接口名一样，并用`Dagger`作为前缀。使用`builder()`方法返回的[Builder](http://en.wikipedia.org/wiki/Builder_pattern)来设置依赖，最后`build()`一个实例。

``` java
CoffeeShop coffeeShop = DaggerCoffeeShop.builder()
    .dripCoffeeModule(new DripCoffeeModule())
    .build();
```

一个模块中如果有可访问的默认构造器，则可以直接省略不写，因为如果没有设置模块，建造器就会自动创建一个实例。如果所有依赖都可以这样构建，那生成的实现类里还会有一个`create()`方法，使用这个方法就可以不需要理会建造器，直接拿到一个实例。

``` java
CoffeeShop coffeeShop = DaggerCoffeeShop.create();
```

现在，我们的`CoffeeApp`就可以很简单地使用 Dagger 生成的`CoffeeShop`实现来得到完全注入的`CoffeeMaker`了。

``` java
public class CoffeeApp {
  public static void main(String[] args) {
    CoffeeShop coffeeShop = DaggerCoffeeShop.create();
    coffeeShop.maker().brew();
  }
}
```

现在图谱就构建完成了，入口也注入好了，我们来运行我们的咖啡机应用吧。真是愉♂悦啊。

```
$ java -cp ... coffee.CoffeeApp
~ ~ ~ heating ~ ~ ~
=> => pumping => =>
 [_]P coffee! [_]P
```

### 单例与作用域绑定

为`@Provides`方法或可注入的类添加上[`@Singleton`](http://docs.oracle.com/javaee/7/api/javax/inject/Singleton.html)注解的话，图谱就会为它所有的使用者（clients）提供单例。

``` java
@Provides @Singleton Heater provideHeater() {
  return new ElectricHeater();
}
```

可注入类上的`@Singleton`注解也可以作为[文档](http://docs.oracle.com/javase/7/docs/api/java/lang/annotation/Documented.html)。它可以提醒潜在的维护者，这个类可能会被多个线程共享。

``` java
@Singleton
class CoffeeMaker {
  ...
}
```

介于 Dagger 2 将图谱中拥有作用域的实例和元件（component）的实现联系在了一起，元件本身就需要声明他们自己打算展现在哪个作用域里。比如，在同一个元件上同时添加`@Singleton`和`@RequestScoped`两种绑定是没有任何意义的，因为这些作用域的生命周期不同，导致它们在元件中也必须度过不同的生命周期。如果要给元件声明一个指定的作用域，只要在元件接口上简单地加上作用域注解就行了。

``` java
@Component(modules = DripCoffeeModule.class)
@Singleton
interface CoffeeShop {
  CoffeeMaker maker();
}
```

### 懒注入

有的时候你需要一个对象实现懒惰实例化。对于任意一个绑定`T`，可以创建一个[`Lazy<T>`](http://google.github.io/dagger/api/latest/dagger/Lazy.html)来把实例化推迟到第一次调用`Lazy<T>`的`get()`方法时。如果`T`是单例，那对于`对象图谱`中所有的注入，`Lazy<T>`都是同一个实例。不然的话，每一个注入点都会拿到不同的`Lazy<T>`实例。但不管怎么说，之后对于任何一个`Lazy<T>`的调用，得到的都是同一个`T`实例。

``` java
class GridingCoffeeMaker {
  @Inject Lazy<Grinder> lazyGrinder;

  public void brew() {
    while (needsGrinding()) {
      // Grinder created once on first call to .get() and cached.
      lazyGrinder.get().grind();
    }
  }
}
```

### 供应器（provider）注入

有的时候你不希望只注入一个值，而希望返回多个实例。要做到这点你有很多种选择，比如工厂，建造器什么的，还有一种选择是注入一个[`Provider<T>`](http://docs.oracle.com/javaee/7/api/javax/inject/Provider.html)，而不是像之前一样只注入一个`T`。每当`.get()`方法被调用时`Provider<T>`都会再次调用*绑定逻辑*。如果这个所谓绑定逻辑是添加了`@Inject`注解的构造器，就会创建一个新的实例，但如果是`@Provides`方法的话就没有这种保证了。

``` java
class BigCoffeeMaker {
  @Inject Provider<Filter> filterProvider;

  public void brew(int numberOfPots) {
  ...
    for (int p = 0; p < numberOfPots; p++) {
      maker.addFilter(filterProvider.get()); //new filter every time.
      maker.addCoffee(...);
      maker.percolate();
      ...
    }
  }
}
```

***注意：***注入`Provider<T>`可能导致代码混乱或者作用域异常和对象图谱结构错误。通常来说你最好还是用[工厂类](http://en.wikipedia.org/wiki/Factory_(object-oriented_programming))或是`Lazy<T>`或者重新组织一下代码的生命周期和结构，做到只注入一个`T`就能解决问题。尽管注入`Provider<T>`在某些情况下可以救命。比如在你必须要用一个没法组织好对象的自然声明周期的陈旧架构的时候（比如：servlets 在设计上是单例的，但是只有在特定请求的数据作为上下文时才有效），这算一个一般用法。

### 标识符(qualifiers)

有的时候只靠类型不足以指明特定的依赖。比如一个复杂的咖啡机应用可能需要不同的加热器来分别给热水器和灶台使用。

在这种情况下，我们就引入了**标识符注解**，也就是被[`@Qualifier`](http://docs.oracle.com/javaee/7/api/javax/inject/Qualifier.html)注解的注解。下面是[`@Named`](http://docs.oracle.com/javaee/7/api/javax/inject/Named.html)注解的声明，它是一个`javax.inject`包里的标识符注解。

``` java
@Qualifier
@Documented
@Retention(RUNTIME)
public @interface Named {
  String value() default "";
}
```

你可以创建自己的标识符注解，或者就直接用`@Named`。在需要的属性或参数上添加标识符，类型和标识符会一起被用来辨识依赖。

``` java
class ExpensiveCoffeeMaker {
  @Inject @Named("water") Heater waterHeater;
  @Inject @Named("hot plate") Heater hotPlateHeater;
  ...
}
```

然后在`@Provides`方法上也添加标识注解即可。

``` java
@Provides @Named("hot plate") Heater provideHotPlateHeater() {
  return new ElectricHeater(70);
}

@Provides @Named("water") Heater provideWaterHeater() {
  return new ElectricHeater(93);
}
```

依赖不能同时拥有多个标识符注解。

### 编译时验证

Dagger 的[注解处理器](http://docs.oracle.com/javase/6/docs/api/javax/annotation/processing/package-summary.html)是严格的(strict)，如果有绑定无效或者不完整的情况出现，就会导致编译错误。比如安装了以下模块的元件缺失了`Executor`的绑定：

``` java
@Module
class DripCoffeeModule {
  @Provides Heater provideHeater(Executor executor) {
    return new CpuHeater(executor);
  }
}
```

编译时`javac`就会拒绝缺失的绑定:

```
[ERROR] COMPILATION ERROR :
[ERROR] error: java.util.concurrent.Executor cannot be provided without an @Provides-annotated method.
```

这时需要向元件中*任意*一个模块里添加一个被`@Provides`注解修饰并且返回一个`Executor`的方法才能解决错误。`@Inject`，`@Module`和`@Provides`注解的验证是逐个进行的，所有绑定间关系的验证都发生在`@Component`层级。Dagger 1 严格依靠`@Module`级别的验证（可能导致相反的运行时表现），Dagger 2 则直接忽略了这一级的验证（以及`@Module`的配置参数）以取代全图谱的验证。

### 编译时代码生成

Dagger 的注解处理器还可能生成一些名字像是`CoffeeMaker$$Factory.java`或者是`CoffeeMaker$$MembersInjector.java`之类的源码文件。这些文件是 Dagger 的实现细节。你一般不需要直接用这些，不过在单步调试注入的时候还是挺好用的。

## 在工程中使用 Dagger

你需要把`dagger-2.0.jar`文件添加到你应用的运行时里去。为了使用代码生成你还需要添加`dagger-compiler-2.0.jar`到编译时的构建中。

在 Maven 工程中，一个要在`pom.xml`的 dependencies 部分添加进运行时，`dagger-compiler`则添加为编译插件的依赖：

``` xml
<dependencies>
  <dependency>
    <groupId>com.google.dagger</groupId>
    <artifactId>dagger</artifactId>
    <version>2.0</version>
  </dependency>
  <dependency>
    <groupId>com.google.dagger</groupId>
    <artifactId>dagger-compiler</artifactId>
    <version>2.0</version>
    <optional>true</optional>
  </dependency>
</dependencies>
```

## 许可证(License)

> Copyright 2014 Google, Inc.
> Copyright 2012 Square, Inc.
> 
> Licensed under the Apache License, Version 2.0 (the "License");
> you may not use this file except in compliance with the License.
> You may obtain a copy of the License at
> 
>    http://www.apache.org/licenses/LICENSE-2.0
> 
> Unless required by applicable law or agreed to in writing, software
> distributed under the License is distributed on an "AS IS" BASIS,
> WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
> See the License for the specific language governing permissions and
> limitations under the License.

##原文
<http://google.github.io/dagger/>