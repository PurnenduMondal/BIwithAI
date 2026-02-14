import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  HomeIcon,
  ChartBarIcon,
  CircleStackIcon,
  BellAlertIcon,
  Cog6ToothIcon,
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
    <aside 
      className={`${isCollapsed ? 'w-20' : 'w-64'} bg-gray-900 text-white transition-all duration-300 fixed left-0 top-0 h-full z-50`}
      onMouseEnter={() => setIsCollapsed(false)}
      onMouseLeave={() => setIsCollapsed(true)}
    >
      <div className="flex items-center justify-center h-16 border-b border-gray-800">
        {!isCollapsed && <h1 className={`text-xl font-bold transition-opacity duration-200 ${isCollapsed ? 'opacity-0' : 'opacity-100 delay-500'}`}>AI2BI</h1>}
        {isCollapsed && <h1 className="text-xl font-bold">AB</h1>}
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
              {!isCollapsed && <span className={`transition-opacity duration-200 ${isCollapsed ? 'opacity-0' : 'opacity-100 delay-500'}`}>{item.name}</span>}
            </NavLink>
          ))}
        </div>
      </nav>
    </aside>
  );
};