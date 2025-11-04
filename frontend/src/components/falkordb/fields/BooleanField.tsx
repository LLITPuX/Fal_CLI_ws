/**
 * Boolean field component for yes/no input
 */

import React from 'react';
import type { TemplateField } from '../../../types/templates';
import { FieldWrapper } from './FieldWrapper';

interface BooleanFieldProps {
  field: TemplateField;
  value: boolean | null;
  onChange: (value: boolean) => void;
  disabled?: boolean;
}

export const BooleanField: React.FC<BooleanFieldProps> = ({
  field,
  value,
  onChange,
  disabled = false,
}) => {
  return (
    <FieldWrapper label={field.label} required={field.required}>
      <div className="boolean-field">
        <label className="boolean-option">
          <input
            type="radio"
            checked={value === true}
            onChange={() => onChange(true)}
            disabled={disabled}
          />
          <span>Yes</span>
        </label>
        <label className="boolean-option">
          <input
            type="radio"
            checked={value === false}
            onChange={() => onChange(false)}
            disabled={disabled}
          />
          <span>No</span>
        </label>
      </div>
    </FieldWrapper>
  );
};

