import { NavLink, Outlet } from 'react-router-dom'
import { cn } from '@/lib/utils'

const navItems = [
  { to: '/assess', label: 'Assess' },
  { to: '/migrate', label: 'Migrate' },
  { to: '/history', label: 'History' },
]

export function App() {
  return (
    <div className="min-h-screen bg-zinc-50">
      <header className="border-b bg-white px-6 py-3 flex items-center gap-6">
        <span className="font-bold text-zinc-800">TAP Migration Demo</span>
        <nav className="flex gap-4">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn('text-sm', isActive ? 'text-zinc-900 font-medium' : 'text-zinc-500 hover:text-zinc-800')
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="p-6">
        <Outlet />
      </main>
    </div>
  )
}
