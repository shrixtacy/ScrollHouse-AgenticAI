"use client";
import React, { useState, useEffect } from 'react';
import AgentForm from '../components/AgentForm';
import WorkflowTimeline from '../components/WorkflowTimeline';
import AgentResults from '../components/AgentResults';

const ALL_STEPS = [
  'validate_input', 'duplicate_check', 'send_welcome_email',
  'create_drive_folder', 'set_drive_permissions', 'create_notion_hub',
  'add_airtable_record', 'send_completion_summary', 'log_onboarding'
];

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [simulatedSteps, setSimulatedSteps] = useState([]);
  const [backendStatus, setBackendStatus] = useState('checking'); // 'checking' | 'online' | 'offline'

  // Check backend health on mount
  useEffect(() => {
    fetch('/api/onboard')
      .then(r => r.json())
      .then(d => setBackendStatus(d.status === 'ok' ? 'online' : 'offline'))
      .catch(() => setBackendStatus('offline'));
  }, []);

  // Simulate step progression while loading
  useEffect(() => {
    let timer;
    if (loading && simulatedSteps.length < ALL_STEPS.length) {
      timer = setTimeout(() => {
        setSimulatedSteps(prev => {
          if (prev.length < ALL_STEPS.length) {
            return [...prev, ALL_STEPS[prev.length]];
          }
          return prev;
        });
      }, 1800);
    }
    return () => clearTimeout(timer);
  }, [loading, simulatedSteps]);

  const handleSubmit = async (data) => {
    setLoading(true);
    setResult(null);
    setSimulatedSteps(['validate_input']);

    try {
      const res = await fetch('/api/onboard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      const json = await res.json();
      setResult(json);
    } catch (err) {
      console.error(err);
      setResult({
        status: 'error',
        errors: [{ step: 'connection', error: err.message || 'Failed to connect to agent server' }],
      });
    } finally {
      setLoading(false);
    }
  };

  const stepsToDisplay = loading ? simulatedSteps : (result?.completed_steps || []);

  return (
    <main style={{ padding: '3rem 1.5rem', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: '3rem' }} className="animate-fade-in">
        <h1 className="gradient-text" style={{ fontSize: '3rem', marginBottom: '0.5rem', letterSpacing: '-0.03em' }}>
          Scrollhouse Onboarding
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem' }}>PS-01 Multi-Agent Workflow Engine</p>

        {/* Backend status badge */}
        <div style={{ marginTop: '0.75rem', display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          <span style={{
            width: 8, height: 8, borderRadius: '50%',
            background: backendStatus === 'online' ? 'var(--success)' : backendStatus === 'offline' ? 'var(--error)' : '#f59e0b',
            display: 'inline-block',
            boxShadow: backendStatus === 'online' ? '0 0 6px var(--success)' : 'none',
          }} />
          Agent {backendStatus === 'checking' ? 'connecting...' : backendStatus}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '2rem', alignItems: 'start' }}>
        <div className="animate-slide-up">
          <AgentForm onSubmit={handleSubmit} loading={loading} />

          {result && !loading && (
            <div style={{ marginTop: '2rem' }} className="animate-fade-in delay-200">
              <AgentResults result={result} />
            </div>
          )}
        </div>

        <div className="animate-slide-up delay-100" style={{ position: 'sticky', top: '2rem' }}>
          <WorkflowTimeline completedSteps={stepsToDisplay} isSimulating={loading} />
        </div>
      </div>
    </main>
  );
}
