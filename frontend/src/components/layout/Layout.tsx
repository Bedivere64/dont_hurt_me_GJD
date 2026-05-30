import { Outlet, NavLink } from 'react-router-dom'
import { LayoutDashboard, BarChart3, GitCompare, TrendingUp } from 'lucide-react'
import './Layout.css'

export default function Layout() {
  return (
    <div className="layout">
      <nav className="sidebar">
        <div className="logo">
          <TrendingUp className="logo-icon" size={28} />
          <span>ETF 分析</span>
        </div>
        <div className="nav-links">
          <NavLink to="/" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            <LayoutDashboard size={20} />
            <span>首页</span>
          </NavLink>
          <NavLink to="/ranking" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            <BarChart3 size={20} />
            <span>排行榜</span>
          </NavLink>
          <NavLink to="/compare" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            <GitCompare size={20} />
            <span>对比分析</span>
          </NavLink>
        </div>
        <div className="sidebar-footer">
          <span className="version">v1.0.0</span>
        </div>
      </nav>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
