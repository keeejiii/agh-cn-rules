# agh-cn-rules

自动生成 AdGuard Home `upstream_dns_file` 规则，将中国域名分流到国内 DNS。

## 做了什么

1. 下载 `cn.list` 和补充规则列表
2. 两个规则集去重合并
3. 输出为 AdGuard Home 可用的 `cn-rules.txt`
4. 每天 UTC 22:00（北京时间次日 06:00）定时自动更新

## 规则来源

- `cn.list`  
  https://github.com/DustinWin/ruleset_geodata/releases/download/mihomo-ruleset/cn.list
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

- 从 `cn.list` 和补充规则列表中提取域名
- 两个规则集去重后合并
- 输出为 AdGuard Home 分流规则格式：`[/domain/]DNS_SERVER`
- 输出文件第一行可包含默认 DNS（`THE_DNS`），其余域名命中后使用 `CN_DNS`

## 配置

在仓库 **Settings → Secrets and variables → Actions → Variables** 中设置：

| 变量 | 说明 | 必填 |
|------|------|------|
| `CN_DNS` | 中国域名使用的 DNS 上游 | 可选（默认阿里 DoH） |
| `THE_DNS` | 默认 DNS 上游（写在整个文件第一行） | 可选（默认 Cloudflare DoH） |

如果不设置，默认使用：
- `CN_DNS`: `https://dns.alidns.com/dns-query`
- `THE_DNS`: `https://cloudflare-dns.com/dns-query`

## AdGuard Home 配置

将生成的 `converted/cn-rules.txt` 放到本机，在 `AdGuardHome.yaml` 中配置：

```yaml
dns:
  upstream_dns_file: /opt/AdGuardHome/cn-rules.txt
```

## 加固说明

- 下载使用 `curl --fail --location --retry`，抵抗临时网络波动
- 输入校验：文件必须存在、非空、非 HTML/错误页、规则数不低于阈值
- `CN_DNS` 必填校验，避免生成残缺结果
- GitHub Actions Summary 输出转换统计，方便巡检

## License

WTFPL
