/**
 * Date field component for date input
 */

import React from 'react';
import type { TemplateField } from '../../../types/templates';
import { FieldWrapper } from './FieldWrapper';

interface DateFieldProps {
  field: TemplateField;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export const DateField: React.FC<DateFieldProps> = ({
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
        type="date"
        value={value}
        onChange={handleChange}
        disabled={disabled}
        required={field.required}
        className="field-input"
      />
    </FieldWrapper>
  );
};

