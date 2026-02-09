import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  HomeIcon,
  ChartBarIcon,
  CircleStackIcon,
  BellAlertIcon,
  Cog6ToothIcon,
  ChevronDoubleLeftIcon,
  ChevronDoubleRightIcon,
} from '@heroicons/react/24/outline';

export const Sidebar = () => {
  const [isCollapsed, setIsCollapsed] = useState(true);
  
  const navigation = [
    { name: 'Home', href: '/', icon: HomeIcon },
    { name: 'Dashboards', href: '/dashboards', icon: ChartBarIcon },
    { name: 'Data Sources', href: '/data-sources', icon: CircleStackIcon },
    { name: 'Alerts', href: '/alerts', icon: BellAlertIcon },
    { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
  ];

  return (
    <aside className={`${isCollapsed ? 'w-20' : 'w-64'} bg-gray-900 text-white transition-all duration-300`}>
      <div className="flex items-center justify-center h-16 border-b border-gray-800">
        {!isCollapsed && <h1 className="text-xl font-bold">BI Dashboard</h1>}
        {isCollapsed && <h1 className="text-xl font-bold">BI</h1>}
      </div>

      <nav className="mt-8">
        <div className="px-2 space-y-2">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                `flex items-center ${isCollapsed ? 'justify-center px-2' : 'px-4'} py-3 text-sm font-medium rounded-lg transition ${
                  isActive
                    ? 'bg-gray-800 text-white'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }`
              }
              title={isCollapsed ? item.name : ''}
            >
              <item.icon className={`w-5 h-5 ${!isCollapsed && 'mr-3'}`} />
              {!isCollapsed && item.name}
            </NavLink>
          ))}
        </div>
      </nav>

      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="absolute bottom-8 left-4 p-2 rounded-lg bg-gray-800 hover:bg-gray-700 transition"
        title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {isCollapsed ? (
          <ChevronDoubleRightIcon className="w-5 h-5" />
        ) : (
          <ChevronDoubleLeftIcon className="w-5 h-5" />
        )}
      </button>
    </aside>
  );
};