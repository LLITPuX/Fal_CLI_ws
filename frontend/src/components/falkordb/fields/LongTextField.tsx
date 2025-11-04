/**
 * Long text field component for multiline text input
 */

import React from 'react';
import type { TemplateField } from '../../../types/templates';
import { FieldWrapper } from './FieldWrapper';

interface LongTextFieldProps {
  field: TemplateField;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export const LongTextField: React.FC<LongTextFieldProps> = ({
  field,
  value,
  onChange,
  disabled = false,
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
  };

  return (
    <FieldWrapper label={field.label} required={field.required}>
      <textarea
        value={value}
        onChange={handleChange}
        placeholder={field.placeholder}
        disabled={disabled}
        required={field.required}
        className="field-textarea"
        rows={4}
      />
    </FieldWrapper>
  );
};

