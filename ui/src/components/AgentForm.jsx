"use client";
import React, { useState } from 'react';

export default function AgentForm({ onSubmit, loading }) {
  const [formData, setFormData] = useState({
    brand_name: '',
    account_manager: '',
    brand_category: '',
    contract_start_date: '',
    deliverable_count: 8,
    billing_contact_email: '',
    invoice_cycle: 'monthly'
  });

  const handleDemoFill = () => {
    setFormData({
      brand_name: "Luminos Skincare",
      account_manager: "Priya Sharma",
      brand_category: "Skincare",
      contract_start_date: "2026-05-10",
      deliverable_count: 8,
      billing_contact_email: "accounts@luminos.com",
      invoice_cycle: "monthly"
    });
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: name === 'deliverable_count' ? parseInt(value) || 0 : value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="glass-panel" style={{ padding: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2 style={{ margin: 0 }} className="gradient-text">New Client Onboarding</h2>
        <button type="button" onClick={handleDemoFill} className="btn btn-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}>
          Demo Data
        </button>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">Brand Name</label>
          <input required type="text" name="brand_name" value={formData.brand_name} onChange={handleChange} className="form-input" placeholder="e.g. Luminos Skincare" />
        </div>
        <div className="form-group">
          <label className="form-label">Account Manager</label>
          <input required type="text" name="account_manager" value={formData.account_manager} onChange={handleChange} className="form-input" placeholder="e.g. Priya Sharma" />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div className="form-group">
            <label className="form-label">Category</label>
            <input required type="text" name="brand_category" value={formData.brand_category} onChange={handleChange} className="form-input" placeholder="Skincare" />
          </div>
          <div className="form-group">
            <label className="form-label">Start Date</label>
            <input required type="date" name="contract_start_date" value={formData.contract_start_date} onChange={handleChange} className="form-input" />
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div className="form-group">
            <label className="form-label">Deliverables / Mo</label>
            <input required type="number" name="deliverable_count" value={formData.deliverable_count} onChange={handleChange} className="form-input" min="1" />
          </div>
          <div className="form-group">
            <label className="form-label">Invoice Cycle</label>
            <select required name="invoice_cycle" value={formData.invoice_cycle} onChange={handleChange} className="form-input">
              <option value="monthly">Monthly</option>
              <option value="quarterly">Quarterly</option>
            </select>
          </div>
        </div>
        <div className="form-group">
          <label className="form-label">Billing Contact Email</label>
          <input required type="email" name="billing_contact_email" value={formData.billing_contact_email} onChange={handleChange} className="form-input" placeholder="billing@client.com" />
        </div>

        <button type="submit" disabled={loading} className="btn btn-primary" style={{ width: '100%', marginTop: '1rem' }}>
          {loading ? 'Initializing Agent...' : 'Trigger Onboarding Agent'}
        </button>
      </form>
    </div>
  );
}
