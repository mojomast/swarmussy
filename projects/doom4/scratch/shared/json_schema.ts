// Lightweight JSON schema validator for world editor payloads
// This is a minimal, dependency-free validator suitable for MVP backends.

export type JsonSchemaError = {
  path: string;
  message: string;
};

function isString(v: any): boolean { return typeof v === 'string'; }
function isNumber(v: any): boolean { return typeof v === 'number'; }
function isArray(v: any): boolean { return Array.isArray(v); }
function isObject(v: any): boolean { return v !== null && typeof v === 'object' && !Array.isArray(v); }

export function validateWorldPayload(p: any): JsonSchemaError[] {
  const errors: JsonSchemaError[] = [];
  if (!isObject(p)) {
    errors.push({ path: '', message: 'World payload must be an object' });
    return errors;
  }

  if (!p.worldId || !isString(p.worldId)) {
    errors.push({ path: 'worldId', message: 'worldId must be a string' });
  }

  // editor
  if (!isObject(p.editor)) {
    errors.push({ path: 'editor', message: 'editor must be an object' });
  } else {
    const e = p.editor;
    if (!e.mode || (e.mode !== 'edit' && e.mode !== 'play')) {
      errors.push({ path: 'editor.mode', message: 'editor.mode must be "edit" or "play"' });
    }
  }

  // plan
  if (!isObject(p.plan)) {
    errors.push({ path: 'plan', message: 'plan must be an object' });
  } else {
    const pl = p.plan;
    if (!pl.planId || !isString(pl.planId)) {
      errors.push({ path: 'plan.planId', message: 'plan.planId must be a string' });
    }
  }

  // assets
  if (!isArray(p.assets)) {
    errors.push({ path: 'assets', message: 'assets must be an array' });
  } else {
    for (let i = 0; i < p.assets.length; i++) {
      const a = p.assets[i];
      if (!isObject(a)) {
        errors.push({ path: `assets[${i}]`, message: 'asset must be an object' });
        continue;
      }
      if (!a.assetId || !isString(a.assetId)) {
        errors.push({ path: `assets[${i}].assetId`, message: 'assetId must be a string' });
      }
      if (!a.type || typeof a.type !== 'string') {
        errors.push({ path: `assets[${i}].type`, message: 'type must be a string' });
      }
      if (!a.name || !isString(a.name)) {
        errors.push({ path: `assets[${i}].name`, message: 'name must be a string' });
      }
      // metadata is optional; skip deep validation
    }
  }

  // levels
  if (!isArray(p.levels)) {
    errors.push({ path: 'levels', message: 'levels must be an array' });
  } else {
    for (let i = 0; i < p.levels.length; i++) {
      const l = p.levels[i];
      if (!isObject(l)) {
        errors.push({ path: `levels[${i}]`, message: 'level must be an object' });
        continue;
      }
      if (!l.levelId || !isString(l.levelId)) {
        errors.push({ path: `levels[${i}].levelId`, message: 'levelId must be a string' });
      }
      if (!l.name || !isString(l.name)) {
        errors.push({ path: `levels[${i}].name`, message: 'name must be a string' });
      }
      if (l.width !== undefined && !isNumber(l.width)) {
        errors.push({ path: `levels[${i}].width`, message: 'width must be a number' });
      }
      if (l.height !== undefined && !isNumber(l.height)) {
        errors.push({ path: `levels[${i}].height`, message: 'height must be a number' });
      }
    }
  }

  // map is optional; if provided must be object
  if (p.map !== undefined && !isObject(p.map)) {
    errors.push({ path: 'map', message: 'map, if provided, must be an object' });
  }

  // createdAt/updatedAt
  if (p.createdAt !== undefined && !isString(p.createdAt)) {
    errors.push({ path: 'createdAt', message: 'createdAt must be a string' });
  }
  if (p.updatedAt !== undefined && !isString(p.updatedAt)) {
    errors.push({ path: 'updatedAt', message: 'updatedAt must be a string' });
  }

  return errors;
}

// New: Plan payload validation (lightweight)
export function validatePlanPayload(p: any): JsonSchemaError[] {
  const errors: JsonSchemaError[] = [];
  if (!isObject(p)) {
    errors.push({ path: '', message: 'Plan payload must be an object' });
    return errors;
  }
  if (!p.planId || !isString(p.planId)) {
    errors.push({ path: 'planId', message: 'planId must be a string' });
  }
  if (!p.name || !isString(p.name)) {
    errors.push({ path: 'name', message: 'name must be a string' });
  }
  if (p.status !== undefined && typeof p.status !== 'string') {
    errors.push({ path: 'status', message: 'status must be a string' });
  }
  return errors;
}
