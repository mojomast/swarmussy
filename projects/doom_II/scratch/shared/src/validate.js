export function validateJson(schema, data) {
  const errors = [];

  function isObject(v) {
    return v !== null && typeof v === 'object' && !Array.isArray(v);
  }

  function typeMatches(expected, value) {
    if (expected === 'string') return typeof value === 'string';
    if (expected === 'number') return typeof value === 'number';
    if (expected === 'object') return isObject(value);
    if (expected === 'array') return Array.isArray(value);
    return true;
  }

  function testPattern(pattern, value) {
    try {
      const re = new RegExp(pattern);
      return typeof value === 'string' && re.test(value);
    } catch {
      return false;
    }
  }

  function walk(subSchema, value, path) {
    if (!subSchema) return;

    // handle required for object-like shapes at this level
    if (subSchema.type === 'object') {
      if (!isObject(value)) {
        errors.push(`${path || 'payload'} should be an object`);
        return;
      }
      // required fields
      const required = subSchema.required || [];
      for (const r of required) {
        if (!(r in value)) {
          errors.push(`Missing required property: ${path ? path + '.' : ''}${r}`);
        }
      }
      // properties check
      const props = subSchema.properties || {};
      for (const key of Object.keys(value)) {
        if (props[key]) {
          walk(props[key], value[key], path ? path + '.' + key : key);
        } else if (subSchema.additionalProperties === false) {
          errors.push(`Unknown property: ${path ? path + '.' : ''}${key}`);
        }
      }
      // also validate that required nested props exist and types
      for (const key of Object.keys(props)) {
        if (key in value) {
          walk(props[key], value[key], path ? path + '.' + key : key);
        }
      }
    } else if (subSchema.type === 'array') {
      if (!Array.isArray(value)) {
        errors.push(`${path || 'payload'} should be an array`);
        return;
      }
      const itemSchema = subSchema.items;
      if (itemSchema) {
        for (let i = 0; i < value.length; i++) {
          walk(itemSchema, value[i], `${path}[${i}]`);
        }
      }
    } else {
      // primitive types
      if (subSchema.type) {
        if (!typeMatches(subSchema.type, value)) {
          errors.push(`Property ${path} should be of type ${subSchema.type}`);
        }
      }
      if (subSchema.pattern) {
        if (!testPattern(subSchema.pattern, value)) {
          errors.push(`Property ${path} does not match pattern ${subSchema.pattern}`);
        }
      }
    }
  }

  // Basic envelope checks
  if (!isObject(data)) {
    errors.push('Payload should be an object');
    return { valid: false, errors };
  }

  // respect top-level schema
  walk(schema, data, 'payload');

  const valid = errors.length === 0;
  return { valid, errors };
}
