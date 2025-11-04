/**
 * Wrapper component for all field types
 */

import React from 'react';

interface FieldWrapperProps {
  label: string;
  required?: boolean;
  error?: string;
  children: React.ReactNode;
}

export const FieldWrapper: React.FC<FieldWrapperProps> = ({
  label,
  required = false,
  error,
  children,
}) => {
  return (
    <div className="field-wrapper">
      <label className="field-label">
        {label}
        {required && <span className="required">*</span>}
      </label>
      {children}
      {error && <span className="field-error">{error}</span>}
    </div>
  );
};

