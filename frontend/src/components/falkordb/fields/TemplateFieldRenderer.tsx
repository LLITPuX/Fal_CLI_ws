/**
 * Dynamic field renderer that selects the appropriate field component
 */

import React from 'react';
import type { TemplateField } from '../../../types/templates';
import { TextField } from './TextField';
import { LongTextField } from './LongTextField';
import { NumberField } from './NumberField';
import { BooleanField } from './BooleanField';
import { EnumField } from './EnumField';
import { DateField } from './DateField';
import { UrlField } from './UrlField';
import { EmailField } from './EmailField';

interface TemplateFieldRendererProps {
  field: TemplateField;
  value: any;
  onChange: (value: any) => void;
  disabled?: boolean;
}

export const TemplateFieldRenderer: React.FC<TemplateFieldRendererProps> = ({
  field,
  value,
  onChange,
  disabled = false,
}) => {
  switch (field.type) {
    case 'text':
      return <TextField field={field} value={value || ''} onChange={onChange} disabled={disabled} />;
    
    case 'longtext':
      return <LongTextField field={field} value={value || ''} onChange={onChange} disabled={disabled} />;
    
    case 'number':
      return <NumberField field={field} value={value ?? ''} onChange={onChange} disabled={disabled} />;
    
    case 'boolean':
      return <BooleanField field={field} value={value ?? null} onChange={onChange} disabled={disabled} />;
    
    case 'enum':
      return <EnumField field={field} value={value || ''} onChange={onChange} disabled={disabled} />;
    
    case 'date':
      return <DateField field={field} value={value || ''} onChange={onChange} disabled={disabled} />;
    
    case 'url':
      return <UrlField field={field} value={value || ''} onChange={onChange} disabled={disabled} />;
    
    case 'email':
      return <EmailField field={field} value={value || ''} onChange={onChange} disabled={disabled} />;
    
    default:
      return <TextField field={field} value={value || ''} onChange={onChange} disabled={disabled} />;
  }
};

