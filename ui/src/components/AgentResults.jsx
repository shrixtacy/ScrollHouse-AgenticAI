"use client";
import React from 'react';

export default function AgentResults({ result }) {
  if (!result) return null;
  const isError = result.status === 'halted' || result.status === 'completed_with_errors' || result.errors?.length > 0;

  return (
    <div className="glass-panel" style={{ padding: '2rem' }}>
      <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center' }}>
        <span style={{ 
          display: 'inline-block', width: '12px', height: '12px', 
          borderRadius: '50%', background: isError ? 'var(--error)' : 'var(--success)', 
          marginRight: '10px', boxShadow: `0 0 10px ${isError ? 'var(--error)' : 'var(--success)'}`
        }}></span>
        Run Results 
        <span style={{ marginLeft: 'auto', fontSize: '0.8rem', color: isError ? 'var(--error)' : 'var(--success)', fontWeight: 'bold' }}>
          {result.status?.toUpperCase() || 'UNKNOWN'}
        </span>
      </h3>

      {isError && result.errors && result.errors.length > 0 && (
        <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--error)', padding: '1rem', borderRadius: '12px', marginBottom: '1.5rem', color: 'var(--error)', fontSize: '0.9rem' }}>
          <strong>Errors Detected:</strong>
          <ul style={{ marginLeft: '1.5rem', marginTop: '0.5rem' }}>
            {result.errors.map((err, i) => (
              <li key={i} style={{ marginBottom: '0.25rem' }}>
                {typeof err === 'object' ? (
                  <>
                    {err.step && <strong>[{err.step.replace(/_/g, ' ')}] </strong>}
                    {err.error || err.message || JSON.stringify(err)}
                    {err.action_taken && <span style={{ opacity: 0.8, marginLeft: '0.5rem' }}>({err.action_taken})</span>}
                  </>
                ) : (
                  String(err)
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {result.flags && result.flags.length > 0 && (
        <div style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid #f59e0b', padding: '1rem', borderRadius: '12px', marginBottom: '1.5rem', color: '#fcd34d', fontSize: '0.9rem' }}>
          <strong>Flags / Warnings:</strong>
          <ul style={{ marginLeft: '1.5rem', marginTop: '0.5rem' }}>
            {result.flags.map((flag, i) => <li key={i}>{flag}</li>)}
          </ul>
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {result.drive_folder_link && (
          <a href={result.drive_folder_link} target="_blank" rel="noopener noreferrer" className="result-card">
            <div className="result-icon" style={{ color: '#4285F4' }}>📁</div>
            <div>
              <div style={{ fontWeight: '600', fontSize: '0.95rem' }}>Google Drive Workspace</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Client Assets & Deliverables</div>
            </div>
          </a>
        )}

        {result.notion_page_link && (
          <a href={result.notion_page_link} target="_blank" rel="noopener noreferrer" className="result-card">
            <div className="result-icon" style={{ color: '#EAEAEA' }}>📝</div>
            <div>
              <div style={{ fontWeight: '600', fontSize: '0.95rem' }}>Notion Client Hub</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Project Management & Briefs</div>
            </div>
          </a>
        )}

        {result.airtable_record_link && (
          <a href={result.airtable_record_link} target="_blank" rel="noopener noreferrer" className="result-card">
            <div className="result-icon" style={{ color: '#F82B60' }}>📊</div>
            <div>
              <div style={{ fontWeight: '600', fontSize: '0.95rem' }}>Airtable CRM Record</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Master Client Database</div>
            </div>
          </a>
        )}

        {!result.drive_folder_link && !result.notion_page_link && !result.airtable_record_link && !isError && (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.9rem', padding: '1rem' }}>
            No assets generated in this run.
          </div>
        )}
      </div>
    </div>
  );
}
