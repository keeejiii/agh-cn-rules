import os
from pathlib import Path

CN_LIST_FILE = 'cn.list'
ADDITIONAL_LIST_FILE = 'cn-additional-list.txt'

HTML_LIKE_PREFIXES = (
    '<!doctype html',
    '<html',
    '<head',
    '<body',
    '<?xml',
)

MIN_RULE_COUNTS = {
    CN_LIST_FILE: 1000,
    ADDITIONAL_LIST_FILE: 1,
}


class ValidationError(RuntimeError):
    pass


def load_rules(rule_file, *, min_rules=0):
    exact_domains = set()
    suffix_domains = set()
    path = Path(rule_file)

    if not path.is_file():
        raise ValidationError(f'Rule file not found: {path}')

    content = path.read_text(encoding='utf-8')
    if not content.strip():
        raise ValidationError(f'Rule file is empty: {path}')

    lowered = content.lstrip().lower()
    if any(lowered.startswith(prefix) for prefix in HTML_LIKE_PREFIXES):
        raise ValidationError(f'Rule file looks like HTML, not a rules list: {path}')

    if lowered.startswith('404:') or lowered.startswith('not found'):
        raise ValidationError(f'Rule file looks like an error page: {path}')

    for raw_line in content.splitlines():
        rule = raw_line.strip()
        if not rule or rule.startswith('#'):
            continue
        if rule.startswith('+.'):
            suffix_domains.add(rule[2:])
        else:
            exact_domains.add(rule)

    total_rules = len(exact_domains) + len(suffix_domains)
    if total_rules < min_rules:
        raise ValidationError(
            f'Rule file has too few valid rules: {path} (got {total_rules}, need at least {min_rules})'
        )

    return exact_domains, suffix_domains


def merge_domains(cn_exact, cn_suffix, additional_exact, additional_suffix):
    """Merge cn.list domains with additional rules, deduplicating by domain name."""
    seen = set()
    domains = []
    has_cn_catchall = 'cn' in cn_suffix

    for domain in sorted(cn_exact | cn_suffix):
        if domain == 'cn':
            continue
        if domain not in seen:
            seen.add(domain)
            domains.append(domain)

    added_count = 0
    skipped_duplicate = 0
    for domain in sorted(additional_exact | additional_suffix):
        if domain in seen:
            skipped_duplicate += 1
            continue
        seen.add(domain)
        domains.append(domain)
        added_count += 1

    return domains, added_count, skipped_duplicate, has_cn_catchall


def write_output(output_file, domains, cn_dns, the_dns, has_cn_catchall):
    with open(output_file, 'w', encoding='utf-8') as file:
        if the_dns:
            file.write(the_dns.rstrip('\n') + '\n')

        if has_cn_catchall:
            file.write(f'[/cn/]{cn_dns}\n')

        for domain in domains:
            file.write(f'[/{domain}/]{cn_dns}\n')


def require_cn_dns():
    value = os.environ.get('CN_DNS')
    if value is None or not value.strip():
        raise ValidationError('CN_DNS is required and cannot be empty')
    return value.strip()


def main():
    current_directory = Path.cwd()
    converted_directory = current_directory / 'converted'
    converted_directory.mkdir(exist_ok=True)

    cn_dns = require_cn_dns()
    the_dns = os.environ.get('THE_DNS')

    cn_exact, cn_suffix = load_rules(
        current_directory / CN_LIST_FILE,
        min_rules=MIN_RULE_COUNTS[CN_LIST_FILE],
    )
    additional_exact, additional_suffix = load_rules(
        current_directory / ADDITIONAL_LIST_FILE,
        min_rules=MIN_RULE_COUNTS[ADDITIONAL_LIST_FILE],
    )

    merged_domains, added_count, skipped_duplicate, has_cn_catchall = merge_domains(
        cn_exact, cn_suffix, additional_exact, additional_suffix,
    )

    final_file = converted_directory / 'cn-rules.txt'
    write_output(final_file, merged_domains, cn_dns, the_dns, has_cn_catchall)

    if not final_file.is_file() or final_file.stat().st_size == 0:
        raise ValidationError(f'Generated file is empty: {final_file}')

    cn_total = len(cn_exact) + len(cn_suffix)
    additional_total = len(additional_exact) + len(additional_suffix)
    the_dns_lines = len(the_dns.rstrip('\n').splitlines()) if the_dns else 0
    catchall_lines = 1 if has_cn_catchall else 0
    output_lines = the_dns_lines + catchall_lines + len(merged_domains)

    print(
        f'CN rules: {cn_total}, '
        f'additional rules: {additional_total}, '
        f'additional skipped duplicates: {skipped_duplicate}, '
        f'additional added: {added_count}, '
        f'merged rules: {len(merged_domains)}, '
        f'output lines: {output_lines}'
    )


if __name__ == '__main__':
    main()
