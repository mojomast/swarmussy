export function validate<T extends object>(payload: T, rules: Partial<{ [K in keyof T]: (v: any) => boolean }>): { ok: boolean; errors?: string[] } {
  const errors: string[] = []
  for (const key of Object.keys(rules) as Array<keyof T>) {
    const rule = (rules as any)[key] as ((v: any) => boolean) | undefined
    const value = (payload as any)[key]
    if (rule && !rule(value)) {
      errors.push(`Invalid value for ${String(key)}`)
    }
  }
  return { ok: errors.length === 0, errors: errors.length ? errors : undefined }
}
