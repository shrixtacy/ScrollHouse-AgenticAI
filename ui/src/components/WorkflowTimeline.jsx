"use client";
import React from 'react';

const STEPS = [
  { id: 'validate_input', label: '1. Validate Input' },
  { id: 'duplicate_check', label: '2. Duplicate Check' },
  { id: 'send_welcome_email', label: '3. Send Welcome Email' },
  { id: 'create_drive_folder', label: '4. Create Drive Folder' },
  { id: 'set_drive_permissions', label: '5. Set Drive Permissions' },
  { id: 'create_notion_hub', label: '6. Create Notion Hub' },
  { id: 'add_airtable_record', label: '7. Add Airtable Record' },
  { id: 'send_completion_summary', label: '8. Send Completion Email' },
  { id: 'log_onboarding', label: '9. Log Onboarding' },
];

export default function WorkflowTimeline({ completedSteps, isSimulating }) {
  return (
    <div className="glass-panel" style={{ padding: '2rem', height: '100%' }}>
      <h3 style={{ marginBottom: '1.5rem', color: 'var(--text-main)', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem' }}>
        Live Agent Workflow
        {isSimulating && <span style={{ marginLeft: '10px', fontSize: '0.8rem', color: 'var(--accent-color)' }} className="animate-pulse">Processing...</span>}
      </h3>
      
      <div className="timeline" style={{ paddingLeft: '1rem' }}>
        {STEPS.map((step, index) => {
          const isCompleted = completedSteps?.includes(step.id);
          const allCompletedBefore = index === 0 ? true : completedSteps?.includes(STEPS[index-1].id);
          const isActive = isSimulating && !isCompleted && allCompletedBefore;

          let className = "timeline-item animate-slide-up";
          if (isCompleted) className += " completed";
          if (isActive) className += " active";

          return (
            <div key={step.id} className={className} style={{ animationDelay: `${index * 80}ms` }}>
              <div className="timeline-dot"></div>
              {index < STEPS.length - 1 && <div className="timeline-line"></div>}
              <div>
                <strong style={{ color: isCompleted ? 'var(--success)' : isActive ? 'var(--accent-color)' : 'var(--text-muted)', transition: 'color 0.3s ease' }}>
                  {step.label}
                </strong>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
