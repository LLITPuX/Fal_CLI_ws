// Types for visual schema builder

export type FieldType =
  | 'string'
  | 'number'
  | 'boolean'
  | 'array<string>'
  | 'array<number>'
  | 'array<object>'
  | 'object';

export interface SchemaField {
  id: string;
  name: string;
  type: FieldType;
  description: string;
  required?: boolean;
  // For nested structures (object and array<object>)
  children?: SchemaField[];
}

export interface VisualSchema {
  fields: SchemaField[];
}

export const FIELD_TYPE_LABELS: Record<FieldType, string> = {
  string: 'Текст (string)',
  number: 'Число (number)',
  boolean: 'Логічне значення (boolean)',
  'array<string>': 'Масив текстів (array<string>)',
  'array<number>': 'Масив чисел (array<number>)',
  'array<object>': 'Масив об\'єктів (array<object>)',
  object: 'Об\'єкт (object)',
};

export const FIELD_TYPE_EXAMPLES: Record<FieldType, string> = {
  string: '"example text"',
  number: '42',
  boolean: 'true / false',
  'array<string>': '["item1", "item2"]',
  'array<number>': '[1, 2, 3]',
  'array<object>': '[{"key": "value"}]',
  object: '{"key": "value"}',
};

