---

layout: post

title: 【译】Google Data Binding Library 官方指南

date: 2016-05-26 16:46:00 +0800

categories: Translation

tags: [android, mvvm, databinding, google, translation, tutorial]

---

本文档意在讲解如何使用 Data Binding Library (下称DBL) 来编写描述性的布局，同时尽量减少用于连接应用逻辑和布局的粘合代码 (glue code)。

DBL同时保证了灵活性和广泛的兼容性——这是个支持库，所以 **Android 2.1 (API level 7+)** 以上的版本都可以使用。

要使用数据绑定 (data binding)，Gradle 插件的版本需要达到 **1.5.0-alpha1** 或更高。

## 构建环境

为了开始使用数据绑定，首先要从 Android SDK manager 的 Support repository 中下载这个库。

要为你的 app 配置数据绑定，需要在 app 模块中的 `build.gradle` 文件中添加 `databinding` 代码块。

使用以下代码来配置数据绑定：

```groovy
android {
    ....
    dataBinding {
        enabled = true
    }
}
```

如果你有 app 模块依赖于使用了数据绑定的库，那么你的 app 模块也要在 `build.gradle` 中配置好数据绑定。

另外，确保你使用的 Android Studio 的版本可以兼容。`Android Studio 1.3` 及以上版本添加了数据绑定的支持，详情参考 [Android Studio Support for Data Binding](https://developer.android.com/topic/libraries/data-binding/index.html#studio_support) 。

## 布局文件

### 编写第一段数据绑定表达式

数据绑定的布局文件和普通的稍有不同，它以 `layout` 作为根元素，后面跟着 `data`元素和一个 `view` 根元素。这个 『view』 就是你在普通布局文件中用作根元素的那个。举个例子：

```xml
<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android">
   <data>
       <variable name="user" type="com.example.User"/>
   </data>
   <LinearLayout
       android:orientation="vertical"
       android:layout_width="match_parent"
       android:layout_height="match_parent">
       <TextView android:layout_width="wrap_content"
           android:layout_height="wrap_content"
           android:text="@{user.firstName}"/>
       <TextView android:layout_width="wrap_content"
           android:layout_height="wrap_content"
           android:text="@{user.lastName}"/>
   </LinearLayout>
</layout>
```

`data` 元素中的 user `variable` 描述了一个可能被这个布局使用的属性。

```xml
<variable name="user" type="com.example.User"/>
```

布局文件中的表达式使用“ `@{}` ” 语法写在视图的属性中。比如这里，这个 TextView 的 text 就设置成了 user 的属性：

```xml
<TextView android:layout_width="wrap_content"
          android:layout_height="wrap_content"
          android:text="@{user.firstName}"/>
```

### 数据对象 (Data Object)

咱们假设你现在有一个普通 Java 对象 (POJO)，User：

```java
public class User {
   public final String firstName;
   public final String lastName;
   public User(String firstName, String lastName) {
       this.firstName = firstName;
       this.lastName = lastName;
   }
}
```

这个类型的对象的数据是不变的。这种只读一次数据然后就永远不变的对象在各种应用中都很常见。用 JavaBeans 对象也是可以的：

```java
public class User {
   private final String firstName;
   private final String lastName;
   public User(String firstName, String lastName) {
       this.firstName = firstName;
       this.lastName = lastName;
   }
   public String getFirstName() {
       return this.firstName;
   }
   public String getLastName() {
       return this.lastName;
   }
}
```

从数据绑定的整体来看，这两种类是一样的。刚才那个 TextView 的 `android:text` 属性使用到的 `@{user.firstName}` 表达式在前一种类中会直接访问 `firstName` 属性，在后一种中则会使用 `getFirstName()` 方法。作为替代，如果有个 `firstName()` 方法也是可以解析出来的。

### 绑定数据

默认情况下，一个 Binding 类会依照“基于布局文件的名字，把它转换成帕斯卡命名法，再加上‘Binding’后缀”的规则自动生成。比如上面的布局文件叫 `main_activity.xml` ，那么生成的类就叫 `MainActivityBinding` 。这个类持有着布局文件中所有属性（比如 `user` 变量）与视图的绑定，并且知道如何给绑定表达式赋值。创建绑定最简单的方法就是在填充 (inflating) 布局的时候创建：

```java
@Override
protected void onCreate(Bundle savedInstanceState) {
   super.onCreate(savedInstanceState);
   MainActivityBinding binding = DataBindingUtil.setContentView(this, R.layout.main_activity);
   User user = new User("Test", "User");
   binding.setUser(user);
}
```

然后就搞定啦！把应用跑起来，你就能看到 Test User 显示在 UI 中了。另外，你还可以用这种方式拿到视图：

```java
MainActivityBinding binding = MainActivityBinding.inflate(getLayoutInflater());
```

如果你要在 ListView 或者 RecyclerView 的适配器中使用数据绑定，你最好使用：

```java
ListItemBinding binding = ListItemBinding.inflate(layoutInflater, viewGroup, false);
//或者
ListItemBinding binding = DataBindingUtil.inflate(layoutInflater, R.layout.list_item, viewGroup, false);
```

### 绑定事件

事件可以直接绑定到处理器 (handler) 方法上，就像 `android:onClick` 分配到 Activity 中的方法上一样。除了一些特殊情况，事件属性名和监听器的方法名一致。举例来说， `View.OnLongClickListener` 里有一个 `onLongClick()` 方法，所以这个事件的属性就叫 `android:onLongClick` 。

要把事件分配给它的 handler，只要写一个普通的绑定表达式，用它的值作为方法名就可以了。比如，如果你的数据 (data) 对象有两个方法：

```java
public class MyHandlers {
    public void onClickFriend(View view) { ... }
    public void onClickEnemy(View view) { ... }
}
```

绑定表达式就可以为视图分配点击监听器：

```java
<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android">
   <data>
       <variable name="handlers" type="com.example.Handlers"/>
       <variable name="user" type="com.example.User"/>
   </data>
   <LinearLayout
       android:orientation="vertical"
       android:layout_width="match_parent"
       android:layout_height="match_parent">
       <TextView android:layout_width="wrap_content"
           android:layout_height="wrap_content"
           android:text="@{user.firstName}"
           android:onClick="@{user.isFriend ? handlers.onClickFriend : handlers.onClickEnemy}"/>
       <TextView android:layout_width="wrap_content"
           android:layout_height="wrap_content"
           android:text="@{user.lastName}"
           android:onClick="@{user.isFriend ? handlers.onClickFriend : handlers.onClickEnemy}"/>
   </LinearLayout>
</layout>
```

有一些特定的点击事件处理器已经存在了，它们需要一个 `android:onClick` 以外的属性来避免冲突。为了避免这些冲突，创建有如下属性：

| 类名                                       | 监听器 Setter                               | 属性                    |
| ---------------------------------------- | ---------------------------------------- | --------------------- |
| [SearchView](https://developer.android.com/reference/android/widget/SearchView.html) | [setOnSearchClickListener(View.OnClickListener)](https://developer.android.com/reference/android/widget/SearchView.html#setOnSearchClickListener(android.view.View.OnClickListener)) | android:onSearchClick |
| [ZoomControls](https://developer.android.com/reference/android/widget/ZoomControls.html) | [setOnZoomInClickListener(View.OnClickListener)](https://developer.android.com/reference/android/widget/ZoomControls.html#setOnZoomInClickListener(android.view.View.OnClickListener)) | android:onZoomIn      |
| [ZoomControls](https://developer.android.com/reference/android/widget/ZoomControls.html) | [setOnZoomOutClickListener(View.OnClickListener)](https://developer.android.com/reference/android/widget/ZoomControls.html#setOnZoomOutClickListener(android.view.View.OnClickListener)) | android:onZoomOut     |

## 布局细节

### 导入 (Imports)

`data` 元素中可以添加有零或多个 `import` 元素。这些元素提供了对类的便捷访问，就像在 Java 中一样。

```xml
<data>
    <import type="android.view.View"/>
</data>
```

于是就可以在绑定表达式中使用 View 了：

```xml
<TextView
   android:text="@{user.lastName}"
   android:layout_width="wrap_content"
   android:layout_height="wrap_content"
   android:visibility="@{user.isAdult ? View.VISIBLE : View.GONE}"/>
```

如果类名冲突，其中一个类就可以用“alias (别名) :” 来重命名：

```xml
<import type="android.view.View"/>
<import type="com.example.real.estate.View"
        alias="Vista"/>
```

于是在这个布局文件中， `Vista` 就可以用来引用 `com.example.real.estate.View` ， `View` 则用来引用 `android.view.View` 。导入的类型可以在变量和表达式中用作类型引用：

```xml
<data>
    <import type="com.example.User"/>
    <import type="java.util.List"/>
    <variable name="user" type="User"/>
    <variable name="userList" type="List&lt;User>"/>
</data>
```

> **注意** ：Android Studio 目前还不能处理导入，所以导入的变量可能无法使用自动完成。你的应用还是可以正常编译，你也可以在变量声明中使用含包名的完整类名 (qualified names) 来暂时将就一下。

```xml
<TextView
   android:text="@{((User)(user.connection)).lastName}"
   android:layout_width="wrap_content"
   android:layout_height="wrap_content"/>
```

导入的类型还可以用来在表达式中引用静态域：

```xml
<data>
    <import type="com.example.MyStringUtils"/>
    <variable name="user" type="com.example.User"/>
</data>
…
<TextView
   android:text="@{MyStringUtils.capitalize(user.lastName)}"
   android:layout_width="wrap_content"
   android:layout_height="wrap_content"/>
```

与 Java 中一样， `java.lang.*` 是默认导入的。

### 变量 (Variables)

`data` 元素内可以使用任意数量的 `variable` 元素。每个 `variable` 元素都描述了一个可能在当前布局文件内通过绑定表达式设置给布局的属性。

```xml
<data>
    <import type="android.graphics.drawable.Drawable"/>
    <variable name="user"  type="com.example.User"/>
    <variable name="image" type="Drawable"/>
    <variable name="note"  type="String"/>
</data>
```

变量的类型执行了编译时检查，所以如果一个变量实现了 [Observable](https://developer.android.com/reference/android/databinding/Observable.html) 接口，或者是一个 [observable 集合](https://developer.android.com/topic/libraries/data-binding/index.html#observable_collections) ，它会反射为(reflected in) 这个类型。如果这个变量是一个没有实现 Observable* 接口的基类或者接口，那么这个变量就 **不会被** 观察 (observed) ！

如果存在着多种配置的布局文件（比如横屏竖屏），这些文件中的变量是一起处理的。所以这些布局文件中不能有冲突的变量声明。

生成的绑定类中会有每个变量的 setter 和 getter。这些变量在 setter 被调用之前取默认的 Java 值——引用类型是 `null` ， `int` 类型是 `0` ， `boolean` 类型是 `false` ，等等。

一个叫 `context` 的特殊变量会自动生成。 `context` 的值就是根视图的 `getContext()` 方法返回的值。如果显式声明了一个叫 `context` 的变量，默认的这个就会被覆盖。

### 自定义绑定类名

默认情况下，生成的绑定类名以布局文件名为基础，以大写字母开头，去掉下划线，把下划线后面的字母大写，最后加上“Binding”作为后缀。这个类会放在当前模块包下的 databinding 包里。举例来说，布局文件 `contact_item.xml` 会生成 `ContactItemBinding` 类。如果模块的包名是 `com.example.my.app` ，它就会被放在 `com.example.my.app.databinding` 包中。

绑定类也可以改名或放到不同的包中，只要修改 `data` 元素的 `class` 属性即可。比如：

```xml
<data class="ContactItem">
    ...
</data>
```

这样绑定类就会叫 `ContactItem` ，放在模块包中的 databinding 包下。如果想把它放到模块包中的其他包下，可以在前面添加“.”作为前缀：

```xml
<data class=".ContactItem">
    ...
</data>
```

这样的话， `ContactItem` 就会直接放在模块包的根目录里。如果进一步指定完整包名，则可以放到任意包中：

```xml
<data class="com.example.ContactItem">
    ...
</data>
```

### 包含 (Includes)

通过在属性中使用应用命名空间及变量名，变量还可以传递到 include 进来的布局的绑定中：

```xml
<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android"
        xmlns:bind="http://schemas.android.com/apk/res-auto">
   <data>
       <variable name="user" type="com.example.User"/>
   </data>
   <LinearLayout
       android:orientation="vertical"
       android:layout_width="match_parent"
       android:layout_height="match_parent">
       <include layout="@layout/name"
           bind:user="@{user}"/>
       <include layout="@layout/contact"
           bind:user="@{user}"/>
   </LinearLayout>
</layout>
```

这种情况下， `name.xml` 和 `contact.xml` 中都必须有一个 `user` 变量。

数据绑定不支持作为 merge 元素直接子元素的情况。比如 **以下布局就不受支持：**

```xml
<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android"
        xmlns:bind="http://schemas.android.com/apk/res-auto">
   <data>
       <variable name="user" type="com.example.User"/>
   </data>
   <merge>
       <include layout="@layout/name"
           bind:user="@{user}"/>
       <include layout="@layout/contact"
           bind:user="@{user}"/>
   </merge>
</layout>
```

### 表达式语言

#### 通用特性

表达式语言和 Java 表达式很像。这些是一样的：

- 数学运算符 + -  * %
- 字符串连接符 +
- 逻辑运算符 && ||
- 位运算符 & | ^
- 一元运算符  + - ! ~
- 移位运算符 >> >>> <<
- 比较运算符 == > < >= <=
- instanceof
- 分组 ()
- 字面量 - 字符，字符串，数字，null
- 类型转换
- 方法调用
- 域访问
- 数组访问 []
- 三元运算符 ?:

比如：

```java
android:text="@{String.valueOf(index + 1)}"
android:visibility="@{age &lt; 13 ? View.GONE : View.VISIBLE}"
android:transitionName='@{"image_" + id}'
```

#### 没有的操作

有一些操作 Java 中有，但是不能在表达式语法中用。

- this
- super
- new
- 显式泛型调用

#### null 合并运算符

null 合并运算符（??）在左操作数不为 null 选择左操作数，否则选择右操作数。

```java
android:text="@{user.displayName ?? user.lastName}"
```

在功能上等同于：

```java
android:text="@{user.displayName != null ? user.displayName : user.lastName}"
```

#### 属性引用

第一种已经在前文中讨论过了：简化版 JavaBean 引用。表达式引用类属性的时候，对于域，getter，和可观察域 (ObservableField) 使用同样的格式。

```java
android:text="@{user.lastName}"
```

#### 避免空指针异常

生成的数据绑定代码会自动做 null 检查，避免空指针异常。佛一个咱抔，在表达式 `@{user.name}` 中，如果 `user` 的值是 null， `user.name` 会被分配一个默认值（null）。如果你引用 `user.age` 而 age 又是 `int` 类型的，那它就会默认指定为0。

#### 集合

普通的集合：数组，列表，稀疏列表，映射，都可以使用 `[]` 操作符来便捷访问。

```xml
<data>
    <import type="android.util.SparseArray"/>
    <import type="java.util.Map"/>
    <import type="java.util.List"/>
    <variable name="list" type="List&lt;String>"/>
    <variable name="sparse" type="SparseArray&lt;String>"/>
    <variable name="map" type="Map&lt;String, String>"/>
    <variable name="index" type="int"/>
    <variable name="key" type="String"/>
</data>
…
android:text="@{list[index]}"
…
android:text="@{sparse[index]}"
…
android:text="@{map[key]}"
String Literals
```

#### 字符串字面量

如果在属性值上使用单引号，就可以在表达式中使用双引号了：

```xml
android:text='@{map["firstName"]}'
```

要在属性值上使用双引号也是可以的。如果要这样，字符串字面量就要使用 `&quot` 或者反引号（`）。

```xml
android:text="@{map[`firstName`}"
android:text="@{map[&quot;firstName&quot;]}"
```

#### 资源

可以使用标准语法作为表达式的一部分来访问资源：

```xml
android:padding="@{large? @dimen/largePadding : @dimen/smallPadding}"
```

格式化字符串和 plural (复数字符串) 可以通过提供参数来赋值：

```xml
android:text="@{@string/nameFormat(firstName, lastName)}"
android:text="@{@plurals/banana(bananaCount)}"
```

如果一个 plural 需要多个参数，那就应该把所有参数都传进去：

```xml

  Have an orange
  Have %d oranges

android:text="@{@plurals/orange(orangeCount, orangeCount)}"
```

有些资源需要显式的类型赋值。

| 类型                | 普通引用      | 表达式引用              |
| ----------------- | --------- | ------------------ |
| String[]          | @array    | @stringArray       |
| int[]             | @array    | @intArray          |
| TypedArray        | @array    | @typedArray        |
| Animator          | @animator | @animator          |
| StateListAnimator | @animator | @stateListAnimator |
| color `int`       | @color    | @color             |
| ColorStateList    | @color    | @colorStateList    |

## 数据对象

任何普通 Java 对象（POJO）都可以用作数据绑定，但是修改 POJO 不会引起 UI 更新。数据绑定真正的力量在于给予数据对象在数据发生变化是发出通知的能力。有着三种不同的数据变化通知机制，[可观察对象 (Observable objects)](https://developer.android.com/topic/libraries/data-binding/index.html#observable_objects) ，[可观察域 (observable fields)](https://developer.android.com/topic/libraries/data-binding/index.html#observablefields) ，和[可观察集合 (observable collection)](https://developer.android.com/topic/libraries/data-binding/index.html#observable_collections) 。

当以上可观察数据对象之一绑定到 UI 上而且数据对象的属性发生了变化，UI 就会自动更新。

### 可观察对象

实现了 [Observable](https://developer.android.com/reference/android/databinding/Observable.html) 接口的类可以在一个被绑定的对象上添加一个监听器，来监听这个对象所有属性的变化。

Observable 接口有着一个添加移除监听器的机制，但怎样通知还是要由开发者决定。为了简化开发，创建有一个基类 [BaseObservable](https://developer.android.com/reference/android/databinding/BaseObservable.html) ，它实现了监听器注册机制。但是数据类依然需要在属性发生变化时发出通知。可以通过在 getter 上添加 [Bindable](https://developer.android.com/reference/android/databinding/Bindable.html) 注解并在 setter 里发出通知来完成。

```java
private static class User extends BaseObservable {
   private String firstName;
   private String lastName;
   @Bindable
   public String getFirstName() {
       return this.firstName;
   }
   @Bindable
   public String getLastName() {
       return this.lastName;
   }
   public void setFirstName(String firstName) {
       this.firstName = firstName;
       notifyPropertyChanged(BR.firstName);
   }
   public void setLastName(String lastName) {
       this.lastName = lastName;
       notifyPropertyChanged(BR.lastName);
   }
}
```

Bindable 注解在编译时在 BR 类文件里生成了一个入口。BR 类文件会生成在模块包里。如果数据类的基类不能修改，则可以使用方便的 [PropertyChangeRegistry](https://developer.android.com/reference/android/databinding/PropertyChangeRegistry.html) 实现 Observable 接口来高效地保存和通知监听器。

### 可观察域

创建 Observable 类还是需要一点工作的，想节约时间或者只有很少几个属性要处理的开发者可以直接使用 `ObservableField` 和几个兄弟类  `ObservableBoolean`，`ObservableByte` ，`ObservableChar` ， `ObservableShort` ， `ObservableInt` ， `ObservableLong` ， `ObservableFloat` ， `ObservableDouble` ，和 `ObservableParcelable` 。`ObservableField` 是一个自包含的可观察对象，里面只有一个域。基本类型的几个版本避免了访问操作时的装箱和拆箱。要使用的话，在数据类中创建一个 public final 的域即可：

```java
private static class User {
   public final ObservableField<String> firstName =
       new ObservableField<>();
   public final ObservableField<String> lastName =
       new ObservableField<>();
   public final ObservableInt age = new ObservableInt();
}
```

这样就行了！如果要访问它的值，就使用 set 和 get 访问器方法：

```java
user.firstName.set("Google");
int age = user.age.get();
```

### 可观察集合

有些应用会使用更加动态的结构来保持数据。可观察集合允许通过键名来访问数据对象。[ObservableArrayMap](https://developer.android.com/reference/android/databinding/ObservableArrayMap.html) 在键是引用类型的情况下很有用，比如是字符串的时候。

```java
ObservableArrayMap<String, Object> user = new ObservableArrayMap<>();
user.put("firstName", "Google");
user.put("lastName", "Inc.");
user.put("age", 17);
```

在布局文件中可以直接用字符串键来访问映射：

```xml
<data>
    <import type="android.databinding.ObservableMap"/>
    <variable name="user" type="ObservableMap&lt;String, Object>"/>
</data>
…
<TextView
   android:text='@{user["lastName"]}'
   android:layout_width="wrap_content"
   android:layout_height="wrap_content"/>
<TextView
   android:text='@{String.valueOf(1 + (Integer)user["age"])}'
   android:layout_width="wrap_content"
   android:layout_height="wrap_content"/>
```

[ObservableArrayList](https://developer.android.com/reference/android/databinding/ObservableArrayList.html) 则在键是整数时很有用：

```java
ObservableArrayList<Object> user = new ObservableArrayList<>();
user.add("Google");
user.add("Inc.");
user.add(17);
```

在列表中使用索引访问列表：

```xml
<data>
    <import type="android.databinding.ObservableList"/>
    <import type="com.example.my.app.Fields"/>
    <variable name="user" type="ObservableList&lt;Object>"/>
</data>
…
<TextView
   android:text='@{user[Fields.LAST_NAME]}'
   android:layout_width="wrap_content"
   android:layout_height="wrap_content"/>
<TextView
   android:text='@{String.valueOf(1 + (Integer)user[Fields.AGE])}'
   android:layout_width="wrap_content"
   android:layout_height="wrap_content"/>
```

## 生成绑定

生成的绑定类在布局中将布局变量和视图连接在一起。如之前讨论过的，类名和包名都是可以自定义的。生成的绑定类都继承自 [ViewDataBinding](https://developer.android.com/reference/android/databinding/ViewDataBinding.html) 。

### 创建

为了保证视图结构 (View hierarchy) 在绑定到布局中包含表达式的视图上之前不受干扰，应该在填充视图后马上进行绑定。绑定到布局的方法有几种。其中最通用的就是使用 Binding 类的静态方法。 inflate 方法在同一步中执行视图填充和绑定。还有一个更简单的只接受一个 LayoutInflater  的版本，以及另一个多接受一个 ViewGroup 的版本:

```java
MyLayoutBinding binding = MyLayoutBinding.inflate(layoutInflater);
MyLayoutBinding binding = MyLayoutBinding.inflate(layoutInflater, viewGroup, false);
```

如果通过其他方式填充了布局，则额外执行绑定：

```java
MyLayoutBinding binding = MyLayoutBinding.bind(viewRoot);
```

有的时候绑定没法预知。这种时候就要用 [DataBindingUtil](https://developer.android.com/reference/android/databinding/DataBindingUtil.html) 类来创建绑定了：

```java
ViewDataBinding binding = DataBindingUtil.inflate(LayoutInflater, layoutId,
    parent, attachToParent);
ViewDataBinding binding = DataBindingUtil.bindTo(viewRoot, layoutId);
```

### 带 ID 的视图

布局中每个有 ID 的视图会分别生成一个 public final 的域。绑定会过一遍视图结构，抽取出每一个带 ID 的视图。这种机制比为每一个视图执行一次 findViewById	 要快。举例来说：

```xml
<layout xmlns:android="http://schemas.android.com/apk/res/android">
   <data>
       <variable name="user" type="com.example.User"/>
   </data>
   <LinearLayout
       android:orientation="vertical"
       android:layout_width="match_parent"
       android:layout_height="match_parent">
       <TextView android:layout_width="wrap_content"
           android:layout_height="wrap_content"
           android:text="@{user.firstName}"
   android:id="@+id/firstName"/>
       <TextView android:layout_width="wrap_content"
           android:layout_height="wrap_content"
           android:text="@{user.lastName}"
  android:id="@+id/lastName"/>
   </LinearLayout>
</layout>
```

生成的绑定类里面会有：

```java
public final TextView firstName;
public final TextView lastName;
```

ID 不像不用数据绑定时那么必要，但是有些场景下通过代码访问视图还是有必要的。

### 变量

每个变量都会得到一个访问器方法。

```xml
<data>
    <import type="android.graphics.drawable.Drawable"/>
    <variable name="user"  type="com.example.User"/>
    <variable name="image" type="Drawable"/>
    <variable name="note"  type="String"/>
</data>
```

会在绑定中生成 getter 和 setter：

```java
public abstract com.example.User getUser();
public abstract void setUser(com.example.User user);
public abstract Drawable getImage();
public abstract void setImage(Drawable image);
public abstract String getNote();
public abstract void setNote(String note);
```

### ViewStub

ViewStub 和普通的 View 有些不同。它们一开始是不可见的，直到它们被设置成可见的或者显式要求填充内容的时候，它们才会填充一个别的布局来替换掉自己。

因为 `ViewStub` 本质上不存在与视图结构中，绑定中的视图就也不能够存在。因为视图都是 final 的，一个 [ViewStubProxy](https://developer.android.com/reference/android/databinding/ViewStubProxy.html) 就替代了 `ViewStub` ，以提供给开发者一个在 ViewStub 存在的时候访问它，在 `ViewStub` 被填充之后访问填充视图的方法。

填充了另一个布局之后，必须基于新布局建立一个绑定。所以， `ViewStubProxy` 必须监听 `ViewStub` 的 `ViewStub.OnInflateListener` ，到时好建立绑定。因为只能存在一个，所以 `ViewStubProxy` 允许开发者设置一个 `OnInflateListener` ，它会在建立绑定之后回调监听器。

### 高级绑定

#### 动态变量

有时候特定绑定类是不可知的。比如操作随机布局的 `RecyclerView.Adapter` 就没法知道对应的绑定类。它还是要通过 `onBindViewHolder(VH, int)` 来设置绑定的值。

在这个例子里，RecyclerView 绑定的所有布局都有一个“item”变量。`BindingHolder` 有一个 `getBinding` 方法，返回 `ViewDataBinding` 基类。

```java
public void onBindViewHolder(BindingHolder holder, int position) {
   final T item = mItems.get(position);
   holder.getBinding().setVariable(BR.item, item);
   holder.getBinding().executePendingBindings();
}
```

#### 立刻绑定

当变量或可观察对象发生变化时，绑定会在下一帧前计划 (scheduled to) 执行修改。但是有的时候绑定必须马上执行。要强制执行的话，就用 [executePendingBindings()](https://developer.android.com/reference/android/databinding/ViewDataBinding.html#executePendingBindings()) 方法。

#### 后台线程

只要你的数据模型不是集合，你就可以在后台线程修改它。数据绑定为了避免并发问题，在赋值的时候会局部化 (localize) 每个变量或者域。

## 属性 setter

绑定的值变化时，生成的绑定类会用绑定表达式来调用视图上的 setter 方法。数据绑定框架有这么几种方式来自定义用哪个方法来设置值。

### 自动化 setter

对于一个 attribute，数据绑定会尝试寻找 setAttribute 方法。命名空间是无所谓的，只与属性名有关。

比如与 TextView 的 `android:text` 属性关联的表达式会寻找 setText(String)。如果表达式返回一个 int 值，数据绑定就会去找 setText(int) 方法。注意要让表达式返回正确的类型，需要的时候要做类型转换。记得就算找不到名字对应的属性，数据绑定还是会正常工作的。所以你可以非常简单地为随便哪个 setter “创建”一个属性。比如支持库里的 DrawerLayout 一个属性都没有，但是有许多个 setter。于是你就可以用自动化 setter 来调用它们。

```xml
<android.support.v4.widget.DrawerLayout
    android:layout_width="wrap_content"
    android:layout_height="wrap_content"
    app:scrimColor="@{@color/scrim}"
    app:drawerListener="@{fragment.drawerListener}"/>
```

### 重命名 setter

有些属性需要自定义绑定逻辑。比如 `android:paddingLeft` 就没有对应的 setter，但是有一个 `setPadding(left, top, right, bottom)` 方法。于是开发者就可以用一个静态绑定适配器方法加上 [BindingAdapter](https://developer.android.com/reference/android/databinding/BindingAdapter.html) 注解来自定义属性的调用方法。

Android 的属性已经创建好 `BindingAdapter` 了，比如 `paddingLeft` 的：

```java
@BindingAdapter("android:paddingLeft")
public static void setPaddingLeft(View view, int padding) {
   view.setPadding(padding,
                   view.getPaddingTop(),
                   view.getPaddingRight(),
                   view.getPaddingBottom());
}
```

绑定适配器在其他类型的自定义上也很有用。比如可以用异步加载器来加载图片。

开发者自定义的绑定适配器在发生冲突的时候会覆盖默认的适配器。

你还可以声明接受多个参数的适配器。

```java
@BindingAdapter({"bind:imageUrl", "bind:error"})
public static void loadImage(ImageView view, String url, Drawable error) {
   Picasso.with(view.getContext()).load(url).error(error).into(view);
}
```

```xml
<ImageView app:imageUrl=“@{venue.imageUrl}”
app:error=“@{@drawable/venueError}”/>
```

如果 `imageurl` 和 `error` 都设置给了一个 ImageView，而且 *imageUrl* 是字符串 *error* 是 drawable 的话，适配器就会被调用。

- 匹配时会忽略自定义命名空间。
- 你也可以为 android 命名空间的属性写适配器。

绑定适配器可以选择性地接受旧值。接受新旧两种值的方法需要把旧值放在第一位，新值跟在后面：

```java
@BindingAdapter("android:paddingLeft")
public static void setPaddingLeft(View view, int oldPadding, int newPadding) {
   if (oldPadding != newPadding) {
       view.setPadding(newPadding,
                       view.getPaddingTop(),
                       view.getPaddingRight(),
                       view.getPaddingBottom());
   }
}
```

事件处理器只能用只有一个抽象方法的接口或者抽象类。比如：

```java
@BindingAdapter("android:onLayoutChange")
public static void setOnLayoutChangeListener(View view, View.OnLayoutChangeListener oldValue,
       View.OnLayoutChangeListener newValue) {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.HONEYCOMB) {
        if (oldValue != null) {
            view.removeOnLayoutChangeListener(oldValue);
        }
        if (newValue != null) {
            view.addOnLayoutChangeListener(newValue);
        }
    }
}
```

如果一个监听器有许多个方法，就要分割成数个监听器。比如 `View.OnAttachStateChangeListener` 有两个方法： `onViewAttachedToWindow()` 和 `onViewDetachedFromWindow()` 。我们得创建两个接口来把属性分离开，分别处理。

```java
@TargetApi(VERSION_CODES.HONEYCOMB_MR1)
public interface OnViewDetachedFromWindow {
    void onViewDetachedFromWindow(View v);
}

@TargetApi(VERSION_CODES.HONEYCOMB_MR1)
public interface OnViewAttachedToWindow {
    void onViewAttachedToWindow(View v);
}
```

因为修改一个监听器会影响到另一个监听器，所以我们要写三个不同的绑定适配器，两个监听分别有一个，还有一个同时处理两个监听。

```java
@BindingAdapter("android:onViewAttachedToWindow")
public static void setListener(View view, OnViewAttachedToWindow attached) {
    setListener(view, null, attached);
}

@BindingAdapter("android:onViewDetachedFromWindow")
public static void setListener(View view, OnViewDetachedFromWindow detached) {
    setListener(view, detached, null);
}

@BindingAdapter({"android:onViewDetachedFromWindow", "android:onViewAttachedToWindow"})
public static void setListener(View view, final OnViewDetachedFromWindow detach,
        final OnViewAttachedToWindow attach) {
    if (VERSION.SDK_INT >= VERSION_CODES.HONEYCOMB_MR1) {
        final OnAttachStateChangeListener newListener;
        if (detach == null && attach == null) {
            newListener = null;
        } else {
            newListener = new OnAttachStateChangeListener() {
                @Override
                public void onViewAttachedToWindow(View v) {
                    if (attach != null) {
                        attach.onViewAttachedToWindow(v);
                    }
                }

                @Override
                public void onViewDetachedFromWindow(View v) {
                    if (detach != null) {
                        detach.onViewDetachedFromWindow(v);
                    }
                }
            };
        }
        final OnAttachStateChangeListener oldListener = ListenerUtil.trackListener(view,
                newListener, R.id.onAttachStateChangeListener);
        if (oldListener != null) {
            view.removeOnAttachStateChangeListener(oldListener);
        }
        if (newListener != null) {
            view.addOnAttachStateChangeListener(newListener);
        }
    }
}
```

因为 View 使用 add 和 remove 来添加和移除监听器，而不是直接设置一个 View.OnAttachStateChangeListener，所以上面的例子比正常情况下要复杂一点。 `android.databinding.adapters.ListenerUtil` 类可以记录之前的监听器，所以可以在绑定适配器里移除它们。

在  `OnViewDetachedFromWindow`  和 `OnViewAttachedToWindow` 接口上添加 `@TargetApi(VERSION_CODES.HONEYCOMB_MR1)` 注解，数据绑定代码生成器就可以知道在 Honeycomb MR1 和以后的设备上才需要生成这些监听器，也就是 `addOnAttachStateChangeListener(View.OnAttachStateChangeListener)` 支持的版本。

## 转换器 (Converters)

### 对象转换

绑定表达式返回一个 Object 的时候会从自动化，重命名和自定义 setter 里选择一个使用。这个 Object 会转换成被选中的 setter 的参数类型。

在用 ObservableMaps 来保持数据的情况下很方便。比如：

```xml
<TextView
   android:text='@{userMap["lastName"]}'
   android:layout_width="wrap_content"
   android:layout_height="wrap_content"/>
```

`userMap` 会返回一个 Object，Object 会自动转换成 setter setText(CharSequence) 中参数的类型。如果可能的参数类型有多个，开发者就需要在表达式中手动转换。

### 自定义转换

有的时候需要在指定的类型中自动转换，比如设置背景时：

```xml
<View
   android:background="@{isError ? @color/red : @color/white}"
   android:layout_width="wrap_content"
   android:layout_height="wrap_content"/>
```

这里 background 接受的是 `Drawable` 类型，但是 color 是整形的。如果需要的是 `Drawable` 而返回的是整形， `int` 就需要转换成 `ColorDrawable` 使用。可以使用静态方法配合 BindingConversion 注解来执行转换：

```java
@BindingConversion
public static ColorDrawable convertColorToDrawable(int color) {
   return new ColorDrawable(color);
}
```

记住转换只能发生在 setter 级别，所以混合类型是 **不允许的** ：

```xml
<View
   android:background="@{isError ? @drawable/error : @color/white}"
   android:layout_width="wrap_content"
   android:layout_height="wrap_content"/>
```

## Android Studio 的数据绑定支持

Android Studio 支持数据绑定代码的许多种编辑特性。可算到最后一个栗子了，它支持如下数据绑定表达式特性：

- 语法高亮
- 表达式语言语法错误检查
- XML 代码补全
- 引用，包括代码导航（比如跳转到实现）和快速文档

> **记住:** 数组和泛型，比如 Observable 类，在实际上没有错误的时候可能还是会显示有错误。

预览窗口会显示表达式的默认值，如果提供了默认值。在下面的怎么还有的例子中，预览窗中 `TextView` 的内容会显示为 `PLACEHOLDER` 。

```xml
<TextView android:layout_width="wrap_content"
   android:layout_height="wrap_content"
   android:text="@{user.firstName, default=PLACEHOLDER}"/>
```

如果你要在设计阶段显示默认值，也可以使用 tools 属性，详情参考 [Designtime Layout Attributes](http://tools.android.com/tips/layout-designtime-attributes) 。



## 原文

https://developer.android.com/topic/libraries/data-binding/index.html