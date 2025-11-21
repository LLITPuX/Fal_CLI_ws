/**
 * Node Schema Editor - візуальний редактор схеми вузлів з динамічними полями
 */

import { useState, useEffect } from 'react';
import { Plus, Trash2, GripVertical, Save, History } from 'lucide-react';
import type { NodeSchema, NodeSchemaField, FieldType } from '../../types/archive';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../ui/card';
import { Checkbox } from '../ui/checkbox';
import { Textarea } from '../ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../ui/dialog';

interface NodeSchemaEditorProps {
  schema: NodeSchema | null;
  onSave: (schema: NodeSchema) => Promise<void>;
  onVersionHistory?: () => void;
  disabled?: boolean;
}

const FIELD_TYPES: FieldType[] = [
  'text',
  'longtext',
  'number',
  'boolean',
  'enum',
  'date',
  'url',
  'email',
  'array',
  'object',
];

const FIELD_TYPE_LABELS: Record<FieldType, string> = {
  text: 'Текст',
  longtext: 'Довгий текст',
  number: 'Число',
  boolean: 'Булеве',
  enum: 'Перелік',
  date: 'Дата',
  url: 'URL',
  email: 'Email',
  array: 'Масив',
  object: 'Об\'єкт',
};

export const NodeSchemaEditor: React.FC<NodeSchemaEditorProps> = ({
  schema,
  onSave,
  onVersionHistory,
  disabled = false,
}) => {
  const [editedSchema, setEditedSchema] = useState<NodeSchema | null>(schema);
  const [editingField, setEditingField] = useState<NodeSchemaField | null>(null);
  const [showFieldDialog, setShowFieldDialog] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    setEditedSchema(schema);
  }, [schema]);

  const handleAddField = () => {
    const newField: NodeSchemaField = {
      id: crypto.randomUUID(),
      name: '',
      type: 'text',
      label: '',
      required: false,
      default_value: null,
      enum_values: null,
      validation: null,
    };
    setEditingField(newField);
    setShowFieldDialog(true);
  };

  const handleEditField = (field: NodeSchemaField) => {
    setEditingField({ ...field });
    setShowFieldDialog(true);
  };

  const handleDeleteField = (fieldId: string) => {
    if (!editedSchema) return;

    const field = editedSchema.fields.find((f) => f.id === fieldId);
    if (field?.required) {
      if (!confirm(`Поле "${field.name}" є обов'язковим. Ви впевнені, що хочете його видалити?`)) {
        return;
      }
    }

    setEditedSchema({
      ...editedSchema,
      fields: editedSchema.fields.filter((f) => f.id !== fieldId),
    });
  };

  const handleSaveField = (field: NodeSchemaField) => {
    if (!editedSchema) return;

    // Validate field
    if (!field.name.trim()) {
      setError('Назва поля обов\'язкова');
      return;
    }

    if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(field.name)) {
      setError('Назва має містити лише латинські літери, цифри та підкреслення');
      return;
    }

    const existingNames = editedSchema.fields
      .filter((f) => f.id !== field.id)
      .map((f) => f.name);

    if (existingNames.includes(field.name)) {
      setError('Поле з такою назвою вже існує');
      return;
    }

    setError(null);

    // Update or add field
    const existingIndex = editedSchema.fields.findIndex((f) => f.id === field.id);
    const updatedFields = [...editedSchema.fields];

    if (existingIndex >= 0) {
      updatedFields[existingIndex] = field;
    } else {
      updatedFields.push(field);
    }

    setEditedSchema({
      ...editedSchema,
      fields: updatedFields,
    });

    setShowFieldDialog(false);
    setEditingField(null);
  };

  const handleSaveSchema = async () => {
    if (!editedSchema) return;

    // Validate schema
    if (!editedSchema.label.trim()) {
      setError('Назва схеми обов\'язкова');
      return;
    }

    if (editedSchema.fields.length === 0) {
      setError('Схема повинна містити принаймні одне поле');
      return;
    }

    setError(null);
    setIsSaving(true);

    try {
      const schemaToSave: NodeSchema = {
        ...editedSchema,
        version: editedSchema.version + 1,
        updated_at: new Date().toISOString(),
      };
      await onSave(schemaToSave);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Помилка збереження схеми');
    } finally {
      setIsSaving(false);
    }
  };

  if (!schema && !editedSchema) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          <p>Виберіть схему для редагування</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Редактор схеми вузла</CardTitle>
            <CardDescription>
              {editedSchema?.label} (версія {editedSchema?.version})
            </CardDescription>
          </div>
          <div className="flex gap-2">
            {onVersionHistory && (
              <Button
                variant="outline"
                size="sm"
                onClick={onVersionHistory}
                disabled={disabled}
              >
                <History className="w-4 h-4 mr-2" />
                Історія версій
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {error && (
          <div className="rounded-md bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {/* Schema metadata */}
        <div className="space-y-2">
          <Label htmlFor="schema-label">Назва схеми *</Label>
          <Input
            id="schema-label"
            value={editedSchema?.label || ''}
            onChange={(e) =>
              setEditedSchema(editedSchema ? { ...editedSchema, label: e.target.value } : null)
            }
            disabled={disabled}
            placeholder="Document, Rule, Entity..."
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="schema-description">Опис схеми</Label>
          <Textarea
            id="schema-description"
            value={editedSchema?.description || ''}
            onChange={(e) =>
              setEditedSchema(
                editedSchema ? { ...editedSchema, description: e.target.value } : null
              )
            }
            disabled={disabled}
            placeholder="Опишіть призначення цієї схеми..."
            rows={3}
          />
        </div>

        {/* Fields list */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label>Поля схеми</Label>
            <Button
              type="button"
              size="sm"
              onClick={handleAddField}
              disabled={disabled}
            >
              <Plus className="w-4 h-4 mr-2" />
              Додати поле
            </Button>
          </div>

          {editedSchema?.fields.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground border border-dashed rounded-md">
              <p>Немає полів. Додайте перше поле.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {editedSchema?.fields.map((field) => (
                <div
                  key={field.id}
                  className="flex items-center gap-2 p-3 border rounded-md hover:bg-accent/50 transition-colors"
                >
                  <GripVertical className="w-4 h-4 text-muted-foreground cursor-grab" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{field.name}</span>
                      {field.required && (
                        <span className="text-xs bg-primary/10 text-primary px-1.5 py-0.5 rounded">
                          обов'язкове
                        </span>
                      )}
                      <span className="text-xs text-muted-foreground">
                        ({FIELD_TYPE_LABELS[field.type]})
                      </span>
                    </div>
                    {field.label && field.label !== field.name && (
                      <div className="text-sm text-muted-foreground">{field.label}</div>
                    )}
                  </div>
                  <div className="flex items-center gap-1">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEditField(field)}
                      disabled={disabled}
                    >
                      Редагувати
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteField(field.id)}
                      disabled={disabled || field.required}
                      title={field.required ? 'Не можна видалити обов\'язкове поле' : 'Видалити'}
                    >
                      <Trash2 className="w-4 h-4 text-destructive" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>

      <CardFooter className="flex justify-end gap-2">
        <Button
          onClick={handleSaveSchema}
          disabled={disabled || isSaving || !editedSchema}
        >
          {isSaving ? (
            <>Збереження...</>
          ) : (
            <>
              <Save className="w-4 h-4 mr-2" />
              Зберегти нову версію
            </>
          )}
        </Button>
      </CardFooter>

      {/* Field editor dialog */}
      <Dialog open={showFieldDialog} onOpenChange={setShowFieldDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingField?.name ? 'Редагувати поле' : 'Додати поле'}
            </DialogTitle>
            <DialogDescription>
              Налаштуйте параметри поля схеми вузла
            </DialogDescription>
          </DialogHeader>

          {editingField && (
            <FieldEditorDialog
              field={editingField}
              onChange={(field) => setEditingField(field)}
              onSave={handleSaveField}
              onCancel={() => {
                setShowFieldDialog(false);
                setEditingField(null);
                setError(null);
              }}
              existingNames={
                editedSchema?.fields
                  .filter((f) => f.id !== editingField.id)
                  .map((f) => f.name) || []
              }
            />
          )}
        </DialogContent>
      </Dialog>
    </Card>
  );
};

interface FieldEditorDialogProps {
  field: NodeSchemaField;
  onChange: (field: NodeSchemaField) => void;
  onSave: (field: NodeSchemaField) => void;
  onCancel: () => void;
  existingNames: string[];
}

const FieldEditorDialog: React.FC<FieldEditorDialogProps> = ({
  field,
  onChange,
  onSave,
  onCancel,
  existingNames,
}) => {
  const [localField, setLocalField] = useState<NodeSchemaField>(field);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLocalField(field);
  }, [field]);

  const handleFieldChange = (updates: Partial<NodeSchemaField>) => {
    const updated = { ...localField, ...updates };
    setLocalField(updated);
    onChange(updated);
  };

  const handleSave = () => {
    // Validate
    if (!localField.name.trim()) {
      setError('Назва поля обов\'язкова');
      return;
    }

    if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(localField.name)) {
      setError('Назва має містити лише латинські літери, цифри та підкреслення');
      return;
    }

    if (existingNames.includes(localField.name)) {
      setError('Поле з такою назвою вже існує');
      return;
    }

    if (!localField.label.trim()) {
      setError('Мітка поля обов\'язкова');
      return;
    }

    setError(null);
    onSave(localField);
  };

  return (
    <div className="space-y-4">
      {error && (
        <div className="rounded-md bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="space-y-2">
        <Label htmlFor="field-name">Назва поля (ключ) *</Label>
        <Input
          id="field-name"
          value={localField.name}
          onChange={(e) => handleFieldChange({ name: e.target.value })}
          placeholder="title, content, priority..."
        />
        <p className="text-xs text-muted-foreground">
          Використовуйте латинські літери, цифри та підкреслення
        </p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="field-label">Мітка поля *</Label>
        <Input
          id="field-label"
          value={localField.label}
          onChange={(e) => handleFieldChange({ label: e.target.value })}
          placeholder="Назва, Контент, Пріоритет..."
        />
        <p className="text-xs text-muted-foreground">
          Відображається назва для користувача
        </p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="field-type">Тип даних *</Label>
        <Select
          value={localField.type}
          onValueChange={(value: FieldType) => handleFieldChange({ type: value })}
        >
          <SelectTrigger id="field-type">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {FIELD_TYPES.map((type) => (
              <SelectItem key={type} value={type}>
                {FIELD_TYPE_LABELS[type]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {localField.type === 'enum' && (
        <div className="space-y-2">
          <Label htmlFor="field-enum-values">Значення переліку (через кому)</Label>
          <Input
            id="field-enum-values"
            value={localField.enum_values?.join(', ') || ''}
            onChange={(e) =>
              handleFieldChange({
                enum_values: e.target.value
                  .split(',')
                  .map((v) => v.trim())
                  .filter((v) => v.length > 0),
              })
            }
            placeholder="high, medium, low"
          />
        </div>
      )}

      <div className="space-y-2">
        <Label htmlFor="field-default">Значення за замовчуванням (опціонально)</Label>
        <Input
          id="field-default"
          value={localField.default_value?.toString() || ''}
          onChange={(e) => {
            const value = e.target.value;
            let parsed: any = value;

            if (localField.type === 'number') {
              parsed = value ? parseFloat(value) : null;
            } else if (localField.type === 'boolean') {
              parsed = value === 'true' || value === '1';
            }

            handleFieldChange({ default_value: value ? parsed : null });
          }}
          placeholder="За замовчуванням..."
        />
      </div>

      <div className="flex items-center space-x-2">
        <Checkbox
          id="field-required"
          checked={localField.required}
          onCheckedChange={(checked) =>
            handleFieldChange({ required: checked === true })
          }
        />
        <Label
          htmlFor="field-required"
          className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
        >
          Обов'язкове поле
        </Label>
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button variant="outline" onClick={onCancel}>
          Скасувати
        </Button>
        <Button onClick={handleSave}>
          {field.name ? 'Зберегти' : 'Додати'}
        </Button>
      </div>
    </div>
  );
};

