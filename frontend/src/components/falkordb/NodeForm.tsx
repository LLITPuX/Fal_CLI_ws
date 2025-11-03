/**
 * Form for creating nodes in FalkorDB
 */

import { useState } from 'react';
import type { CreateNodeRequest, NodeProperties } from '../../types/falkordb';

interface NodeFormProps {
  onSubmit: (request: CreateNodeRequest) => Promise<void>;
  isLoading: boolean;
}

export const NodeForm = ({ onSubmit, isLoading }: NodeFormProps) => {
  const [label, setLabel] = useState('');
  const [properties, setProperties] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!label.trim()) {
      alert('Label is required');
      return;
    }

    let parsedProperties: NodeProperties = {};
    
    if (properties.trim()) {
      try {
        parsedProperties = JSON.parse(properties);
      } catch (error) {
        alert('Invalid JSON in properties field');
        return;
      }
    }

    await onSubmit({
      label: label.trim(),
      properties: parsedProperties,
    });

    // Reset form
    setLabel('');
    setProperties('');
  };

  return (
    <form onSubmit={handleSubmit} className="falkordb-form">
      <h3>📍 Create Node</h3>
      
      <div className="form-group">
        <label htmlFor="node-label">Label *</label>
        <input
          id="node-label"
          type="text"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          placeholder="Person, Company, Product..."
          disabled={isLoading}
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="node-properties">Properties (JSON)</label>
        <textarea
          id="node-properties"
          value={properties}
          onChange={(e) => setProperties(e.target.value)}
          placeholder='{"name": "John", "age": 30}'
          rows={4}
          disabled={isLoading}
        />
      </div>

      <button type="submit" disabled={isLoading} className="btn-primary">
        {isLoading ? 'Creating...' : 'Create Node'}
      </button>
    </form>
  );
};

