<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->

# Spring Boot `@Value` 注解取值为空问题排查指南

在 Spring Boot 开发过程中，如果发现 `@Value` 注解无法正确读取配置文件中的属性值，并且总是返回空字符串（或 null），可以参考以下经验进行排查。

## 1. 问题现象

假设我们有一个配置类，期望通过 `@Value` 注入属性：

```java
public class JdApiConfig {
    @Value("${jd.api.username:}")
    private String username;
}
```

即使在 `application-dev.properties` 中已经配置了 `jd.api.username=admin`，但在应用启动后，`username` 的值依然为空字符串 `""`。

## 2. 根本原因排查步骤

### 第一步：确认实际生效的 Profile 环境

**这是导致类似问题最常见也是最容易被忽略的原因。**

很多时候我们在 `application-dev.properties` 中添加了配置，但应用实际启动时加载的并不是这个文件。
需要检查主配置文件 `application.properties` 或 `application.yml` 中的环境激活配置：

```properties
# application.properties
spring.profiles.active=dev-gs
```

**案例分析**：
在上述情况中，`spring.profiles.active` 被指定为了 `dev-gs`。这意味着 Spring Boot 在启动时去寻找并加载的是 `application-dev-gs.properties`，而不是开发者刚刚修改过的 `application-dev.properties`。因为对应的配置文件里没有 `jd.api.xxx` 相关的键值对，导致属性无法被读取到。

### 第二步：检查 `@Value` 的默认值语法规则

观察 `@Value("${jd.api.username:}")` 这段代码。
末尾的冒号 `:` 代表如果 Spring 容器中找不到 `jd.api.username` 这个键，就使用冒号后面的内容作为默认值。

由于冒号后面什么都没有（空字符串），当 Spring 找不到真正的配置项（比如因为读取了错的 profile 文件）时，它就不会报错，而是悄无声息地将变量赋值为了空字符串 `""`。这也是为什么没有抛出 `IllegalArgumentException: Could not resolve placeholder` 异常的原因。

### 第三步：检查属性键名是否拼写一致

确认 properties 文件里的键名和 `@Value` 中配置的占位符完全一致。
- 正确对应：`jd.api.username` <-> `@Value("${jd.api.username}")`
- 对于带有连字符的属性（如 `jd.api.base-url`），在直接使用 `@Value` 读取时，不能像 `@ConfigurationProperties` 那样享受自动驼峰转换（Relaxed Binding）的便利，必须**严格匹配**占位符中的字符串（即使用 `@Value("${jd.api.base-url}")`）。

## 3. 解决方案与总结

1. **核对 Profile**：在追加或修改配置前，全局搜索和确认 `spring.profiles.active` 或者打包/启动脚本中 `-Dspring.profiles.active` 的实际值，确保修改的是真正会被应用加载的那个配置文件（如 `application-dev-gs.properties` ）。
2. **正确书写配置**：将必要的配置块完整地追加到真实生效的 properties 文件中。
3. **慎用隐式空默认值**：如果某个配置是系统必须的，不要在 `@Value` 中加 `":"` 赋空默认值。如果在启动时缺少必须的配置直接报错退出，反而能更早地让你意识到“配置文件没读到”这个问题。例如强制改成 `@Value("${jd.api.username}")`，若读不到就会抛出明确的异常，帮助快速定位 Profile 加载错误。
