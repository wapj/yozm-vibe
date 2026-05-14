import styles from './DashboardGrid.module.css'
import ClockWidget from '../widgets/clock/ClockWidget'
import WeatherWidget from '../widgets/weather/WeatherWidget'
import ScheduleWidget from '../widgets/schedule/ScheduleWidget'
import MemoWidget from '../widgets/memo/MemoWidget'
import ExchangeWidget from '../widgets/exchange/ExchangeWidget'
import QuoteWidget from '../widgets/quote/QuoteWidget'
import LinksWidget from '../widgets/links/LinksWidget'

export default function DashboardGrid() {
  return (
    <div className={styles.grid}>
      {/* Row 1 */}
      <ClockWidget />
      <WeatherWidget />
      <ScheduleWidget />
      <MemoWidget />
      {/* Row 2 */}
      <ExchangeWidget />
      <QuoteWidget />
      <LinksWidget />
      <div />
    </div>
  )
}
