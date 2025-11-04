/**
 * Text field component for short text input
 */

import React from 'react';
import type { TemplateField } from '../../../types/templates';
import { FieldWrapper } from './FieldWrapper';

interface TextFieldProps {
  field: TemplateField;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export const TextField: React.FC<TextFieldProps> = ({
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
        type="text"
        value={value}
        onChange={handleChange}
        placeholder={field.placeholder}
        disabled={disabled}
        required={field.required}
        className="field-input"
      />
    </FieldWrapper>
  );
};

