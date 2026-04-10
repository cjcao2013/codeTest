import React from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'
import { App } from './App'
import { AssessPage } from './pages/AssessPage'
import { MigratePage } from './pages/MigratePage'
import { HistoryPage } from './pages/HistoryPage'
import './index.css'

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { index: true, element: <Navigate to="/assess" replace /> },
      { path: 'assess', element: <AssessPage /> },
      { path: 'migrate', element: <MigratePage /> },
      { path: 'history', element: <HistoryPage /> },
    ],
  },
])

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>
)
