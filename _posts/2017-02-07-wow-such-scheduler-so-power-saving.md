---
layout: post

title: 震惊！他竟然为了这个功能放弃了 5.0 以下的用户！

date: 2017-02-07 17:26

categories: Tutorial

tags: [jobscheduler, android, lollipop]


---

JobScheduler 是一个新特性，用于实现周期性或定时运行的，且对具体运行时间点要求不高的后台任务，仅兼容 API level 21 以上。

JobScheduler 提供的功能其实在以往的系统上完全可以通过广播加服务的方式实现，但它的可贵之处有二：

- 节能 - 在于通过 JobScheduler 计划的任务会经过系统调度，以类似某些 ROM 中对齐唤醒的机制，把数个时间点相近的任务打包在一起执行，创造休眠窗口，避免了系统被不断唤醒。
- 易用 - 在于它 API 简单易用，一声明一计划即可。且原生提供了网络状况、是否充电、是否闲置等数个条件的限制，节约了手动实现的工作。

对于诸如每周清理缓存、手机闲置一分钟后清理后台应用、添加了新联系人时同步到服务器之类定时或者周期运行，而且早一点晚一点都不要紧的后台工作，实现起来可是轻松极了。

## 1. 实现 JobService

第一步，决定任务被触发时要做什么。
首先继承 `JobService` 类，有两个抽象方法必须实现：

``` java
@Override
public boolean onStartJob(JobParameters params) {
    return false;
}

@Override
public boolean onStopJob(JobParameters params) {
    return false;
}
```

`params` 参数中保存着任务 ID 和配置任务时携带的额外信息，用于区分不同的任务。

### 1.1. onStartJob()

任务启动时被调用，在这时执行具体任务内容。方法返回值分两种情况：

- `false` - 表示任务在方法返回时就已经同步地执行完了
- `true` - 表示方法返回时还有异步的任务没有执行完毕，执行完时需要手动调用 `jobFinished(JobParameters, boolean)` 方法

jobFinished 方法的第二个参数指是否需要重新把这个任务加入计划中，可以理解为任务执行失败了，值为 `true` 时会启动任务重试，具体重试机制在下文详述。

需要注意的是这个方法是在应用的主线程执行的，因此平时开发时需要注意的问题在这里也适用。

### 1.2. onStopJob()

任务执行完毕，被取消或者没有满足运行条件而被放弃时调用，在这个方法内做收尾善后工作。方法返回值同样分为两种情况：

- `false` - 彻底放弃这个任务
- `true` - 重新计划这次任务，启动重试机制

不管返回值如何，这个方法被调用的时候都应该停止目前正在执行的工作。

### 1.3. 举个例子

``` java
private boolean stillRunning;

@Override
public boolean onStartJob(final JobParameters params) {
    new Thread(() -> {
        PersistableBundle bundle = params.getExtras();
        int userId = bundle.getInt(KEY_PARAM_USER_ID);

        stillRunning = true;
        while (stillRunning) {
            sendSpam(userId);
        }
    }).start();
    return true;
}

@Override
public boolean onStopJob(JobParameters params) {
    stillRunning = false;
    return false;
}
```

JobService 写完后在清单文件中注册，声明 `android.permission.BIND_JOB_SERVICE` 权限即可。

``` xml
<service
            android:name=".service.MyJobService"
            android:permission="android.permission.BIND_JOB_SERVICE"
            android:exported="true"/>
```

## 2. JobInfo.Builder

决定好了任务怎样执行，接下来该决定任务何时执行了。JobScheduler 使用 `JobInfo` 类来描述任务触发的种种条件， JobInfo 实例使用建造者模式来初始化。

### 2.1. 条件限制

需要注意的是以下条件都是严格限制的，如果条件一直没有被满足，任务就一直不会执行。如果希望即使条件没有满足也在某个时间点执行任务，则需要配合下文中的超时强制执行功能使用。

- ```setRequiredNetworkType(int)```
  网络类型限制，可选项有四个：
  + `NETWORK_TYPE_NONE`：缺省值。对联网状态没有要求，离线也可以。
  + `NETWORK_TYPE_ANY`：只要联网就可以。
  + `NETWORK_TYPE_UNMETERED`：要求非付费网络，『非付费』的定义和系统里那个一样难以捉摸。
  + `NETWORK_TYPE_NOT_ROAMING`：要求非漫游网络。
- ```setRequiresCharging(boolean)```
  要求正在充电，默认关闭。
- ```setRequiresDeviceIdle(boolean)```
  要求设备正在闲置状态，默认关闭。根据文档说明，这里的『闲置状态』是个宽泛的概念，指手机一段时间没有被使用后进入的状态。

### 2.2. 触发条件

以下触发条件只能粗略限制执行时机，实际执行的时间点还是要依靠系统调度的，并不能保证条件满足了就会立刻执行。

- ```addTriggerContentUri(TriggerContentUri)```
  使用 `ContentObserver` 监听指定 URI，URI 内容发生变动时触发任务。设备重启后失效。
  因为一个任务只监听一次变动，如果想监听到所有变动，则需要在处理任务并返回方法之前重新计划一个监听任务。
- ```setTriggerContentUpdateDelay(long)```
  在监听的 URI 发生变动之后延迟一段时间才执行任务。如果在延迟时间内有新的变动发生了，就抛弃当前等待的变动，对新的变动重新开始计时，只针对最近的一次变动执行计划任务。
- ```setTriggerContentMaxDelay(long)```
  设置单次变动等待超时。在监听的 URI 发生变动后最多等待指定的时间，如果系统一直没有调度到这次变动的任务，就在超时时强制执行。
- ```setPeriodic(long interval)```
  循环执行任务。但是只保证在指定 `interval` 内只执行一次，具体在这个时间段内的哪个时间点执行就不知道了。所以前一次任务到最后才执行，而后一次任务一开始就执行了，结果相当于连续执行了两次任务也是有可能的。并不能当定时器使用。
  间隔时间最短为十五分钟，也可以设置为更短，但执行时会被强制限制到十五分钟。
  和 URI 监听功能一起使用没有意义，同时设置的话会抛出异常。
- ```setPeriodic(long interval, long flexMillis)```
  同上，循环执行任务，区别在于可以把任务执行的时间范围限制在指定时间段内的倒数 `flexMillis` 毫秒里。相比起上面的方法，可以做到更接近定时器的效果。
  但 `flexMillis` 也是有最短限制的，第一不能小于五分钟，第二不能小于 `interval` 的 5%。所以 `setPeriodic(30 * 60 * 1000, 0)` 这种诡计用法就不要想了。
- ```setMinimumLatency(long)```
  设置最小延时，满足条件后等待指定时间才执行任务。
  由于循环任务本来就没有具体的执行时间点，设置延时也没有意义，所以不能和 `setPeriodic` 方法同时使用。
- ```setOverrideDeadline(long)```
  设置等待超时，超时后即使任何条件都没满足也会执行任务。同样无法与 `setPeriodic` 方法同时使用。

### 2.3. 其他设置

- ```setBackoffCriteria(long initialBackoffMillis, int backoffPolicy)```
  设置任务执行失败时的重试策略。`backoffPolicy` 有两种选项可用，设置为 `BACKOFF_POLICY_LINEAR` 时每次重试的间隔相同，设置为 `BACKOFF_POLICY_EXPONENTIAL` 时每次重试的间隔都是上一次的两倍。默认情况下两个值分别是 30 秒和 Exponential。
  和 `setRequiresDeviceIdle` 同时使用的话，调用的时机会冲突，因此也是不能同时设置的。
- ```setExtras(PersistableBundle)```
  与 `Intent` 中的 extras 类似，用于携带额外信息。里面的内容会被存储在硬盘上，所以只允许携带基本类型。
- ```setPersisted(boolean)```
  在关机时把任务保存在硬盘上，重启后可以继续执行计划。默认情况下重启后服务是运行不起来的。
  但由于 Android 系统的限制，重启后继续 URI 监听是做不到的，同时设置的话会抛异常。
  另外需要在配置文件里加上 `RECEIVE_BOOT_COMPLETED` 权限，不然也会抛异常。

### 2.4. 当然，

完全没有限制是绝对不可以的，源码里的注释激烈地吐槽了这一点：

> // Allow jobs with no constraints - What am I, a database?

『你拿我当什么了？』

## 3. 一切准备停当

最后使用 `Context.getSystemService(Context.JOB_SCHEDULER_SERVICE)` 拿到 `JobScheduler` 实例，调用它的 `schedule(JobInfo)` 方法，就可以安静等待任务被执行了。