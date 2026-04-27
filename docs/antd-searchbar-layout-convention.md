<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->

# Ant Design Vue 搜索栏布局规约

> 日期：2026-03-05
> 背景：/jd/sync/loglist 搜索栏"查询/重置"按钮居右失败，`margin-left: auto` 在 `ant-form-inline` 中不生效。

---

## 一、按钮居右：正确做法

### ❌ 错误 — 在 `a-form-item` 上用 `margin-left: auto`

```html
<a-form layout="inline" class="search-form">
  <a-form-item label="字段A">...</a-form-item>
  <a-form-item label="字段B">...</a-form-item>
  <a-form-item class="search-btn-group">  <!-- margin-left: auto 不生效 -->
    <a-button>查询</a-button>
  </a-form-item>
</a-form>
```

```less
// ❌ 不可靠：ant-form-inline 内部 flex 渲染不一致，scoped 样式优先级不够
.search-form {
  display: flex;
  .search-btn-group { margin-left: auto; }
}
```

### ✅ 正确 — 拆分为两个独立 div

```html
<div class="search-bar">
  <!-- 左侧：筛选条件 -->
  <div class="search-filters">
    <a-form layout="inline">
      <a-form-item label="字段A">...</a-form-item>
      <a-form-item label="字段B">...</a-form-item>
    </a-form>
  </div>
  <!-- 右侧：操作按钮 -->
  <div class="search-actions">
    <a-button type="primary" icon="search" @click="doSearch">查询</a-button>
    <a-button style="margin-left: 8px;" icon="redo" @click="doReset">重置</a-button>
  </div>
</div>
```

```less
// ✅ 可靠：直接在外层容器用 flex，与 ant-form 内部渲染无关
.search-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;   // 左右两端对齐
  padding: 12px 16px;
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  margin-bottom: 12px;

  .search-filters {
    .ant-form-item {
      margin-bottom: 0;
      margin-right: 0;
    }
  }

  .search-actions {
    flex-shrink: 0;      // 防止按钮被压缩
    white-space: nowrap;
  }
}
```

---

## 二、根本原因

`<a-form layout="inline">` 在 Ant Design Vue 1.x 中渲染为 `<form class="ant-form ant-form-inline">`，它自身有 `display: flex; flex-wrap: wrap` 样式，并且优先级高于 Vue scoped 样式中对子元素的 flex 控制。因此在 `a-form-item` 层用 `margin-left: auto` 来推按钮居右是**不可靠**的。

**正确思路**：不要依赖 `a-form` 内部的 flex 布局做对齐，而是在外层 `div` 上建立独立的 flex 容器，将筛选区和按钮区完全分离。

---

## 三、`showTotal` 使用说明

本项目中分页条数显示由 Ant Design 默认控制，`showTotal` **不启用**：

```js
pagination: {
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  pageSizeOptions: ['10', '20', '50', '100'],
  // showTotal 不配置，使用默认样式
},
```

如需启用，格式为：

```js
showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条 / 共 ${total} 条`,
```

---

## 四、完整模板参考

参见 [`JdSyncLogList.vue`](file:///Users/youfanyu/Desktop/workspace/hnht/ecp-vue/src/views/jd/JdSyncLogList.vue) 的 `search-bar` 实现。

---

## 五、筛选项间距规范

`ant-form-inline` 及其子组件 `ant-form-item` 的内部 DOM 不带 Vue scoped 的 `data-v-xxx` 属性，导致间距样式始终无法生效。

### ❌ 方案一：直接写 `.ant-form-item`（无效）

```less
// scoped 会生成 .ant-form-item[data-v-xxx]，但组件内部 DOM 没有该属性
.search-filters {
  .ant-form-item { margin-right: 24px; }  // 不生效
}
```

### ❌ 方案二：用 `/deep/` 穿透（实测不稳定）

```less
// 理论上可以，但在部分 Vue 2 + Less 环境下仍然不生效
.search-filters {
  /deep/ .ant-form-item { margin-right: 40px; }  // 不可靠
}
```

### ✅ 方案三：放弃 `a-form`，改用原生 div（推荐）

彻底绕开 Ant Design 组件内部渲染，间距写在自己的 div 上，100% 可靠：

```html
<div class="search-filters">
  <div class="filter-item">
    <span class="filter-label">同步类型：</span>
    <a-select v-model="queryParams.syncType" ...></a-select>
  </div>
  <div class="filter-item">
    <span class="filter-label">同步模块：</span>
    <a-select v-model="queryParams.syncModule" ...></a-select>
  </div>
</div>
```

```less
.search-filters {
  display: flex;
  align-items: center;

  .filter-item {
    display: flex;
    align-items: center;
    margin-right: 32px;       // 完全受我们控制，必定生效

    .filter-label {
      white-space: nowrap;
      color: rgba(0, 0, 0, 0.65);
      font-size: 14px;
    }
  }
}
```

> **间距推荐值**：常规场景 `32px`，紧凑场景 `16px`。
