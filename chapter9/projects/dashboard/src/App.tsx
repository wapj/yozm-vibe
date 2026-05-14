import DashboardGrid from './grid/DashboardGrid'
import StorageWarningBanner from './components/StorageWarningBanner'

export default function App() {
  return (
    <>
      <StorageWarningBanner />
      <DashboardGrid />
    </>
  )
}
