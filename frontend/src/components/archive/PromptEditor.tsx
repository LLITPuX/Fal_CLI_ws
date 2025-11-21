/**
 * Prompt Editor - редактор промптів з підтримкою placeholders та версіонування
 */

import { useState, useEffect, useRef } from 'react';
import { Save, History, Eye } from 'lucide-react';
import type { PromptTemplate } from '../../types/archive';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../ui/card';

interface PromptEditorProps {
  prompt: PromptTemplate | null;
  onSave: (prompt: PromptTemplate) => Promise<void>;
  onVersionHistory?: () => void;
  onPreview?: (content: string) => void;
  disabled?: boolean;
}

const PLACEHOLDERS = [
  { key: 'content', label: '{{content}}', description: 'Контент документа' },
  { key: 'schema', label: '{{schema}}', description: 'JSON схема' },
  { key: 'file_path', label: '{{file_path}}', description: 'Шлях до файлу' },
  { key: 'document_type', label: '{{document_type}}', description: 'Тип документа' },
];

export const PromptEditor: React.FC<PromptEditorProps> = ({
  prompt,
  onSave,
  onVersionHistory,
  onPreview,
  disabled = false,
}) => {
  const [editedPrompt, setEditedPrompt] = useState<PromptTemplate | null>(prompt);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [showPlaceholders, setShowPlaceholders] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    setEditedPrompt(prompt);
  }, [prompt]);

  const handleContentChange = (value: string) => {
    if (!editedPrompt) return;
    setEditedPrompt({ ...editedPrompt, content: value });
  };

  const insertPlaceholder = (placeholder: string) => {
    if (!textareaRef.current || !editedPrompt) return;

    const textarea = textareaRef.current;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = editedPrompt.content;
    const newText = text.substring(0, start) + placeholder + text.substring(end);

    handleContentChange(newText);

    // Restore cursor position after placeholder
    setTimeout(() => {
      textarea.focus();
      const newPosition = start + placeholder.length;
      textarea.setSelectionRange(newPosition, newPosition);
    }, 0);

    setShowPlaceholders(false);
  };

  const handleSave = async () => {
    if (!editedPrompt) return;

    if (!editedPrompt.content.trim()) {
      setError('Промпт не може бути порожнім');
      return;
    }

    if (!editedPrompt.name.trim()) {
      setError('Назва промпту обов\'язкова');
      return;
    }

    setError(null);
    setIsSaving(true);

    try {
      const promptToSave: PromptTemplate = {
        ...editedPrompt,
        version: editedPrompt.version + 1,
        updated_at: new Date().toISOString(),
      };
      await onSave(promptToSave);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Помилка збереження промпту');
    } finally {
      setIsSaving(false);
    }
  };

  const handlePreview = () => {
    if (!editedPrompt || !onPreview) return;
    onPreview(editedPrompt.content);
  };

  // Detect placeholders in content
  const detectedPlaceholders = editedPrompt?.content.match(/\{\{(\w+)\}\}/g) || [];
  const uniquePlaceholders = Array.from(
    new Set(detectedPlaceholders.map((p) => p.replace(/[{}]/g, '')))
  );

  if (!prompt && !editedPrompt) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          <p>Виберіть промпт для редагування</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Редактор промпту</CardTitle>
            <CardDescription>
              {editedPrompt?.name} (версія {editedPrompt?.version})
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

        {/* Prompt name */}
        <div className="space-y-2">
          <Label htmlFor="prompt-name">Назва промпту *</Label>
          <input
            id="prompt-name"
            type="text"
            value={editedPrompt?.name || ''}
            onChange={(e) =>
              setEditedPrompt(
                editedPrompt ? { ...editedPrompt, name: e.target.value } : null
              )
            }
            disabled={disabled}
            className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
            placeholder="Назва промпту..."
          />
        </div>

        {/* Placeholders helper */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label>Доступні placeholders</Label>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setShowPlaceholders(!showPlaceholders)}
            >
              {showPlaceholders ? 'Сховати' : 'Показати'}
            </Button>
          </div>

          {showPlaceholders && (
            <div className="grid grid-cols-2 gap-2 p-3 border rounded-md bg-muted/50">
              {PLACEHOLDERS.map((ph) => (
                <button
                  key={ph.key}
                  type="button"
                  onClick={() => insertPlaceholder(ph.label)}
                  disabled={disabled}
                  className="text-left p-2 rounded hover:bg-accent transition-colors text-sm"
                  title={ph.description}
                >
                  <code className="text-primary font-mono">{ph.label}</code>
                  <div className="text-xs text-muted-foreground mt-1">
                    {ph.description}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Detected placeholders */}
        {uniquePlaceholders.length > 0 && (
          <div className="space-y-2">
            <Label>Виявлені placeholders у промпті</Label>
            <div className="flex flex-wrap gap-2">
              {uniquePlaceholders.map((ph) => (
                <span
                  key={ph}
                  className="px-2 py-1 rounded bg-primary/10 text-primary text-xs font-mono"
                >
                  {`{{${ph}}}`}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Prompt content editor */}
        <div className="space-y-2">
          <Label htmlFor="prompt-content">Промпт *</Label>
          <div className="relative">
            <Textarea
              ref={textareaRef}
              id="prompt-content"
              value={editedPrompt?.content || ''}
              onChange={(e) => {
                handleContentChange(e.target.value);
              }}
              onKeyDown={(e) => {
                // Auto-complete {{ when user types {
                if (e.key === '{' && !e.shiftKey) {
                  e.preventDefault();
                  const textarea = e.currentTarget;
                  const start = textarea.selectionStart;
                  const value = editedPrompt?.content || '';
                  const newValue = value.substring(0, start) + '{{' + value.substring(start);
                  handleContentChange(newValue);
                  setTimeout(() => {
                    textarea.setSelectionRange(start + 2, start + 2);
                  }, 0);
                }
              }}
              disabled={disabled}
              placeholder="Введіть промпт для парсингу документів..."
              rows={15}
              className="font-mono text-sm"
              style={{ tabSize: 2 }}
            />
            <div className="absolute bottom-2 right-2 text-xs text-muted-foreground">
              {editedPrompt?.content.length || 0} символів
            </div>
          </div>
          <p className="text-xs text-muted-foreground">
            Використовуйте placeholders для динамічних значень. Натисніть кнопку
            "Показати" вище, щоб вставити placeholder.
          </p>
        </div>

        {/* Preview button */}
        {onPreview && (
          <Button
            type="button"
            variant="outline"
            onClick={handlePreview}
            disabled={disabled || !editedPrompt?.content}
          >
            <Eye className="w-4 h-4 mr-2" />
            Попередній перегляд
          </Button>
        )}
      </CardContent>

      <CardFooter className="flex justify-end gap-2">
        <Button
          onClick={handleSave}
          disabled={disabled || isSaving || !editedPrompt}
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
    </Card>
  );
};

