# FAK-DNS for AdGuard Home

自动生成 AdGuard Home `upstream_dns_file` 规则，将中国域名分流到国内 DNS。

## 做了什么

1. 下载 `cn.list`、`google-cn.list`、`microsoft@cn.list`、补充规则列表
2. 从 `cn.list` 中剔除与 Google / Microsoft 中国直连规则重叠的域名
3. 合并补充规则
4. 输出为 AdGuard Home 可用的 `FAK-DNS.txt`
5. 每天 UTC 22:00（北京时间次日 06:00）定时自动更新

## 规则来源

- `cn.list`  
  https://github.com/DustinWin/ruleset_geodata/releases/download/mihomo-ruleset/cn.list
- `google-cn.list`  
  https://github.com/DustinWin/ruleset_geodata/releases/download/mihomo-ruleset/google-cn.list
- `microsoft@cn.list`  
  https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/refs/heads/meta/geo/geosite/microsoft@cn.list
- 补充规则  
  https://static-file-global.353355.xyz/rules/cn-additional-list.txt

## 规则格式

```text
# 精确匹配
example.com
# 后缀匹配
+.example.com
```

## 处理逻辑

- 从 `cn.list` 中移除与 Google / Microsoft 中国直连规则重叠的域名
- 合并补充规则（去重）
- 输出为 AdGuard Home 分流规则格式：`[/domain/]DNS_SERVER`
- 输出文件第一行可包含默认 DNS（`THE_DNS`），其余域名命中后使用 `CN_DNS`

## 配置

在仓库 **Settings → Secrets and variables → Actions → Variables** 中设置：

| 变量 | 说明 | 必填 |
|------|------|------|
| `CN_DNS` | 中国域名使用的 DNS 上游 | ✅ 必填 |
| `THE_DNS` | 默认 DNS 上游（写在整个文件第一行） | 可选 |

示例：
```
CN_DNS: h3://dns.alidns.com/dns-query
THE_DNS: https://cloudflare-dns.com/dns-query
```

## AdGuard Home 配置

将生成的 `converted/FAK-DNS.txt` 放到本机，在 `AdGuardHome.yaml` 中配置：

```yaml
dns:
  upstream_dns_file: /opt/AdGuardHome/FAK-DNS.txt
```

## 加固说明

- 下载使用 `curl --fail --location --retry`，抵抗临时网络波动
- 输入校验：文件必须存在、非空、非 HTML/错误页、规则数不低于阈值
- `CN_DNS` 必填校验，避免生成残缺结果
- GitHub Actions Summary 输出转换统计，方便巡检

## License

WTFPL
