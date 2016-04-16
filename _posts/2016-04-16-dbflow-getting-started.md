---

layout: post

title: 【译】DBFlow 入门指南

date: 2016-04-16 15:49

categories: Android

tags: [database, android, orm, translation, tutorial]

---

在本节中我们将简要介绍如何构建一个简单的数据库，一张表，并在`模型`之间建立关系。

**蚁后**:我们很想知道如何保存蚁群的数据。我们想要跟踪一个指定蚁群（Colony）中的蚁后（Queen）和其他蚂蚁（Ants），并给他们做上标记。

存在如下关系：

```
蚁群(1对1) -> 蚁后(1对多) -> 蚂蚁
```

## 准备 DBFlow

为了初始化 DBFlow，建议在自定义的`Application`类中添加如下代码：

```java
public class ExampleApplication extends Application {

    @Override
    public void onCreate() {
        super.onCreate();
        FlowManager.init(this);
    }

}
```

不用怕，即使用其他的`Context`来初始化，它也只会持有`Application`的实例作为上下文(context)。

最后，在清单文件中添加如下定义（名称修改为你自定义的 Application 的类名）：

```xml
<application
  android:name="{packageName}.ExampleApplication"
  ...>
</application>
```

## 定义数据库

在 DBFlow 中，`@Database`作为一个占位对象，可以生成一个`BaseDatabaseDefinition`的子类，这个子类将所有表，模型适配器（ModelAdapter），视图（Views），查询（Queries）等等的相互连接集于同一个对象中。所有的连接的建立都是在预编译期完成的，所以不会有任何搜索，反射，或者其他的什么来在运行时拖慢你的应用。

在这个例子中，我们需要定义蚁群保存的位置：

```java
@Database(name = ColonyDatabase.NAME, version = ColonyDatabase.VERSION)
public class ColonyDatabase {

  public static final String NAME = "Colonies";

  public static final int VERSION = 1;
}
```

作为最佳实践，我们把`NAME`和`VERSION`定义为公开常量，这样我们为 DBFlow 定义的其他组件之后需要的话就可以直接引用。

*注意：*如果你想用 [SQLCipher](https://www.zetetic.net/sqlcipher/) 的话请读 [setup here](https://github.com/Raizlabs/DBFlow/blob/master/usage/usage/SQLCipherSupport.md) 

## 创建表并建立关系

保存蚁群数据的地方已经准备好了，现在我们需要明确定义其下的 SQL 数据的保存方式，我们会得到一个`模型（Model）`来表示这些数据。

### 蚁后表

我们自上而下地处理蚁群。每个蚁群中只能有一只蚁后。我们使用 ORM（object-relational mapping， 对象关系映射）模型来定义数据库对象。我们要做的就是在对应为指定数据库表的类中逐个标记需要表示为数据库列的属性。

在 DBFlow中，任何使用 ORM 方式与数据库交互的对象都必须实现`Model`接口。接口 + 基类的定义方式保证了其他类型的`Model`——比如视图或者虚拟表——也可以遵守同样的协议，又不必依赖于某一个基类来规范它们。我们在这里就继承`BaseModel`来方便地创建一个基于`Model`接口的标准表。另外，不强制使用接口也避免了把对象传进本来不是为它们而写的方法里去。

要正确定义一个表我们必须：

1. 在类上添加`@Table`注解
2. 将表指向正确的数据库，在这个例子中就是`ColonyDatabase`
3. 定义至少一个主键
4. 类和其中所有的数据库列都必须是公开的，同包可见的或者是私有加 getter/setter 方法的，这样 DBFlow 生成的类才能访问到它们

一个`蚁后`的基础定义像这样：

```java
@Table(database = ColonyDatabase.class)
public class Queen extends BaseModel {

  @PrimaryKey(autoincrement = true)
  long id;

  @Column
  String name;

}
```

于是我们就定义了一个蚁后，接下来我们需要为这个蚁后定义一个`蚁群`。

### 蚁群

```java
@ModelContainer // 后面再详细解释这个
@Table(database = ColonyDatabase.class)
public class Colony extends BaseModel {

  @PrimaryKey(autoincrement = true)
  long id;

  @Column
  String name;

}
```

现在我们有了一个`蚁后`表和一个`蚁群`表，我们想要在它们之间建立一对一的关系。我们希望数据库来处理数据被移除的情况，比如一场大火把`蚁群`给烧掉了。`蚁群`被烧掉的话，`蚁后`自然也不复存在了，所以我们希望当`蚁群`消失的时候`蚁后`也能同时被『干掉』。

### 一对一

为了建立联系，我们首先需要定义一个子表——也就是`蚁后` ——使用的外键：

```java
@ModelContainer
@Table(database = ColonyDatabase.class)
public class Queen extends BaseModel {

  //……之前的代码

  @Column
  @ForeignKey(saveForeignKeyModel = false)
  Colony colony;

}
```

将外键定义为`Model`的话，使用查询语句查询外键引用的列的值时就会自动调取外键所指定的关系。出于性能的考虑，我们默认指定`saveForiegnKeyModel=false`，这样保存`蚁后`的数据时并不会把父表`蚁群`的数据也保存起来。

如果你想保留这个对应关系的话，就设置`saveForeignKeyModel=true`。

从 3.0 版本开始，我们不再需要给每一个引用到的列显式定义`@ForeignKeyReference`了。DBFlow 会基于被引用到的表的`@PrimaryKey`来把它们自动添加到表的定义里去。它们会表示为`{外键属性名}_{被引用的列名}`的格式。

### 蚂蚁表与一对多

我们现在有了一个`蚁群`和一个从属于它的`蚁后`，我们需要一些蚂蚁来效忠于她了！

```java
@Table(database = ColonyDatabase.class)
public class Ant extends BaseModel {

  @PrimaryKey(autoincrement = true)
  long id;

  @Column
  String type;

  @Column
  boolean isMale;

  @ForeignKey(saveForeignKeyModel = false)
  ForeignKeyContainer<Queen> queenForeignKeyContainer;

  /**
  * 一个把模型设置给蚁后的例子。
  */
  public void associateQueen(Queen queen) {
    queenForeignKeyContainer = FlowManager.getContainerAdapter(Queen.class).toForeignKeyContainer(queen);
  }
}
```

我们定义了`type（类型）`，比如可以是『工蚁』，『兵蚁』，或者『其它』。还有蚂蚁的雌雄。

因为我们可能有成千上万个蚂蚁，我们在这个实例中使用了`ForeignKeyContainer`。由于性能原因，与`蚁后`的关系是『懒加载』的，而且只有在我们调用`toModel()`时才会执行对`蚁后`的查询。也就是说，为了给`ForeignKeyContainer`设置正确的值，你*应该*调用它生成的`FlowManager.getContainerAdapter(Queen.class).toForeignKeyContainer(queen)`方法来把它转换成`ForeignKeyContainer`。

最后，使用`@ForeignKeyContainer`可以避免循环引用问题。如果`蚁后`和`蚁群`通过`Model`互相引用，最终会引起`StackOverFlowError`，因为它们会不停地从数据库中加载彼此的数据。

接下来，我们通过懒加载（因为我们可能存有成千上万，甚至上百万的数据）蚂蚁来建立一对多的关系：

```java
@ModelContainer
@Table(database = ColonyDatabase.class)
public class Queen extends BaseModel {
  //...

  // 要能被 DELETE 访问到
  List<Ant> ants;

  @OneToMany(methods = {OneToMany.Method.SAVE, OneToMany.Method.DELETE}, variableName = "ants")
  public List<Ant> getMyAnts() {
    if (ants == null || ants.isEmpty()) {
            ants = SQLite.select()
                    .from(Ant.class)
                    .where(Ant_Table.queenForeignKeyContainer_id.eq(id))
                    .queryList();
    }
    return ants;
  }
}
```

如果你想自己来懒加载表间关系，就指定`OneToMany.Method.DELETE`和`SAVE`，不用`ALL`。如果你希望`蚁后`的数据发生变化时不要保存它们，就只指定`DELETE`和`LOAD`。