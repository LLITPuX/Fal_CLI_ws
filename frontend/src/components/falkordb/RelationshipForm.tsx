/**
 * Form for creating relationships in FalkorDB
 */

import { useState } from 'react';
import type { CreateRelationshipRequest, NodeProperties } from '../../types/falkordb';

interface RelationshipFormProps {
  onSubmit: (request: CreateRelationshipRequest) => Promise<void>;
  isLoading: boolean;
}

export const RelationshipForm = ({ onSubmit, isLoading }: RelationshipFormProps) => {
  const [fromLabel, setFromLabel] = useState('');
  const [fromProperties, setFromProperties] = useState('');
  const [toLabel, setToLabel] = useState('');
  const [toProperties, setToProperties] = useState('');
  const [relationshipType, setRelationshipType] = useState('');
  const [relationshipProperties, setRelationshipProperties] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!fromLabel.trim() || !toLabel.trim() || !relationshipType.trim()) {
      alert('From label, To label, and Relationship type are required');
      return;
    }

    let parsedFromProps: NodeProperties = {};
    let parsedToProps: NodeProperties = {};
    let parsedRelProps: NodeProperties = {};

    try {
      if (fromProperties.trim()) {
        parsedFromProps = JSON.parse(fromProperties);
      }
      if (toProperties.trim()) {
        parsedToProps = JSON.parse(toProperties);
      }
      if (relationshipProperties.trim()) {
        parsedRelProps = JSON.parse(relationshipProperties);
      }
    } catch (error) {
      alert('Invalid JSON in one of the properties fields');
      return;
    }

    await onSubmit({
      from_label: fromLabel.trim(),
      from_properties: parsedFromProps,
      to_label: toLabel.trim(),
      to_properties: parsedToProps,
      relationship_type: relationshipType.trim().toUpperCase(),
      relationship_properties: parsedRelProps,
    });

    // Reset form
    setFromLabel('');
    setFromProperties('');
    setToLabel('');
    setToProperties('');
    setRelationshipType('');
    setRelationshipProperties('');
  };

  return (
    <form onSubmit={handleSubmit} className="falkordb-form">
      <h3>🔗 Create Relationship</h3>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="from-label">From Label *</label>
          <input
            id="from-label"
            type="text"
            value={fromLabel}
            onChange={(e) => setFromLabel(e.target.value)}
            placeholder="Person"
            disabled={isLoading}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="from-props">From Properties (JSON)</label>
          <textarea
            id="from-props"
            value={fromProperties}
            onChange={(e) => setFromProperties(e.target.value)}
            placeholder='{"name": "John"}'
            rows={2}
            disabled={isLoading}
          />
        </div>
      </div>

      <div className="relationship-arrow">↓</div>

      <div className="form-group">
        <label htmlFor="rel-type">Relationship Type *</label>
        <input
          id="rel-type"
          type="text"
          value={relationshipType}
          onChange={(e) => setRelationshipType(e.target.value)}
          placeholder="KNOWS, WORKS_AT, OWNS..."
          disabled={isLoading}
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="rel-props">Relationship Properties (JSON)</label>
        <textarea
          id="rel-props"
          value={relationshipProperties}
          onChange={(e) => setRelationshipProperties(e.target.value)}
          placeholder='{"since": 2020}'
          rows={2}
          disabled={isLoading}
        />
      </div>

      <div className="relationship-arrow">↓</div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="to-label">To Label *</label>
          <input
            id="to-label"
            type="text"
            value={toLabel}
            onChange={(e) => setToLabel(e.target.value)}
            placeholder="Company"
            disabled={isLoading}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="to-props">To Properties (JSON)</label>
          <textarea
            id="to-props"
            value={toProperties}
            onChange={(e) => setToProperties(e.target.value)}
            placeholder='{"name": "ACME Corp"}'
            rows={2}
            disabled={isLoading}
          />
        </div>
      </div>

      <button type="submit" disabled={isLoading} className="btn-primary">
        {isLoading ? 'Creating...' : 'Create Relationship'}
      </button>
    </form>
  );
};

