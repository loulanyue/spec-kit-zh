<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->

# 数据库建表与 MyBatis Mapper 规约

> 日期：2026-03-05

---

## 一、字段命名避免 SQL 保留字

数据库建表时，字段名禁止使用 SQL 保留字，否则在不同数据库方言下会导致语法错误。

**常见高风险保留字（禁止直接用作列名）：**

| 保留字 | 替代命名示例 |
|--------|------------|
| `year` | `sync_year`、`stat_year` |
| `month` | `sync_month`、`stat_month` |
| `rank` | `sort_rank`、`item_rank` |
| `order` | `sort_order` |
| `key` | `config_key`、`item_key` |
| `value` | `config_value`、`item_value` |
| `from` | `from_source`、`origin` |

> 判断标准：在 MySQL 中可用 `SELECT * FROM information_schema.KEYWORDS WHERE WORD = 'xxx'` 查询是否为保留字。

---

## 二、数据表必备字段规范

每张业务表必须包含以下字段：

```sql
`id`           varchar(32)  NOT NULL COMMENT '主键ID（UUID）',
`gmt_create`   varchar(25)  NOT NULL DEFAULT '' COMMENT '创建时间',
`gmt_modified` varchar(25)  NOT NULL DEFAULT '' COMMENT '修改时间',
PRIMARY KEY (`id`)
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `varchar(32)` | 唯一标识，存 UUID，由应用层生成 |
| `gmt_create` | `varchar(25)` | 记录创建时间，格式 `yyyy-MM-dd HH:mm:ss` |
| `gmt_modified` | `varchar(25)` | 记录最后修改时间，随每次 UPDATE 更新 |

> **为何用 `varchar(25)` 而非 `datetime`**：项目统一约定，便于跨时区展示和字符串直接比较排序。

---

## 三、MyBatis Mapper 接口必须使用 `@EcpMapper`

本项目使用自定义注解 `@EcpMapper` 替代标准的 `@Mapper`，Spring 容器只扫描 `@EcpMapper` 标注的接口。

### ❌ 错误 — 使用标准 `@Mapper`（Spring 无法发现该 Bean）

```java
@Mapper
public interface JdSyncLogMapper { ... }
```

### ✅ 正确 — 使用 `@EcpMapper`

```java
@EcpMapper(module = "jd", value = "mapper.jd.JdSyncLogMapper")
public interface JdSyncLogMapper { ... }
```

**参数说明：**

| 参数 | 含义 | 示例 |
|------|------|------|
| `module` | 所属业务模块（小写） | `"jd"`、`"product"` |
| `value` | Mapper 的完整限定路径，格式 `mapper.{module}.{ClassName}` | `"mapper.jd.JdSyncLogMapper"` |

> 详细规范参见 `/new-mapper` 工作流：`.agents/workflows/new-mapper.md`

---

## 四、KingBase（KingbaseES）表名大小写敏感问题

**现象**：MyBatis XML 中引用含大写字母的表名，KingBase 报错 `关系 "xxx" 不存在`，但表实际存在。

**根本原因**：KingBase 基于 PostgreSQL，**不加引号的标识符统一折叠为小写**。若表名含大写字母（如 ECP 历史业务表 `ECP_DMC_wupinqingdanweihu20240329112452`），不加引号会被折叠为全小写，导致找不到对应表。

**解决方案**：在 SQL 中用**双引号**包裹含大写字母的表名（MyBatis XML 里直接写 `"` 即可，无需转义）：

```xml
<!-- ❌ 错误：KingBase 折叠为小写，找不到表 -->
SELECT id FROM ECP_DMC_wupinqingdanweihu20240329112452 WHERE ...

<!-- ✅ 正确：双引号保持原始大小写 -->
SELECT id FROM "ECP_DMC_wupinqingdanweihu20240329112452" WHERE ...
```

> **适用范围**：SELECT / INSERT INTO / UPDATE / DELETE FROM 中的表名均须加引号。字段名通常全小写，不受影响。

---

## 五、对接无标准字段的 ECP 历史业务表

ECP 平台部分历史业务表**不含** `gmt_create` / `gmt_modified` 标准字段，且不允许改变表结构。对接时注意：

1. **SQL 层**：INSERT / UPDATE 语句中直接去掉这两列，不写入即可，不会报错。
2. **Service 层**：不生成时间字符串，不往 params Map 中放时间相关 key，保持代码干净。
3. **幂等 upsert 设计**：以业务唯一标识字段为查询条件，先 `SELECT id ... LIMIT 1`，有则 UPDATE，无则 INSERT，避免重复插入。

```java
// 标准 upsert 模式（不依赖 gmt_create/gmt_modified）
String existingId = ecpBusinessMapper.selectIdBySkuId(skuIdStr);
if (existingId == null) {
    params.put("id", UUID.randomUUID().toString().replace("-", ""));
    params.put("pkUuid", UUID.randomUUID().toString().replace("-", ""));
    ecpBusinessMapper.insertBusinessRecord(params);  // 新增
} else {
    ecpBusinessMapper.updateBusinessRecord(params);  // 更新
}
```
