import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import type { Loss } from '../services/runService'

interface Props {
  losses: Loss[]
}

interface ChartPoint {
  epoch: number
  train?: number
  validation?: number
}

export default function LossCharts({ losses }: Props) {
  if (losses.length === 0) return null

  const byEpoch = losses.reduce<Record<number, ChartPoint>>((acc, l) => {
    if (!acc[l.epoch]) acc[l.epoch] = { epoch: l.epoch }
    acc[l.epoch][l.split_type] = l.loss
    return acc
  }, {})

  const data = Object.values(byEpoch).sort((a, b) => a.epoch - b.epoch)

  const hasTrain = data.some((d) => d.train !== undefined)
  const hasValidation = data.some((d) => d.validation !== undefined)

  return (
    <section className="experiments-section">
      <h2 className="section-heading">Loss Curves</h2>
      <div className="loss-chart">
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={data} margin={{ top: 8, right: 24, left: 0, bottom: 24 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis
              dataKey="epoch"
              tick={{ fill: '#9fb5d1', fontSize: 11 }}
              tickLine={false}
              label={{ value: 'Epoch', position: 'insideBottom', offset: -12, fill: '#9fb5d1', fontSize: 12 }}
            />
            <YAxis
              tick={{ fill: '#9fb5d1', fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              width={48}
            />
            <Tooltip
              contentStyle={{
                background: 'rgba(15, 23, 42, 0.95)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 8,
                fontSize: 12,
                color: '#e5ecf6',
              }}
              labelFormatter={(v) => `Epoch ${v}`}
              formatter={(v, name) => [typeof v === 'number' ? v.toFixed(4) : String(v), String(name).charAt(0).toUpperCase() + String(name).slice(1)]}
            />
            <Legend
              verticalAlign="top"
              align="right"
              wrapperStyle={{ fontSize: 12, color: '#9fb5d1', paddingBottom: 8 }}
              formatter={(value) => value.charAt(0).toUpperCase() + value.slice(1)}
            />
            {hasTrain && (
              <Line type="monotone" dataKey="train" stroke="#63b3ed" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
            )}
            {hasValidation && (
              <Line type="monotone" dataKey="validation" stroke="#9a75ea" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}
