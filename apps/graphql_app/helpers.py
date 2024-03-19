def _plural_from_single(s):
    return s.rstrip('y') + 'ies' if s.endswith('y') else s + 's'