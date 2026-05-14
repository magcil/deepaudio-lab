import { useEffect, useState } from 'react';
import { getActiveTasks } from '../services/taskService';
import type { ActiveTask } from '../services/taskService';

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
      <td className="am-mono">{task.task_type}</td>
      <td><ProgressBar pct={progress} /></td>
      <td className="am-mono am-num">{formatLoss(info?.train_loss)}</td>
      <td className="am-mono am-num">{formatLoss(info?.val_loss)}</td>
      <td className="am-mono am-num">{formatLoss(info?.best_val_loss)}</td>
      <td className="am-mono am-num">
        {task.task_type === 'train' && typeof info?.current_patience === 'number' && typeof info?.total_patience === 'number'
          ? `${info.current_patience}/${info.total_patience}`
          : '–'}
      </td>
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
  const [loading, setLoading] = useState(false);

  async function fetchTasks() {
    setLoading(true);
    try {
      const fetched = await getActiveTasks();
      setTasks(fetched);
    } catch {
      // keep previous state on error
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { fetchTasks(); }, []);

  return (
    <div className="page-content">
      <p className="eyebrow">Deep Audio Lab</p>
      <h1 className="page-title">Activity Monitor</h1>
      <p className="page-summary">
        Monitor running and completed training and evaluation tasks.
      </p>

      <div className="am-toolbar">
        <button className="am-refresh-btn" onClick={fetchTasks} disabled={loading}>
          {loading ? 'Loading…' : 'Refresh Results'}
        </button>
      </div>

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
                <th>Type</th>
                <th>Progress</th>
                <th>Train Loss</th>
                <th>Val Loss</th>
                <th>Best Val Loss</th>
                <th>Patience</th>
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
