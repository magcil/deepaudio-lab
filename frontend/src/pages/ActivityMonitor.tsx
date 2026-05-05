import { useEffect, useState } from 'react';
import { getActiveTasks } from '../services/taskService';
import type { ActiveTask } from '../services/taskService';
import { BASE_URL } from '../api/client';
const TERMINAL_STATES = new Set(['SUCCESS', 'FAILURE', 'REVOKED']);

function progressUrl(task: ActiveTask): string {
  const prefix = task.task_type === 'train' ? 'train' : 'evaluate';
  return `${BASE_URL}/${prefix}/progress/${task.task_id}`;
}

function formatSeconds(s: number): string {
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return m > 0 ? `${m}m ${sec}s` : `${sec}s`;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  const month = d.toLocaleString('en-US', { month: 'short' });
  const day = String(d.getDate()).padStart(2, '0');
  const time = d.toTimeString().slice(0, 8);
  return `${month} ${day}  ${time}`;
}

function formatLoss(v: unknown): string {
  return typeof v === 'number' ? v.toFixed(4) : '–';
}

type StatusConfig = { dot: string; label: string; color: string };

const STATUS_MAP: Record<string, StatusConfig> = {
  PROGRESS: { dot: '●', label: 'In Progress', color: '#4a9eff' },
  STARTED:  { dot: '●', label: 'In Progress', color: '#4a9eff' },
  PENDING:  { dot: '●', label: 'Pending',     color: '#f0b429' },
  SUCCESS:  { dot: '✓', label: 'Completed',   color: '#3ecf8e' },
  FAILURE:  { dot: '●', label: 'Failure',      color: '#f56565' },
};

function StatusCell({ state }: { state: string }) {
  const cfg = STATUS_MAP[state] ?? { dot: '●', label: state, color: '#9fb5d1' };
  return (
    <span className="am-status">
      <span style={{ color: cfg.color }}>{cfg.dot}</span>
      {' '}{cfg.label}
    </span>
  );
}

function ProgressBar({ pct }: { pct: number }) {
  return (
    <span className="am-progress-wrap">
      <span className="am-progress-track">
        <span className="am-progress-fill" style={{ width: `${pct}%` }} />
      </span>
      <span className="am-progress-pct">{pct.toFixed(1)}%</span>
    </span>
  );
}

function TaskRow({ task }: { task: ActiveTask }) {
  const info = task.info as Record<string, unknown> | null;
  const progress = typeof info?.progress === 'number' ? info.progress : 0;

  return (
    <tr className="am-row">
      <td><StatusCell state={task.state} /></td>
      <td className="am-mono">{formatDate(task.created_at)}</td>
      <td className="am-experiment">{task.experiment_name}</td>
      <td><ProgressBar pct={progress} /></td>
      <td className="am-mono am-num">{formatLoss(info?.train_loss)}</td>
      <td className="am-mono am-num">{formatLoss(info?.val_loss)}</td>
      <td className="am-mono am-num">{formatLoss(info?.best_val_loss)}</td>
      <td className="am-mono am-num">
        {typeof info?.elapsed_seconds === 'number' ? formatSeconds(info.elapsed_seconds) : '–'}
      </td>
      <td className="am-mono am-num">
        {typeof info?.eta_seconds === 'number' ? formatSeconds(info.eta_seconds) : '–'}
      </td>
    </tr>
  );
}

export default function ActivityMonitor() {
  const [tasks, setTasks] = useState<ActiveTask[]>([]);

  useEffect(() => {
    let sources: EventSource[] = [];

    getActiveTasks().then((fetched) => {
      console.log('Active tasks:', fetched);
      setTasks(fetched);

      sources = fetched.map((task) => {
        const es = new EventSource(progressUrl(task));

        es.onmessage = (event) => {
          const update = JSON.parse(event.data) as {
            state: string;
            info: Record<string, unknown> | null;
          };
          console.log(`[${task.task_id}] progress update:`, update);
          setTasks((prev) =>
            prev.map((t) =>
              t.task_id === task.task_id
                ? { ...t, state: update.state as ActiveTask['state'], info: update.info }
                : t
            )
          );
          if (TERMINAL_STATES.has(update.state)) es.close();
        };

        es.onerror = () => es.close();
        return es;
      });
    });

    return () => sources.forEach((es) => es.close());
  }, []);

  return (
    <div className="page-content">
      <p className="eyebrow">Deep Audio Lab</p>
      <h1 className="page-title">Activity Monitor</h1>
      <p className="page-summary">
        Monitor running and completed training and evaluation tasks.
      </p>

      <div className="am-wrap">
        {tasks.length === 0 ? (
          <p className="am-empty">No active tasks.</p>
        ) : (
          <table className="am-table">
            <thead>
              <tr>
                <th>Status</th>
                <th>Started</th>
                <th>Experiment</th>
                <th>Progress</th>
                <th>Train Loss</th>
                <th>Val Loss</th>
                <th>Best Val Loss</th>
                <th>Elapsed</th>
                <th>ETA</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((task) => (
                <TaskRow key={task.task_id} task={task} />
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
