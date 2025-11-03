/**
 * Form for creating relationships in FalkorDB
 */

import { useState, useEffect } from 'react';
import type { CreateRelationshipRequest, NodeProperties } from '../../types/falkordb';

interface RelationshipFormProps {
  onSubmit: (request: CreateRelationshipRequest) => Promise<void>;
  isLoading: boolean;
  availableLabels?: string[];
  availableRelationshipTypes?: string[];
}

interface PropertyField {
  id: string;
  key: string;
  value: string;
  type: 'string' | 'number' | 'boolean';
}

export const RelationshipForm = ({ 
  onSubmit, 
  isLoading, 
  availableLabels = [],
  availableRelationshipTypes = []
}: RelationshipFormProps) => {
  const [fromLabel, setFromLabel] = useState('');
  const [fromCustomLabel, setFromCustomLabel] = useState('');
  const [useFromCustomLabel, setUseFromCustomLabel] = useState(false);
  
  const [toLabel, setToLabel] = useState('');
  const [toCustomLabel, setToCustomLabel] = useState('');
  const [useToCustomLabel, setUseToCustomLabel] = useState(false);
  
  const [relationshipType, setRelationshipType] = useState('');
  const [customRelType, setCustomRelType] = useState('');
  const [useCustomRelType, setUseCustomRelType] = useState(false);
  
  const [fromProperties, setFromProperties] = useState<PropertyField[]>([]);
  const [toProperties, setToProperties] = useState<PropertyField[]>([]);
  const [relationshipProperties, setRelationshipProperties] = useState<PropertyField[]>([]);

  // Initialize with one empty field for each
  useEffect(() => {
    if (fromProperties.length === 0) {
      setFromProperties([{ id: 'from-1', key: '', value: '', type: 'string' }]);
    }
    if (toProperties.length === 0) {
      setToProperties([{ id: 'to-1', key: '', value: '', type: 'string' }]);
    }
    if (relationshipProperties.length === 0) {
      setRelationshipProperties([{ id: 'rel-1', key: '', value: '', type: 'string' }]);
    }
  }, []);

  const addProperty = (setter: React.Dispatch<React.SetStateAction<PropertyField[]>>, prefix: string) => {
    setter(prev => [
      ...prev,
      { id: `${prefix}-${Date.now()}`, key: '', value: '', type: 'string' }
    ]);
  };

  const removeProperty = (setter: React.Dispatch<React.SetStateAction<PropertyField[]>>, id: string) => {
    setter(prev => prev.filter(p => p.id !== id));
  };

  const updateProperty = (
    setter: React.Dispatch<React.SetStateAction<PropertyField[]>>,
    id: string,
    field: 'key' | 'value' | 'type',
    value: string
  ) => {
    setter(prev => prev.map(p => p.id === id ? { ...p, [field]: value } : p));
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

  const buildPropertiesObject = (fields: PropertyField[]): NodeProperties => {
    const props: NodeProperties = {};
    fields.forEach(field => {
      if (field.key.trim()) {
        props[field.key.trim()] = parseValue(field.value, field.type);
      }
    });
    return props;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const finalFromLabel = useFromCustomLabel ? fromCustomLabel.trim() : fromLabel;
    const finalToLabel = useToCustomLabel ? toCustomLabel.trim() : toLabel;
    const finalRelType = useCustomRelType ? customRelType.trim().toUpperCase() : relationshipType;

    if (!finalFromLabel || !finalToLabel || !finalRelType) {
      alert('From label, To label, and Relationship type are required');
      return;
    }

    await onSubmit({
      from_label: finalFromLabel,
      from_properties: buildPropertiesObject(fromProperties),
      to_label: finalToLabel,
      to_properties: buildPropertiesObject(toProperties),
      relationship_type: finalRelType,
      relationship_properties: buildPropertiesObject(relationshipProperties),
    });

    // Reset form
    setFromLabel('');
    setFromCustomLabel('');
    setUseFromCustomLabel(false);
    setToLabel('');
    setToCustomLabel('');
    setUseToCustomLabel(false);
    setRelationshipType('');
    setCustomRelType('');
    setUseCustomRelType(false);
    setFromProperties([{ id: 'from-1', key: '', value: '', type: 'string' }]);
    setToProperties([{ id: 'to-1', key: '', value: '', type: 'string' }]);
    setRelationshipProperties([{ id: 'rel-1', key: '', value: '', type: 'string' }]);
  };

  const hasAvailableLabels = availableLabels.length > 0;
  const hasAvailableRelTypes = availableRelationshipTypes.length > 0;

  const renderPropertyFields = (
    properties: PropertyField[],
    setter: React.Dispatch<React.SetStateAction<PropertyField[]>>,
    prefix: string,
    label: string
  ) => (
    <div className="form-group">
      <div className="properties-header">
        <label>{label}</label>
        <button
          type="button"
          onClick={() => addProperty(setter, prefix)}
          disabled={isLoading}
          className="btn-add-property-small"
          title={`Add ${label.toLowerCase()}`}
        >
          +
        </button>
      </div>

      <div className="properties-list-compact">
        {properties.map((prop) => (
          <div key={prop.id} className="property-row-compact">
            <input
              type="text"
              value={prop.key}
              onChange={(e) => updateProperty(setter, prop.id, 'key', e.target.value)}
              placeholder="Key"
              disabled={isLoading}
              className="property-key"
            />
            
            <select
              value={prop.type}
              onChange={(e) => updateProperty(setter, prop.id, 'type', e.target.value)}
              disabled={isLoading}
              className="property-type-small"
            >
              <option value="string">Text</option>
              <option value="number">Num</option>
              <option value="boolean">Bool</option>
            </select>

            {prop.type === 'boolean' ? (
              <select
                value={prop.value}
                onChange={(e) => updateProperty(setter, prop.id, 'value', e.target.value)}
                disabled={isLoading}
                className="property-value"
              >
                <option value="">...</option>
                <option value="true">True</option>
                <option value="false">False</option>
              </select>
            ) : (
              <input
                type={prop.type === 'number' ? 'number' : 'text'}
                value={prop.value}
                onChange={(e) => updateProperty(setter, prop.id, 'value', e.target.value)}
                placeholder="Value"
                disabled={isLoading}
                className="property-value"
                step={prop.type === 'number' ? 'any' : undefined}
              />
            )}

            {properties.length > 1 && (
              <button
                type="button"
                onClick={() => removeProperty(setter, prop.id)}
                disabled={isLoading}
                className="btn-remove-property-small"
                title="Remove"
              >
                ×
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <form onSubmit={handleSubmit} className="falkordb-form relationship-form">
      <h3>🔗 Create Relationship</h3>

      {/* FROM Node */}
      <div className="relationship-section">
        <h4 className="section-title">📍 From Node</h4>
        
        <div className="form-group">
          <label>Label *</label>
          
          {hasAvailableLabels && (
            <div className="label-toggle">
              <label className="toggle-option">
                <input
                  type="radio"
                  checked={!useFromCustomLabel}
                  onChange={() => setUseFromCustomLabel(false)}
                  disabled={isLoading}
                />
                <span>Existing</span>
              </label>
              <label className="toggle-option">
                <input
                  type="radio"
                  checked={useFromCustomLabel}
                  onChange={() => setUseFromCustomLabel(true)}
                  disabled={isLoading}
                />
                <span>Custom</span>
              </label>
            </div>
          )}

          {!useFromCustomLabel && hasAvailableLabels ? (
            <select
              value={fromLabel}
              onChange={(e) => setFromLabel(e.target.value)}
              disabled={isLoading}
              required
              className="select-input"
            >
              <option value="">Select...</option>
              {availableLabels.map((l) => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
          ) : (
            <input
              type="text"
              value={fromCustomLabel}
              onChange={(e) => setFromCustomLabel(e.target.value)}
              placeholder="Person, Company..."
              disabled={isLoading}
              required
            />
          )}
        </div>

        {renderPropertyFields(fromProperties, setFromProperties, 'from', 'Properties')}
      </div>

      <div className="relationship-arrow">↓</div>

      {/* RELATIONSHIP */}
      <div className="relationship-section">
        <h4 className="section-title">🔗 Relationship</h4>
        
        <div className="form-group">
          <label>Type *</label>
          
          {hasAvailableRelTypes && (
            <div className="label-toggle">
              <label className="toggle-option">
                <input
                  type="radio"
                  checked={!useCustomRelType}
                  onChange={() => setUseCustomRelType(false)}
                  disabled={isLoading}
                />
                <span>Existing</span>
              </label>
              <label className="toggle-option">
                <input
                  type="radio"
                  checked={useCustomRelType}
                  onChange={() => setUseCustomRelType(true)}
                  disabled={isLoading}
                />
                <span>Custom</span>
              </label>
            </div>
          )}

          {!useCustomRelType && hasAvailableRelTypes ? (
            <select
              value={relationshipType}
              onChange={(e) => setRelationshipType(e.target.value)}
              disabled={isLoading}
              required
              className="select-input"
            >
              <option value="">Select...</option>
              {availableRelationshipTypes.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          ) : (
            <input
              type="text"
              value={customRelType}
              onChange={(e) => setCustomRelType(e.target.value)}
              placeholder="KNOWS, WORKS_AT..."
              disabled={isLoading}
              required
            />
          )}
        </div>

        {renderPropertyFields(relationshipProperties, setRelationshipProperties, 'rel', 'Properties')}
      </div>

      <div className="relationship-arrow">↓</div>

      {/* TO Node */}
      <div className="relationship-section">
        <h4 className="section-title">📍 To Node</h4>
        
        <div className="form-group">
          <label>Label *</label>
          
          {hasAvailableLabels && (
            <div className="label-toggle">
              <label className="toggle-option">
                <input
                  type="radio"
                  checked={!useToCustomLabel}
                  onChange={() => setUseToCustomLabel(false)}
                  disabled={isLoading}
                />
                <span>Existing</span>
              </label>
              <label className="toggle-option">
                <input
                  type="radio"
                  checked={useToCustomLabel}
                  onChange={() => setUseToCustomLabel(true)}
                  disabled={isLoading}
                />
                <span>Custom</span>
              </label>
            </div>
          )}

          {!useToCustomLabel && hasAvailableLabels ? (
            <select
              value={toLabel}
              onChange={(e) => setToLabel(e.target.value)}
              disabled={isLoading}
              required
              className="select-input"
            >
              <option value="">Select...</option>
              {availableLabels.map((l) => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
          ) : (
            <input
              type="text"
              value={toCustomLabel}
              onChange={(e) => setToCustomLabel(e.target.value)}
              placeholder="Person, Company..."
              disabled={isLoading}
              required
            />
          )}
        </div>

        {renderPropertyFields(toProperties, setToProperties, 'to', 'Properties')}
      </div>

      <button type="submit" disabled={isLoading} className="btn-primary">
        {isLoading ? 'Creating...' : 'Create Relationship'}
      </button>
    </form>
  );
};

