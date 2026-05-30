import { useQuery } from '@tanstack/react-query'
import { getETFRanking } from '../../services/api'
import { useNavigate } from 'react-router-dom'
import './Ranking.css'

export default function Ranking() {
  const navigate = useNavigate()
  const { data } = useQuery({
    queryKey: ['ranking'],
    queryFn: () => getETFRanking('tot_vol', 50),
  })

  return (
    <div className="ranking-page">
      <h1>ETF 份额排行榜</h1>
      <div className="ranking-grid">
        {data?.map((item: any, index: number) => (
          <div key={item.sec_code} className="ranking-card" onClick={() => navigate(`/trend/${item.sec_code}`)}>
            <div className="rank">#{index + 1}</div>
            <div className="info">
              <div className="name">{item.sec_name}</div>
              <div className="code">{item.sec_code}</div>
            </div>
            <div className="vol">{(item.tot_vol / 10000).toFixed(2)}亿</div>
          </div>
        ))}
      </div>
    </div>
  )
}
