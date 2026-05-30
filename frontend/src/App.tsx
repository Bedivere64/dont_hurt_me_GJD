import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard/Dashboard'
import Ranking from './pages/Ranking/Ranking'
import Trend from './pages/Trend/Trend'
import Compare from './pages/Compare/Compare'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="ranking" element={<Ranking />} />
            <Route path="trend/:code" element={<Trend />} />
            <Route path="compare" element={<Compare />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
