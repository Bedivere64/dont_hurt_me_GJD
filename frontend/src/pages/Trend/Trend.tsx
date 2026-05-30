import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getETFTrend } from '../../services/api'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import './Trend.css'

export default function Trend() {
  const { code } = useParams<{ code: string }>()
  const { data, isLoading } = useQuery({
    queryKey: ['trend', code],
    queryFn: () => getETFTrend(code!, 30),
    enabled: !!code,
  })

  if (isLoading) return <div className="loading">加载中...</div>

  return (
    <div className="trend-page">
      <h1>ETF {code} 份额趋势</h1>
      <div className="chart-container">
        <ResponsiveContainer width="100%" height={400}>
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorVol" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#00D4FF" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#00D4FF" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <XAxis dataKey="date" tick={{ fontSize: 12, stroke: '#8892b0' }} />
            <YAxis tick={{ fontSize: 12, stroke: '#8892b0' }} />
            <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(0,212,255,0.3)', borderRadius: '8px' }} />
            <Area type="monotone" dataKey="tot_vol" stroke="#00D4FF" fillOpacity={1} fill="url(#colorVol)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <div className="data-table">
        <table>
          <thead>
            <tr>
              <th>日期</th>
              <th>总份额(万)</th>
              <th>收盘价</th>
            </tr>
          </thead>
          <tbody>
            {data?.slice().reverse().map((item: any) => (
              <tr key={item.date}>
                <td>{item.date}</td>
                <td>{item.tot_vol?.toFixed(2)}</td>
                <td>{item.close_price?.toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
