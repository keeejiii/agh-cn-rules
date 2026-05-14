import os
from pathlib import Path

CN_LIST_FILE = 'cn.list'
GOOGLE_CN_LIST_FILE = 'google-cn.list'
MICROSOFT_CN_LIST_FILE = 'microsoft-cn.list'
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
    GOOGLE_CN_LIST_FILE: 10,
    MICROSOFT_CN_LIST_FILE: 10,
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


def suffix_matches_domain(suffix_domain, domain):
    return domain == suffix_domain or domain.endswith(f'.{suffix_domain}')


def rules_overlap(rule, other_rule):
    rule_type, domain = rule
    other_type, other_domain = other_rule

    if rule_type == 'exact' and other_type == 'exact':
        return domain == other_domain

    if rule_type == 'exact' and other_type == 'suffix':
        return suffix_matches_domain(other_domain, domain)

    if rule_type == 'suffix' and other_type == 'exact':
        return suffix_matches_domain(domain, other_domain)

    return (
        suffix_matches_domain(domain, other_domain)
        or suffix_matches_domain(other_domain, domain)
    )


def filter_cn_rules(cn_exact_domains, cn_suffix_domains, excluded_rules):
    filtered_domains = []
    removed_count = 0
    has_cn_catchall = 'cn' in cn_suffix_domains

    for domain in sorted(cn_exact_domains):
        if has_cn_catchall and suffix_matches_domain('cn', domain):
            continue

        rule = ('exact', domain)
        if any(rules_overlap(rule, excluded_rule) for excluded_rule in excluded_rules):
            removed_count += 1
            continue
        filtered_domains.append(domain)

    for domain in sorted(cn_suffix_domains):
        if domain == 'cn':
            continue

        if has_cn_catchall and suffix_matches_domain('cn', domain):
            continue

        rule = ('suffix', domain)
        if any(rules_overlap(rule, excluded_rule) for excluded_rule in excluded_rules):
            removed_count += 1
            continue
        filtered_domains.append(domain)

    return filtered_domains, removed_count, has_cn_catchall


def merge_additional_rules(domains, additional_exact_domains, additional_suffix_domains, has_cn_catchall):
    merged_domains = list(domains)
    existing_domains = set(domains)
    added_count = 0
    skipped_cn_count = 0
    skipped_duplicate_count = 0

    for domain in sorted(additional_exact_domains | additional_suffix_domains):
        if has_cn_catchall and suffix_matches_domain('cn', domain):
            skipped_cn_count += 1
            continue

        if domain in existing_domains:
            skipped_duplicate_count += 1
            continue

        merged_domains.append(domain)
        existing_domains.add(domain)
        added_count += 1

    return merged_domains, added_count, skipped_cn_count, skipped_duplicate_count


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


def count_output_lines(the_dns, has_cn_catchall, domain_count):
    the_dns_lines = len(the_dns.rstrip('\n').splitlines()) if the_dns else 0
    catchall_lines = 1 if has_cn_catchall else 0
    return the_dns_lines + catchall_lines + domain_count


def main():
    current_directory = Path.cwd()
    converted_directory = current_directory / 'converted'
    converted_directory.mkdir(exist_ok=True)

    cn_dns = require_cn_dns()
    the_dns = os.environ.get('THE_DNS')

    cn_exact_domains, cn_suffix_domains = load_rules(
        current_directory / CN_LIST_FILE,
        min_rules=MIN_RULE_COUNTS[CN_LIST_FILE],
    )
    google_exact_domains, google_suffix_domains = load_rules(
        current_directory / GOOGLE_CN_LIST_FILE,
        min_rules=MIN_RULE_COUNTS[GOOGLE_CN_LIST_FILE],
    )
    microsoft_exact_domains, microsoft_suffix_domains = load_rules(
        current_directory / MICROSOFT_CN_LIST_FILE,
        min_rules=MIN_RULE_COUNTS[MICROSOFT_CN_LIST_FILE],
    )
    additional_exact_domains, additional_suffix_domains = load_rules(
        current_directory / ADDITIONAL_LIST_FILE,
        min_rules=MIN_RULE_COUNTS[ADDITIONAL_LIST_FILE],
    )

    excluded_rules = [
        *[("exact", domain) for domain in sorted(google_exact_domains | microsoft_exact_domains)],
        *[("suffix", domain) for domain in sorted(google_suffix_domains | microsoft_suffix_domains)],
    ]

    filtered_domains, removed_count, has_cn_catchall = filter_cn_rules(
        cn_exact_domains,
        cn_suffix_domains,
        excluded_rules,
    )

    merged_domains, added_count, skipped_cn_count, skipped_duplicate_count = merge_additional_rules(
        filtered_domains,
        additional_exact_domains,
        additional_suffix_domains,
        has_cn_catchall,
    )

    final_file = converted_directory / 'cn-rules.txt'
    write_output(final_file, merged_domains, cn_dns, the_dns, has_cn_catchall)

    if not final_file.is_file() or final_file.stat().st_size == 0:
        raise ValidationError(f'Generated file is empty: {final_file}')

    generated_output_lines = count_output_lines(the_dns, has_cn_catchall, len(merged_domains))

    print(
        f'CN rules: {len(cn_exact_domains) + len(cn_suffix_domains)}, '
        f'removed overlaps: {removed_count}, '
        f'additional rules: {len(additional_exact_domains) + len(additional_suffix_domains)}, '
        f'additional skipped cn: {skipped_cn_count}, '
        f'additional skipped duplicates: {skipped_duplicate_count}, '
        f'additional added: {added_count}, '
        f'generated rules: {len(merged_domains)}, '
        f'output lines: {generated_output_lines}'
    )


if __name__ == '__main__':
    main()
