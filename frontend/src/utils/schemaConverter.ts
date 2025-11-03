// Utilities for converting between VisualSchema and JSON string

import type { VisualSchema, SchemaField } from '../types/schema';

/**
 * Convert visual schema to JSON string for API
 */
export function visualSchemaToJSON(schema: VisualSchema): string {
  if (schema.fields.length === 0) {
    return '';
  }

  const buildFieldValue = (field: SchemaField): any => {
    const description = field.description || '';
    
    switch (field.type) {
      case 'string':
        return `string - ${description}`;
      
      case 'number':
        return `number - ${description}`;
      
      case 'boolean':
        return `boolean - ${description}`;
      
      case 'array<string>':
        return [`array of strings - ${description}`];
      
      case 'array<number>':
        return [`array of numbers - ${description}`];
      
      case 'array<object>':
        if (field.children && field.children.length > 0) {
          const childObj: Record<string, any> = {};
          field.children.forEach(child => {
            childObj[child.name] = buildFieldValue(child);
          });
          return [childObj];
        }
        return [`object with custom fields - ${description}`];
      
      case 'object':
        if (field.children && field.children.length > 0) {
          const childObj: Record<string, any> = {};
          field.children.forEach(child => {
            childObj[child.name] = buildFieldValue(child);
          });
          return childObj;
        }
        return `object with custom fields - ${description}`;
      
      default:
        return `${field.type} - ${description}`;
    }
  };

  const obj: Record<string, any> = {};
  schema.fields.forEach(field => {
    obj[field.name] = buildFieldValue(field);
  });

  return JSON.stringify(obj, null, 2);
}

/**
 * Try to parse JSON string into visual schema
 * Best effort - may not handle all complex cases
 */
export function jsonToVisualSchema(jsonString: string): VisualSchema {
  try {
    const parsed = JSON.parse(jsonString);
    if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
      throw new Error('Root must be an object');
    }

    const fields: SchemaField[] = [];

    const extractField = (name: string, value: any): SchemaField | null => {
      const id = crypto.randomUUID();
      
      // Try to parse type and description
      if (typeof value === 'string') {
        const parts = value.split(' - ');
        const typeStr = parts[0].trim().toLowerCase();
        const description = parts.slice(1).join(' - ').trim();
        
        if (typeStr.startsWith('string')) {
          return { id, name, type: 'string', description };
        } else if (typeStr.startsWith('number')) {
          return { id, name, type: 'number', description };
        } else if (typeStr.startsWith('boolean')) {
          return { id, name, type: 'boolean', description };
        }
        
        // Default to string if unclear
        return { id, name, type: 'string', description: value };
      }
      
      // Array
      if (Array.isArray(value) && value.length > 0) {
        const first = value[0];
        
        if (typeof first === 'string') {
          const desc = first.replace(/^array of strings\s*-\s*/i, '').trim();
          return { id, name, type: 'array<string>', description: desc };
        }
        
        if (typeof first === 'number') {
          return { id, name, type: 'array<number>', description: '' };
        }
        
        if (typeof first === 'object' && first !== null) {
          const children: SchemaField[] = [];
          Object.entries(first).forEach(([childName, childValue]) => {
            const child = extractField(childName, childValue);
            if (child) children.push(child);
          });
          return {
            id,
            name,
            type: 'array<object>',
            description: '',
            children,
          };
        }
      }
      
      // Object
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        const children: SchemaField[] = [];
        Object.entries(value).forEach(([childName, childValue]) => {
          const child = extractField(childName, childValue);
          if (child) children.push(child);
        });
        
        return {
          id,
          name,
          type: 'object',
          description: '',
          children,
        };
      }
      
      return null;
    };

    Object.entries(parsed).forEach(([fieldName, fieldValue]) => {
      const field = extractField(fieldName, fieldValue);
      if (field) fields.push(field);
    });

    return { fields };
  } catch (error) {
    console.error('Failed to parse JSON to visual schema:', error);
    return { fields: [] };
  }
}

/**
 * Get default visual schema (matches original default)
 */
export function getDefaultVisualSchema(): VisualSchema {
  return {
    fields: [
      {
        id: crypto.randomUUID(),
        name: 'title',
        type: 'string',
        description: 'A concise, descriptive title extracted from the text',
        required: true,
      },
      {
        id: crypto.randomUUID(),
        name: 'date_iso',
        type: 'string',
        description: 'Publication or creation date in ISO 8601 format (YYYY-MM-DD). Use today\'s date if not found',
        required: true,
      },
      {
        id: crypto.randomUUID(),
        name: 'summary',
        type: 'string',
        description: 'A comprehensive 2-3 sentence summary capturing the main ideas',
        required: true,
      },
      {
        id: crypto.randomUUID(),
        name: 'tags',
        type: 'array<string>',
        description: 'Keywords or topics (3-7 tags). Be specific and relevant',
      },
      {
        id: crypto.randomUUID(),
        name: 'sections',
        type: 'array<object>',
        description: 'Main content sections',
        children: [
          {
            id: crypto.randomUUID(),
            name: 'name',
            type: 'string',
            description: 'Section heading or topic name',
          },
          {
            id: crypto.randomUUID(),
            name: 'content',
            type: 'string',
            description: 'Full content of this section, preserving important details',
          },
        ],
      },
    ],
  };
}

