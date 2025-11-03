/**
 * Form for creating nodes in FalkorDB
 */

import { useState, useEffect } from 'react';
import type { CreateNodeRequest, NodeProperties } from '../../types/falkordb';

interface NodeFormProps {
  onSubmit: (request: CreateNodeRequest) => Promise<void>;
  isLoading: boolean;
  availableLabels?: string[];
}

interface PropertyField {
  id: string;
  key: string;
  value: string;
  type: 'string' | 'number' | 'boolean';
}

export const NodeForm = ({ onSubmit, isLoading, availableLabels = [] }: NodeFormProps) => {
  const [label, setLabel] = useState('');
  const [customLabel, setCustomLabel] = useState('');
  const [useCustomLabel, setUseCustomLabel] = useState(false);
  const [properties, setProperties] = useState<PropertyField[]>([]);

  // Initialize with one empty field
  useEffect(() => {
    if (properties.length === 0) {
      addProperty();
    }
  }, []);

  const addProperty = () => {
    setProperties([
      ...properties,
      { id: Date.now().toString(), key: '', value: '', type: 'string' },
    ]);
  };

  const removeProperty = (id: string) => {
    setProperties(properties.filter((p) => p.id !== id));
  };

  const updateProperty = (
    id: string,
    field: 'key' | 'value' | 'type',
    value: string
  ) => {
    setProperties(
      properties.map((p) =>
        p.id === id ? { ...p, [field]: value } : p
      )
    );
  };

  const parseValue = (value: string, type: PropertyField['type']): string | number | boolean => {
    if (!value.trim()) return '';
    
    switch (type) {
      case 'number':
        const num = parseFloat(value);
        return isNaN(num) ? value : num;
      case 'boolean':
        return value.toLowerCase() === 'true';
      default:
        return value;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const finalLabel = useCustomLabel ? customLabel.trim() : label;

    if (!finalLabel) {
      alert('Label is required');
      return;
    }

    // Build properties object from fields
    const nodeProperties: NodeProperties = {};
    properties.forEach((prop) => {
      if (prop.key.trim()) {
        nodeProperties[prop.key.trim()] = parseValue(prop.value, prop.type);
      }
    });

    await onSubmit({
      label: finalLabel,
      properties: nodeProperties,
    });

    // Reset form
    setLabel('');
    setCustomLabel('');
    setUseCustomLabel(false);
    setProperties([{ id: Date.now().toString(), key: '', value: '', type: 'string' }]);
  };

  const hasAvailableLabels = availableLabels.length > 0;

  return (
    <form onSubmit={handleSubmit} className="falkordb-form">
      <h3>📍 Create Node</h3>
      
      <div className="form-group">
        <label htmlFor="node-label">Label *</label>
        
        {hasAvailableLabels && (
          <div className="label-toggle">
            <label className="toggle-option">
              <input
                type="radio"
                checked={!useCustomLabel}
                onChange={() => setUseCustomLabel(false)}
                disabled={isLoading}
              />
              <span>Existing</span>
            </label>
            <label className="toggle-option">
              <input
                type="radio"
                checked={useCustomLabel}
                onChange={() => setUseCustomLabel(true)}
                disabled={isLoading}
              />
              <span>Custom</span>
            </label>
          </div>
        )}

        {!useCustomLabel && hasAvailableLabels ? (
          <select
            id="node-label"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            disabled={isLoading}
            required
            className="select-input"
          >
            <option value="">Select a label...</option>
            {availableLabels.map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>
        ) : (
          <input
            id="node-label"
            type="text"
            value={customLabel}
            onChange={(e) => setCustomLabel(e.target.value)}
            placeholder="Person, Company, Product..."
            disabled={isLoading}
            required
          />
        )}
      </div>

      <div className="form-group">
        <div className="properties-header">
          <label>Properties</label>
          <button
            type="button"
            onClick={addProperty}
            disabled={isLoading}
            className="btn-add-property"
            title="Add property"
          >
            + Add
          </button>
        </div>

        <div className="properties-list">
          {properties.map((prop, index) => (
            <div key={prop.id} className="property-row">
              <input
                type="text"
                value={prop.key}
                onChange={(e) => updateProperty(prop.id, 'key', e.target.value)}
                placeholder="Key"
                disabled={isLoading}
                className="property-key"
              />
              
              <select
                value={prop.type}
                onChange={(e) => updateProperty(prop.id, 'type', e.target.value)}
                disabled={isLoading}
                className="property-type"
              >
                <option value="string">Text</option>
                <option value="number">Number</option>
                <option value="boolean">Boolean</option>
              </select>

              {prop.type === 'boolean' ? (
                <select
                  value={prop.value}
                  onChange={(e) => updateProperty(prop.id, 'value', e.target.value)}
                  disabled={isLoading}
                  className="property-value"
                >
                  <option value="">Select...</option>
                  <option value="true">True</option>
                  <option value="false">False</option>
                </select>
              ) : (
                <input
                  type={prop.type === 'number' ? 'number' : 'text'}
                  value={prop.value}
                  onChange={(e) => updateProperty(prop.id, 'value', e.target.value)}
                  placeholder="Value"
                  disabled={isLoading}
                  className="property-value"
                  step={prop.type === 'number' ? 'any' : undefined}
                />
              )}

              {properties.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeProperty(prop.id)}
                  disabled={isLoading}
                  className="btn-remove-property"
                  title="Remove property"
                >
                  ×
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      <button type="submit" disabled={isLoading} className="btn-primary">
        {isLoading ? 'Creating...' : 'Create Node'}
      </button>
    </form>
  );
};

