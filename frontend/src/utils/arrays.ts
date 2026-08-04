/** Coerce unknown values to a safe array for iteration (.map, spread, for...of). */
export function asArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? value : [];
}
