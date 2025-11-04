/**
 * URL field component for URL input with validation
 */

import React from 'react';
import type { TemplateField } from '../../../types/templates';
import { FieldWrapper } from './FieldWrapper';

interface UrlFieldProps {
  field: TemplateField;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export const UrlField: React.FC<UrlFieldProps> = ({
  field,
  value,
  onChange,
  disabled = false,
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value);
  };

  return (
    <FieldWrapper label={field.label} required={field.required}>
      <input
        type="url"
        value={value}
        onChange={handleChange}
        placeholder={field.placeholder || 'https://example.com'}
        disabled={disabled}
        required={field.required}
        className="field-input"
      />
    </FieldWrapper>
  );
};

