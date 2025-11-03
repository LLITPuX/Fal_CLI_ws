import { useEffect, useState } from 'react';

const TEMPLATES_KEY = 'gemini_schema_templates';

export interface SchemaTemplate {
  id: string;
  name: string;
  schema: string;
  createdAt: string;
}

export const useSchemaTemplates = () => {
  const [templates, setTemplates] = useState<SchemaTemplate[]>([]);

  // Load templates from localStorage on mount
  useEffect(() => {
    const loadTemplates = () => {
      try {
        const stored = localStorage.getItem(TEMPLATES_KEY);
        if (stored) {
          const parsed = JSON.parse(stored);
          setTemplates(Array.isArray(parsed) ? parsed : []);
        }
      } catch (error) {
        console.error('Failed to load schema templates:', error);
        setTemplates([]);
      }
    };

    loadTemplates();
  }, []);

  // Save templates to localStorage
  const saveTemplates = (newTemplates: SchemaTemplate[]) => {
    try {
      localStorage.setItem(TEMPLATES_KEY, JSON.stringify(newTemplates));
      setTemplates(newTemplates);
    } catch (error) {
      console.error('Failed to save schema templates:', error);
      throw new Error('Failed to save template');
    }
  };

  const addTemplate = (name: string, schema: string): SchemaTemplate => {
    const newTemplate: SchemaTemplate = {
      id: crypto.randomUUID(),
      name: name.trim(),
      schema: schema.trim(),
      createdAt: new Date().toISOString(),
    };

    const updated = [...templates, newTemplate];
    saveTemplates(updated);
    return newTemplate;
  };

  const deleteTemplate = (id: string) => {
    const updated = templates.filter((t) => t.id !== id);
    saveTemplates(updated);
  };

  const updateTemplate = (id: string, name: string, schema: string) => {
    const updated = templates.map((t) =>
      t.id === id ? { ...t, name: name.trim(), schema: schema.trim() } : t
    );
    saveTemplates(updated);
  };

  const exportTemplates = (): string => {
    return JSON.stringify(templates, null, 2);
  };

  const importTemplates = (jsonString: string): void => {
    try {
      const parsed = JSON.parse(jsonString);
      if (!Array.isArray(parsed)) {
        throw new Error('Invalid format: expected an array');
      }

      // Validate structure
      for (const item of parsed) {
        if (!item.id || !item.name || !item.schema || !item.createdAt) {
          throw new Error('Invalid template structure');
        }
      }

      saveTemplates(parsed);
    } catch (error) {
      console.error('Failed to import templates:', error);
      throw new Error(
        error instanceof Error ? error.message : 'Failed to import templates'
      );
    }
  };

  return {
    templates,
    addTemplate,
    deleteTemplate,
    updateTemplate,
    exportTemplates,
    importTemplates,
  };
};

