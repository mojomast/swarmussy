type RuleFn = (value: any) => boolean;

export function validate(payload: any, rules: Record<string, RuleFn>): { ok: boolean; errors: string[] } {
  const errors: string[] = [];
  for (const key of Object.keys(rules)) {
    const rule = rules[key];
    const value = (payload as any)[key];
    if (!rule(value)) {
      errors.push(`invalid_${key}`);
    }
  }
  return { ok: errors.length === 0, errors };
}
