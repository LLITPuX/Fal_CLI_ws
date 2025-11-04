/**
 * Number field component for numeric input
 */

import React from 'react';
import type { TemplateField } from '../../../types/templates';
import { FieldWrapper } from './FieldWrapper';

interface NumberFieldProps {
  field: TemplateField;
  value: number | string;
  onChange: (value: number | string) => void;
  disabled?: boolean;
}

export const NumberField: React.FC<NumberFieldProps> = ({
  field,
  value,
  onChange,
  disabled = false,
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    // Allow empty string or valid number
    if (newValue === '') {
      onChange('');
    } else {
      const numValue = parseFloat(newValue);
      if (!isNaN(numValue)) {
        onChange(numValue);
      }
    }
  };

  return (
    <FieldWrapper label={field.label} required={field.required}>
      <input
        type="number"
        value={value}
        onChange={handleChange}
        placeholder={field.placeholder}
        disabled={disabled}
        required={field.required}
        min={field.validation?.min}
        max={field.validation?.max}
        step="any"
        className="field-input"
      />
    </FieldWrapper>
  );
};

