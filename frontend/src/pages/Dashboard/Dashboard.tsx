import { useQuery } from '@tanstack/react-query'
import { getETFRanking } from '../../services/api'
import { TrendingUp, TrendingDown, Activity, BarChart3 } from 'lucide-react'
import { AreaChart, Area, ResponsiveContainer } from 'recharts'
import { useNavigate } from 'react-router-dom'
import './Dashboard.css'

export default function Dashboard() {
  const navigate = useNavigate()
  const { data: ranking } = useQuery({
    queryKey: ['ranking'],
    queryFn: () => getETFRanking('tot_vol', 10),
  })

  return (
    <div className="dashboard">
      <div className="page-header">
        <h1>ETF 份额概览</h1>
        <span className="update-time">实时数据</span>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon blue"><Activity size={24} /></div>
          <div className="stat-info">
            <span className="stat-label">监控ETF</span>
            <span className="stat-value">{ranking?.length || 0}</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon green"><TrendingUp size={24} /></div>
          <div className="stat-info">
            <span className="stat-label">份额增长</span>
            <span className="stat-value positive">+2.34%</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon purple"><BarChart3 size={24} /></div>
          <div className="stat-info">
            <span className="stat-label">总ETF数量</span>
            <span className="stat-value">869</span>
          </div>
        </div>
      </div>

      <div className="section">
        <h2>份额排行 TOP 10</h2>
        <div className="ranking-table">
          <table>
            <thead>
              <tr>
                <th>排名</th>
                <th>代码</th>
                <th>名称</th>
                <th>总份额(万)</th>
                <th>最新日期</th>
              </tr>
            </thead>
            <tbody>
              {ranking?.map((item: any, index: number) => (
                <tr key={item.sec_code} onClick={() => navigate(`/trend/${item.sec_code}`)}>
                  <td><span className="rank-badge">{index + 1}</span></td>
                  <td className="code">{item.sec_code}</td>
                  <td className="name">{item.sec_name}</td>
                  <td className="volume">{(item.tot_vol / 10000).toFixed(2)}亿</td>
                  <td className="date">{item.stat_date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
