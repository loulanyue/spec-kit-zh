<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->

# ECP 平台接口对接经验

> 日期：2026-03-18

---

## 一、PUT / DELETE 方法被 403 拦截

**现象**：前端调用 `PUT /api/xxx` 或 `DELETE /api/xxx` 时，后端报错「资源不可用」，HTTP 状态码 403，但接口本身逻辑正常、token 也有效。

**根本原因**：ECP 平台后端网关（`request.js` 中的 `doUrlCheckPOW`）对 `PUT` / `DELETE` 方法有**额外菜单权限校验**，未在平台权限系统注册的接口会被直接 403 拒绝。而 `POST` / `GET` 方法不受此机制约束。

**解决方案**：将 `PUT` / `DELETE` 接口改为 `POST`，路径加后缀区分语义：

```
# 原设计（会被 403）
PUT  /api/jd/sync/plan

# 修改后（正常访问）
POST /api/jd/sync/plan/update
```

> **规约**：在 ECP 平台新增"写操作"接口，**统一使用 POST 方法**，不使用 PUT / PATCH / DELETE，避免被平台网关拦截。

---

## 二、POST 请求 Body 被加密导致 `@RequestBody` 报 415

**现象**：`@RequestBody JSONObject` 接收 POST 请求时报 `Content type 'application/x-www-form-urlencoded' not supported`（415）。

**根本原因**：ECP 平台 `request.js` 的请求拦截器会对带有 `req.data`（body）的请求做 **AES 加密**，加密后 `Content-Type` 变为 `application/x-www-form-urlencoded`，后端 `@RequestBody` 期望 `application/json`，类型不匹配。

**解决方案**：将 `@RequestBody` 改为 `@RequestParam`：

```java
// ❌ 错误：body 会被加密，Content-Type 变为 form-urlencoded
@PostMapping("/sync/plan/update")
public JSONObject updateSyncPlan(@RequestBody JSONObject payload) { ... }

// ✅ 正确：使用 @RequestParam，接收 query string
@PostMapping("/sync/plan/update")
public JSONObject updateSyncPlan(
        @RequestParam(required = false) Boolean fullSyncEnabled,
        @RequestParam(required = false) Boolean priceSyncEnabled,
        @RequestParam(required = false) Boolean stockSyncEnabled) { ... }
```

---

## 三、axios.post Body 被加密导致参数丢失

**现象**：`axios.post(url, data)` 发送 `{key: false}` 的对象，后端 `@RequestParam` 始终收到 `null`，开关无法关闭。

**根本原因**：`axios.post(url, data)` 的第二个参数 `data` 放到 HTTP body 中，会被平台请求拦截器的 AES 加密模块处理，后端 `@RequestParam` 从 query string 中取不到值。

**解决方案**：简单参数通过 **URL query string** 传递，body 传 `null`：

```js
// ❌ 错误：参数放 body，被加密
axios.post(`/api/jd/sync/plan/update`, { fullSyncEnabled: false })

// ✅ 正确：参数放 URL query，不受加密干扰
axios.post(`/api/jd/sync/plan/update`, null, { params: { fullSyncEnabled: false } })
// 实际请求：POST /api/jd/sync/plan/update?fullSyncEnabled=false
```

> **规约**：ECP 平台中，简单参数（开关、ID 等基本类型）统一使用 `params`（query string）传递。只有复杂对象需要 body 时，确认加密拦截器是否影响。

---

## 四、Vue 2 `a-switch` 开关状态不更新

**现象**：`a-switch :checked="plan.enabled"` 点击后，Switch 状态不随后端返回值变化（始终卡在开启）。

**根本原因**：
1. `:checked` 是单向绑定，依赖响应式数据变更
2. `Object.assign({}, obj, res)` 替换了整个对象引用，Vue 2 检测不到嵌套属性变化

**解决方案**：乐观更新 + 重新拉取 + 失败回滚：

```js
updatePlan(field, checked) {
  // 1. 乐观更新：先改本地，让 Switch 立即响应
  const oldVal = this.syncPlan[field]
  this.$set(this.syncPlan, field, checked)  // ✅ 用 $set 确保响应式

  // 2. 调接口
  updateApi({ [field]: checked }).then(() => {
    return this.loadPlan()  // 成功后重新拉取
  }).catch(err => {
    this.$set(this.syncPlan, field, oldVal)  // 3. 失败回滚
  })
}
```

> **关键点**：Vue 2 中修改对象属性必须用 `this.$set(obj, key, value)`，不能直接赋值或用 `Object.assign` 替换整个对象。

---

## 五、京东 VOP API 对接规约

### 5.1 `getNewStockById` 参数格式

| 参数 | 类型 | 说明 |
|------|------|------|
| `token` | String | 必填，access_token |
| `skuNums` | String | 必填，格式：`[{"skuId":569172,"num":1}]`，最多 100 条 |
| `area` | String | 必填，格式：`省_市_县_镇`，如 `13_1000_4277_0` |

**配置项**（`application-*.properties`）：

```properties
jd.api.defaultProvince=13
jd.api.defaultCity=1000
jd.api.defaultCounty=4277
jd.api.defaultTown=0    # 可省略，默认填 0
```

**常见报错**：

| 报错现象 | 原因 | 解决 |
|----------|------|------|
| 京东返回参数错误 | `area` 某级地址未配置，拼出 `13__4277_` | 补全配置项，town 未配置时自动填 `0` |
| `result` 解析报 NPE | 库存接口 `result` 字段是 **JSON 字符串**，需二次解析 | `JSONArray.parseArray(result.getString("result"))` |

**`skuNums` 正确构造方式**（Java）：

```java
// ✅ 手动拼接，格式明确
StringBuilder sb = new StringBuilder("[");
for (int i = 0; i < skuIds.size(); i++) {
    if (i > 0) sb.append(",");
    sb.append("{\"skuId\":").append(skuIds.get(i)).append(",\"num\":1}");
}
sb.append("]");
String skuNums = sb.toString();
// 结果: [{"skuId":569172,"num":1},{"skuId":202551,"num":1}]
```

### 5.2 `area` 参数与库存返回值关系

| `num` 传值 | `remainNum` 返回 |
|-----------|----------------|
| < 50 | 真实剩余库存 |
| 50 ≤ num < 100 | 返回 -1（不显示真实库存） |
| > 100 | 返回 num 本身（非真实库存） |

> **建议**：`num` 统一传 `1`，可获取到真实库存值。

### 5.3 响应示例

```json
{
  "success": true,
  "resultMessage": "",
  "resultCode": "0000",
  "result": "[{\"skuId\":202551,\"areaId\":\"13_1032_1033_0\",\"stockStateId\":33,\"stockStateDesc\":\"有货\",\"remainNum\":21}]"
}
```

> `result` 是 JSON 字符串（非 JSON 对象），使用前必须 `JSON.parse()` / `JSONArray.parseArray()`。
