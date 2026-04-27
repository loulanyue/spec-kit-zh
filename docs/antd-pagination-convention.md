<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->

# Ant Design Vue 列表分页配置规约

> 日期：2026-03-05
> 背景：/jd/sync/loglist 列表分页功能不完善，缺少每页条数切换、快速跳页及筛选联动。

---

## 一、完整分页配置模板

使用 `<a-table>` 时，`pagination` 对象应包含以下字段：

```js
pagination: {
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,                          // 显示每页条数切换
  showQuickJumper: true,                          // 显示快速跳页输入框
  pageSizeOptions: ['10', '20', '50', '100'],     // 可选每页条数
  showTotal: (total, range) =>
    `第 ${range[0]}-${range[1]} 条 / 共 ${total} 条`,
},
```

**明细/子表（数据量较大）** 推荐：

```js
detailPagination: {
  current: 1,
  pageSize: 50,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  pageSizeOptions: ['20', '50', '100', '200'],
  showTotal: (total, range) =>
    `第 ${range[0]}-${range[1]} 条 / 共 ${total} 条`,
},
```

---

## 二、筛选项必须与分页联动

筛选下拉选框的 `@change` 应绑定查询方法，切换条件时**自动重置到第 1 页**并刷新数据：

```html
<!-- ✅ 正确 -->
<a-select v-model="queryParams.syncType" @change="doSearch">...</a-select>

<!-- ❌ 错误：无 @change，用户切换条件后需手动点查询 -->
<a-select v-model="queryParams.syncType">...</a-select>
```

`doSearch` 方法中必须重置页码：

```js
doSearch() {
  this.pagination.current = 1   // ← 回第 1 页
  this.loadData()
},
```

---

## 三、表格分页事件处理

`<a-table>` 的 `@change` 会在翻页/切换每页条数时触发，需同步回 `pagination` 对象：

```js
handleTableChange(pag) {
  this.pagination.current = pag.current
  this.pagination.pageSize = pag.pageSize   // 同步 pageSize，否则切换后下次请求仍是旧值
  this.loadData()
},
```

---

## 四、反模式对照

| 问题 | 原因 | 解决方式 |
|------|------|------|
| 没有每页条数切换 | `showSizeChanger` 未配置 | 加 `showSizeChanger: true` + `pageSizeOptions` |
| 无法快速跳页 | `showQuickJumper` 未配置 | 加 `showQuickJumper: true` |
| 底部只显示"共 N 条" | `showTotal` 无范围信息 | 使用 `(total, range) => \`第 ${range[0]}-${range[1]} 条 / 共 ${total} 条\`` |
| 切换筛选条件后数据不刷新 | 筛选 select 未绑 `@change` | 每个筛选项加 `@change="doSearch"` |
| 切换每页条数后数量不对 | `handleTableChange` 未同步 `pageSize` | 补 `this.pagination.pageSize = pag.pageSize` |
