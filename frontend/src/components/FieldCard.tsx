import type { SchemaField } from '../types/schema';
import { FIELD_TYPE_LABELS } from '../types/schema';

interface FieldCardProps {
  field: SchemaField;
  onEdit: (field: SchemaField) => void;
  onDelete: (id: string) => void;
  onMoveUp?: (id: string) => void;
  onMoveDown?: (id: string) => void;
  canMoveUp: boolean;
  canMoveDown: boolean;
  disabled?: boolean;
  level?: number;
}

export const FieldCard: React.FC<FieldCardProps> = ({
  field,
  onEdit,
  onDelete,
  onMoveUp,
  onMoveDown,
  canMoveUp,
  canMoveDown,
  disabled = false,
  level = 0,
}) => {
  const handleDelete = () => {
    if (confirm(`Видалити поле "${field.name}"?`)) {
      onDelete(field.id);
    }
  };

  return (
    <div className={`field-card ${level > 0 ? 'field-card-nested' : ''}`}>
      <div className="field-card-header">
        <div className="field-card-title">
          <span className="field-name">{field.name}</span>
          {field.required && <span className="required-badge">обов'язкове</span>}
        </div>
        <div className="field-card-actions">
          {onMoveUp && (
            <button
              type="button"
              onClick={() => onMoveUp(field.id)}
              disabled={!canMoveUp || disabled}
              className="field-action-btn"
              title="Перемістити вгору"
            >
              ↑
            </button>
          )}
          {onMoveDown && (
            <button
              type="button"
              onClick={() => onMoveDown(field.id)}
              disabled={!canMoveDown || disabled}
              className="field-action-btn"
              title="Перемістити вниз"
            >
              ↓
            </button>
          )}
          <button
            type="button"
            onClick={() => onEdit(field)}
            disabled={disabled}
            className="field-action-btn edit"
            title="Редагувати"
          >
            ✏️
          </button>
          <button
            type="button"
            onClick={handleDelete}
            disabled={disabled}
            className="field-action-btn delete"
            title="Видалити"
          >
            🗑️
          </button>
        </div>
      </div>

      <div className="field-card-meta">
        <span className="field-type">{FIELD_TYPE_LABELS[field.type]}</span>
      </div>

      {field.description && (
        <p className="field-description">{field.description}</p>
      )}

      {field.children && field.children.length > 0 && (
        <div className="field-children">
          <div className="field-children-label">Вкладені поля:</div>
          {field.children.map((child) => (
            <FieldCard
              key={child.id}
              field={child}
              onEdit={onEdit}
              onDelete={onDelete}
              canMoveUp={false}
              canMoveDown={false}
              disabled={disabled}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};

