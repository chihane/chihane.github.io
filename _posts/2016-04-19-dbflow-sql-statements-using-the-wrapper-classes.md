---

layout: post

title: 【译】DBFlow - 使用 SQL 语句包装器

date: 2016-04-19 23:44:00 +0800

categories: Translation

tags: [database, android, orm, translation, tutorial]

---

用 Android 自带的数据库写 SQL 语句`一点也不好玩`，所以为了简化使用，本库就提供了一系列 SQLite 语句的包装器，让 java 代码尽量接近 SQLite。

我在第一节中描述了如何使用包装器类来大大简化代码编写。

## 示例

假设我们想从`Ant`中找出所有雌性『工蚁』，SQL 语句很好写：

```sql
SELECT * FROM Ant where type = 'worker' AND isMale = 0;
```

我们用 Android 代码来把 SQL 数据转换成可用信息：

```java
String[] args = new String[2];
args[0] = "worker";
args[1] = "0";
Cursor cursor = db.rawQuery("SELECT * FROM Ant where type = ? AND isMale = ?", args);
final List<Ant> ants = new ArrayList<Ant>();
Ant ant;

if (cursor.moveToFirst()) {
  do {
    // 取出每列的数据并分别设置好
    ant = new Ant();
    ant.setId(cursor.getLong(cursor.getColumnIndex("id")));
    ant.setType(cursor.getString(cursor.getColumnIndex("type")));
    ant.setIsMale(cursor.getInt(cursor.getColumnIndex("isMale") == 1);
    ant.setQueenId(cursor.getLong(cursor.getColumnIndex("queen_id")));
    ants.add(ant);
  }
  while (cursor.moveToNext());
}
```

简单的查询这么写算是轻松加愉快，但是为什么还要写这些语句呢？

如果：

1. 要添加或者删除列
2. 要给其他的表，查询或者其他类型的数据写更多这种功能呢？

简单来说，我们希望代码可以易于维护、短小精炼、可以复用，而且始终清晰易懂。在本库中，这次查询就可以变得非常简单：

```java
// 主线程检索
List<Ant> devices = SQLite.select().from(Ant.class)
  .where(Ant_Table.type.eq("worker"))
  .and(Ant_Table.isMale.eq(false)).queryList();

// 异步事务队列检索（建议在大型查询中使用）
  SQLite.select()
  .from(DeviceObject.class)
  .where(Ant_Table.type.eq("worker"))
  .and(Ant_Table.isMale.eq(false))
  .async().queryList(transactionListener);
```

DBFlow 支持许多种查询，包括：

1. SELECT
2. UPDATE
3. INSERT
4. DELETE
5. JOIN

## SELECT 语句与检索方法

`SELECT`语句可以从数据库中检索数据。我们可以通过以下方法检索数据：

1. 在主线程使用普通的`Select`方式
2. 使用`TransactionManager`执行`Transaction`（建议在大型查询中使用）。

```java
// 查询列表
SQLite.select().from(SomeTable.class).queryList();
SQLite.select().from(SomeTable.class).where(conditions).queryList();

// 查询单个模型
SQLite.select().from(SomeTable.class).querySingle();
SQLite.select().from(SomeTable.class).where(conditions).querySingle();

// 查询表列表和游标列表
SQLite.select().from(SomeTable.class).where(conditions).queryTableList();
SQLite.select().from(SomeTable.class).where(conditions).queryCursorList();

// 向 ModelContainer 中读取数据！
SQLite.select().from(SomeTable.class).where(conditions).queryModelContainer(new MapModelContainer<>(SomeTable.class));

// SELECT 方法
SQLite.select().distinct().from(table).queryList();
SQLite.select().from(table).queryList();
SQLite.select(Method.avg(SomeTable_Table.salary))
  .from(SomeTable.class).queryList();
SQLite.select(Method.max(SomeTable_Table.salary))
  .from(SomeTable.class).queryList();

// 使用 DBTransactionQueue 处理请求
TransactionManager.getInstance().addTransaction(
  new SelectListTransaction<>(new Select().from(SomeTable.class).where(conditions),
  new TransactionListenerAdapter<List<SomeTable>>() {
    @Override
    public void onResultReceived(List<SomeTable> someObjectList) {
      // 在这里检索
});

// 使用查询列数的 SELECT 语句
long count = SQLite.selectCountOf()
  .where(conditions).count();
```

### Order By

```java
// true 代表 'ASC'，false 代表 'DESC'
SQLite.select()
  .from(table)
  .where()
  .orderBy(Customer_Table.customer_id, true)
  .queryList();

  SQLite.select()
    .from(table)
    .where()
    .orderBy(Customer_Table.customer_id, true)
    .orderBy(Customer_Table.name, false)
    .queryList();
```

### Group By

```java
SQLite.select()
  .from(table)
  .groupBy(Customer_Table.customer_id, Customer_Table.customer_name)
  .queryList();
```

### Having

```java
SQLite.select()
  .from(table)
  .groupBy(Customer_Table.customer_id, Customer_Table.customer_name))
  .having(Customer_Table.customer_id.greaterThan(2))
  .queryList();
```

### LIMIT + OFFSET

```java
SQLite.select()
  .from(table)
  .limit(3)
  .offset(2)
  .queryList();
```

## UPDATE 语句

有两种方法更新数据库中的数据：

1. 调用`SQLite.update()`或者使用`Update`类
2. 使用`TransactionManager`执行`Transaction`（要求线程安全时建议使用，不过观察修改还是异步的）。

本节中我们来描述批量更新数据的方法。

还是用之前蚂蚁的例子，我们现在想把所有雄性『工蚁』都改成『其他』蚂蚁，因为它们都懒成狗不干活了。

使用原生 SQL 语句：

```sql
UPDATE Ant SET type = 'other' WHERE male = 1 AND type = 'worker';
```

使用 DBFlow：

```java
// 原生 SQL 包装器
Where<Ant> update = SQLite.update(Ant.class)
  .set(Ant_Table.type.eq("other"))
  .where(Ant_Table.type.is("worker"))
    .and(Ant_Table.isMale.is(true));
update.queryClose();

// TransactionManager（其他方法也与此类似）
TransactionManager.getInstance().addTransaction(new QueryTransaction(DBTransactionInfo.create(BaseTransaction.PRIORITY_UI), update);
```

## DELETE 语句

```java
// 删除整张表
Delete.table(MyTable.class, conditions);

// 删除多张表
Delete.tables(MyTable1.class, MyTable2.class);

// 使用查询方式删除
SQLite.delete(MyTable.class)
  .where(DeviceObject_Table.carrier.is("T-MOBILE"))
    .and(DeviceObject_Table.device.is("Samsung-Galaxy-S5"))
  .query();
```

## JOIN 语句

作为参考，请看（[JOIN examples](http://www.tutorialspoint.com/sqlite/sqlite_using_joins.htm)）。

`JOIN`语句非常适合用于组合多对多的关系。如果你的查询返回了非表中数据，而且没法映射到已有对象，请参考[query models](https://github.com/Raizlabs/DBFlow/blob/master/usage/usage/QueryModels.md)

假设我们有一张表叫做`Customer`，还有一张叫`Reservations`。

```sql
SELECT FROM `Customer` AS `C` INNER JOIN `Reservations` AS `R` ON `C`.`customerId`=`R`.`customerId`
```

```java
// 如果结果没法适用到已有的 Model 类，则改用不同的 QueryModel（来代替 Table）。
List<CustomTable> customers = new Select()   
  .from(Customer.class).as("C")   
  .join(Reservations.class, JoinType.INNER).as("R")    
  .on(Customer_Table.customerId
      .withTable(new NameAlias("C"))
    .eq(Reservations_Table.customerId.withTable("R"))
    .queryCustomList(CustomTable.class);
```

`IProperty.withTable()`方法会把`NameAlias`或者`Table`的别名预设给查询中的`IProperty`，给 JOIN 查询提供方便：

```sql
SELECT EMP_ID, NAME, DEPT FROM COMPANY LEFT OUTER JOIN DEPARTMENT
      ON COMPANY.ID = DEPARTMENT.EMP_ID
```

用 DBFlow的话：

```java
SQLite.select(Company_Table.EMP_ID, Company_Table.DEPT)
  .from(Company.class)
  .leftOuterJoin(Department.class)
  .on(Company_Table.ID.withTable().eq(Department_Table.EMP_ID.withTable()))
  .queryList();
```

