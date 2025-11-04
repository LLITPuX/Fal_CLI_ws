/**
 * Email field component for email input with validation
 */

import React from 'react';
import type { TemplateField } from '../../../types/templates';
import { FieldWrapper } from './FieldWrapper';

interface EmailFieldProps {
  field: TemplateField;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export const EmailField: React.FC<EmailFieldProps> = ({
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
        type="email"
        value={value}
        onChange={handleChange}
        placeholder={field.placeholder || 'example@domain.com'}
        disabled={disabled}
        required={field.required}
        className="field-input"
      />
    </FieldWrapper>
  );
};

