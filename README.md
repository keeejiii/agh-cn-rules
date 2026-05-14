# agh-cn-rules

自动生成 AdGuard Home `upstream_dns_file` 规则，将中国域名分流到国内 DNS。

## 做了什么

1. 下载 `cn.list` 和补充规则列表
2. 两个规则集去重合并
3. 输出为 AdGuard Home 可用的 `cn-rules.txt`
4. 支持手动触发生成

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

## 生成规则

生成文件 `converted/cn-rules.txt` 不纳入仓库提交。

本项目可能基于第三方来源生成规则，包括 GPL-3.0 许可的规则数据以及未明确许可的第三方列表。用户在再分发生成结果前，应自行审查并遵守上游许可证及条款。

详见 [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md)。

## 致谢

本项目使用或参考了以下项目和来源的规则、数据与实现思路：

- [DustinWin/ruleset_geodata](https://github.com/DustinWin/ruleset_geodata)  
 作为规则集/地理数据来源。以 GPL-3.0 许可。

- [Leev1s/FAK-DNS](https://github.com/Leev1s/FAK-DNS)  
 作为 AdGuard Home DNS 规则转换与路由逻辑的参考。  
 项目包含多许可证代码：上游代码使用 WTFPL，Leev1s 的修改和新增部分使用 MIT。

- NodeSeek `fastoo` 帖子：国内主流企业工信部 ICP 备案域名列表  
 作为中国 ICP 备案域名规则的额外参考/来源。  
 许可：未声明。  
 来源：https://www.nodeseek.com/post-464238-1

感谢以上项目、规则集和数据集的作者与维护者。

详细的第三方声明见 [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md)。

## License

WTFPL
