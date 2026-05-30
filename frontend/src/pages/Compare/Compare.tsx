import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { compareETF } from '../../services/api'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import './Compare.css'

const COLORS = ['#00D4FF', '#7B2CBF', '#34C759', '#FF9500', '#FF3B30']

export default function Compare() {
  const [codes, setCodes] = useState<string[]>(['512880', '510300'])
  const [input, setInput] = useState('')
  const { data } = useQuery({
    queryKey: ['compare', codes],
    queryFn: () => compareETF(codes),
    enabled: codes.length >= 2,
  })

  const addCode = () => {
    if (input && !codes.includes(input)) {
      setCodes([...codes, input])
      setInput('')
    }
  }

  return (
    <div className="compare-page">
      <h1>ETF 对比分析</h1>
      <div className="compare-input">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="输入ETF代码，如 512880"
          onKeyDown={(e) => e.key === 'Enter' && addCode()}
        />
        <button onClick={addCode}>添加</button>
      </div>
      <div className="code-tags">
        {codes.map((code, i) => (
          <span key={code} className="tag" style={{ background: COLORS[i % COLORS.length] + '20', color: COLORS[i % COLORS.length] }}>
            {code}
            <button onClick={() => setCodes(codes.filter(c => c !== code))}>×</button>
          </span>
        ))}
      </div>
      <div className="compare-chart">
        <ResponsiveContainer width="100%" height={400}>
          <LineChart>
            <XAxis dataKey="date" tick={{ fontSize: 12, stroke: '#8892b0' }} />
            <YAxis tick={{ fontSize: 12, stroke: '#8892b0' }} />
            <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(0,212,255,0.3)', borderRadius: '8px' }} />
            <Legend />
            {codes.map((code, i) => (
              <Line key={code} type="monotone" dataKey="tot_vol" data={data?.[code]} name={code} stroke={COLORS[i % COLORS.length]} strokeWidth={2} dot={false} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
