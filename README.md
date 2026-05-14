# AdGuard Home China DNS Rules

[![Generate DNS Rules](https://github.com/keeejiii/agh-cn-rules/actions/workflows/update-rules.yml/badge.svg)](https://github.com/keeejiii/agh-cn-rules/actions/workflows/update-rules.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)

用于 AdGuard Home `upstream_dns_file` 的中国域名分流规则集。

默认通过 **GitHub Releases latest** 提供可直接使用的 `cn-rules.txt`：

- 国内 DNS：阿里 DNS（HTTP/3 + QUIC）+ 腾讯 DNSPod DoH
- 国外/默认 DNS：Cloudflare DoH + Google DoH
- 每天北京时间 **06:15** 左右自动更新

当前 latest release 使用的上游如下：

- `CN_DNS`: `h3://dns.alidns.com/dns-query quic://dns.alidns.com https://doh.pub/dns-query`
- `THE_DNS`:
  - `https://cloudflare-dns.com/dns-query`
  - `https://dns.google/dns-query`

## 直接使用

### 1. 下载规则文件

```bash
mkdir -p /opt/AdGuardHome
curl -L https://github.com/keeejiii/agh-cn-rules/releases/latest/download/cn-rules.txt -o /opt/AdGuardHome/cn-rules.txt
```

直链：<https://github.com/keeejiii/agh-cn-rules/releases/latest/download/cn-rules.txt>

### 2. 配置定时拉取（cron 示例）

```bash

cat >/usr/local/bin/update-agh-cn-rules.sh <<'EOF'
#!/bin/sh
curl -L https://github.com/keeejiii/agh-cn-rules/releases/latest/download/cn-rules.txt -o /tmp/cn-rules.txt.new || exit 1
cmp -s /tmp/cn-rules.txt.new /opt/AdGuardHome/cn-rules.txt && rm -f /tmp/cn-rules.txt.new && exit 0
mv /tmp/cn-rules.txt.new /opt/AdGuardHome/cn-rules.txt
systemctl restart AdGuardHome
EOF
chmod +x /usr/local/bin/update-agh-cn-rules.sh
(crontab -l 2>/dev/null; echo '30 6 * * * /usr/local/bin/update-agh-cn-rules.sh >/dev/null 2>&1') | crontab -
```

- 每天 06:30 自动拉取
- 文件没变：不重启
- 文件变了：覆盖并重启 AdGuard Home

### 3. 修改 AdGuard Home 配置

在 `AdGuardHome.yaml` 里加上：

```yaml
dns:
  upstream_dns_file: /opt/AdGuardHome/cn-rules.txt
```

> 说明：核心是让 AdGuard Home 最终从 `AdGuardHome.yaml` 读取到这份文件。

### 4. 首次手动重启一次

```bash
systemctl restart AdGuardHome
```

## 自定义生成

如果你想换成自己的国内 DNS / 默认 DNS，可以 fork 本仓库后用 GitHub Actions 生成。

### 添加变量

仓库页面进入：

**Settings → Secrets and variables → Actions → Variables**

新增这两个变量（都可选，不填就用默认值）：

| 变量名 | 作用 | 示例值 |
|------|------|------|
| `CN_DNS` | 中国域名命中后使用的 DNS 上游 | `https://dns.alidns.com/dns-query` |
| `THE_DNS` | 默认 DNS 上游，写在规则文件第一行 | `https://cloudflare-dns.com/dns-query` |

### 手动触发生成

仓库页面进入：

**Actions → Generate DNS Rules → Run workflow**

工作流会自动：

1. 下载 `cn.list`
2. 下载 `cn-additional-list.txt`
3. 去重合并
4. 生成 `cn-rules.txt`
5. 仅在规则变化时更新 **latest Release**

## 规则逻辑

输出文件格式示例：

```text
https://cloudflare-dns.com/dns-query
https://dns.google/dns-query
[/cn/]h3://dns.alidns.com/dns-query quic://dns.alidns.com https://doh.pub/dns-query
[/example.com/]h3://dns.alidns.com/dns-query quic://dns.alidns.com https://doh.pub/dns-query
```

含义：

- 前两行是默认 DNS（`THE_DNS`），这里用的是 Cloudflare DoH 和 Google DoH
- `[/cn/]` 作为 `.cn` 兜底规则，这里用的是阿里 DNS（HTTP/3 + QUIC）和 DNSPod DoH
- 其余中国域名逐条写入分流规则
- 已存在 `[/cn/]` 时，不再重复写入 `.cn` 子域名规则

## 规则来源

- `cn.list`  
  <https://github.com/DustinWin/ruleset_geodata/releases/download/mihomo-ruleset/cn.list>
- `cn-additional-list.txt`  
  <https://static-file-global.353355.xyz/rules/cn-additional-list.txt>

## 第三方声明

本项目代码采用 MIT License。

规则生成涉及第三方规则数据以及不同许可证来源。重新分发前，请自行审查上游许可证与使用条件。

详见 [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md)。

## 致谢

- [DustinWin/ruleset_geodata](https://github.com/DustinWin/ruleset_geodata)
- [Leev1s/FAK-DNS](https://github.com/Leev1s/FAK-DNS)
- [NodeSeek 用户 `fastoo` 分享的 ICP 备案域名列表](https://www.nodeseek.com/post-464238-1)
