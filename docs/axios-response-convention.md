<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->

# 前后端接口响应结构规约

> 日期：2026-03-05
> 背景：/jd/sync/loglist 页面查询报错 `Cannot read properties of undefined (reading 'list')`，根因为后端返回结构与前端拦截器不一致。

---

## 一、拦截器规则（不可改动）

`ecp-vue/src/utils/request.js` 中所有 axios 实例的响应拦截器统一如下：

```js
service.interceptors.response.use(res => {
  const t = res.data        // HTTP 响应体
  if (t.success) {
    return t.data           // ← 只将 t.data 暴露给调用方
  } else {
    return Promise.reject(t)
  }
})
```

**结论**：前端 `.then(res => ...)` 中的 `res` 实际上是 `HTTP响应体.data`，而不是整个响应体。

---

## 二、后端必须遵守的返回结构

### ✅ 正确 — 分页列表

```json
{
  "success": true,
  "data": {
    "list": [...],
    "total": 100,
    "page": 1,
    "pageSize": 20
  }
}
```

前端正常访问：`res.list`、`res.total`

### ✅ 正确 — 单对象

```json
{
  "success": true,
  "data": { "id": 1, "name": "xxx" }
}
```

### ✅ 正确 — 操作类（触发同步等）

```json
{
  "success": true,
  "data": { "batchNo": "BATCH-20260305-001" }
}
```

### ❌ 错误 — 业务字段挂在顶层

```json
{
  "success": true,
  "list": [...],
  "total": 100
}
```

> 拦截器返回 `t.data = undefined`，前端访问 `res.list` 直接报错。

---

## 三、Java Controller 编写模板

```java
// 分页列表
JSONObject data = new JSONObject();
data.put("list", list);
data.put("total", total);
data.put("page", page);
data.put("pageSize", pageSize);

JSONObject result = new JSONObject();
result.put("success", true);
result.put("data", data);   // ← 必须套一层 data
return result;
```

```java
// 单对象
JSONObject result = new JSONObject();
result.put("success", true);
result.put("data", entity);
return result;
```

```java
// 操作类（触发、保存等）
JSONObject result = new JSONObject();
result.put("success", true);
result.put("data", new JSONObject().fluentPut("batchNo", batchNo));
return result;
```

---

## 四、排查 SOP

遇到前端报 `Cannot read properties of undefined` 或拿到 `undefined` 时：

1. 打开浏览器 **Network 面板**，找到对应接口
2. 查看响应 JSON，确认是否有 `"success": true`
3. 确认业务数据是否在 `"data"` 字段下
4. 若不满足 → 修改 **后端 Controller**，将返回值包装进 `data`
5. **不要修改拦截器**来绕过规范

---

## 五、两层结构速查表

| 层级 | 字段 | 作用 |
|------|------|------|
| 外层 | `success: true/false` | 供拦截器判断成功与否 |
| 外层 | `data: { ... }` | 拦截器提取后交给前端的实际数据 |
| 内层 | `list / total / id ...` | 前端 `res.xxx` 实际访问到的字段 |

---

## 六、涉及文件参考

| 文件 | 说明 |
|------|------|
| `ecp-vue/src/utils/request.js`（第 415–422 行） | 拦截器定义 |
| `product/infrastructure/.../jd/controller/JdSyncController.java` | 标准 Controller 示例 |
