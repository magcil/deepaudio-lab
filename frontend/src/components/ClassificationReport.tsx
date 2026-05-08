import './ClassificationReport.css'

const SUMMARY_KEYS = ['accuracy', 'macro avg', 'weighted avg']

type ReportRow = { precision: number; recall: number; 'f1-score': number; support: number }

interface Props {
  report: Record<string, unknown>
}

export default function ClassificationReport({ report }: Props) {
  const classKeys = Object.keys(report).filter(k => !SUMMARY_KEYS.includes(k))

  function fmt(val: unknown) {
    return typeof val === 'number' ? val.toFixed(2) : '—'
  }

  function renderRow(key: string, isSummary = false) {
    const row = report[key]
    const label = key

    if (key === 'accuracy') {
      const support = (report['macro avg'] as ReportRow | undefined)?.support
      return (
        <tr key={key} className="report-table__summary-row">
          <td className="report-table__label">{label}</td>
          <td></td>
          <td></td>
          <td>{fmt(row)}</td>
          <td>{support ?? '—'}</td>
        </tr>
      )
    }

    const r = row as ReportRow
    return (
      <tr key={key} className={isSummary ? 'report-table__summary-row' : ''}>
        <td className="report-table__label">{label}</td>
        <td>{fmt(r.precision)}</td>
        <td>{fmt(r.recall)}</td>
        <td>{fmt(r['f1-score'])}</td>
        <td>{r.support}</td>
      </tr>
    )
  }

  return (
    <div className="report-table-wrapper">
      <table className="report-table">
        <thead>
          <tr>
            <th></th>
            <th>precision</th>
            <th>recall</th>
            <th>f1-score</th>
            <th>support</th>
          </tr>
        </thead>
        <tbody>
          {classKeys.map(k => renderRow(k))}
          <tr className="report-table__divider"><td colSpan={5}></td></tr>
          {SUMMARY_KEYS.filter(k => k in report).map(k => renderRow(k, true))}
        </tbody>
      </table>
    </div>
  )
}
