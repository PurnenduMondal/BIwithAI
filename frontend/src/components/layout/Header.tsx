import { useState, useRef, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useNotifications } from '../../contexts/NotificationContext';
import { useExports } from '../../contexts/ExportContext';
import { ExportQueueModal } from '../exports/ExportQueueModal';
import { apiClient } from '../../api/client';
import toast from 'react-hot-toast';
import {
  BellIcon,
  UserCircleIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
  CheckIcon,
  XMarkIcon,
  ArrowDownTrayIcon,
} from '@heroicons/react/24/outline';
import { formatDistanceToNow } from 'date-fns';

export const Header = () => {
  const { user, logout } = useAuth();
  const { notifications, unreadCount, markAsRead, markAllAsRead, removeNotification } = useNotifications();
  const { activeCount } = useExports();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isNotificationOpen, setIsNotificationOpen] = useState(false);
  const [isExportQueueOpen, setIsExportQueueOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const notificationRef = useRef<HTMLDivElement>(null);

  const handleDownload = async (url: string, filename: string) => {
    try {
      const response = await apiClient.get(url, { responseType: 'blob' });
      const blob = new Blob([response.data]);
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
      toast.success('Download started');
    } catch (error) {
      console.error('Download error:', error);
      toast.error('Failed to download file');
    }
  };

  // Close menus when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
      if (notificationRef.current && !notificationRef.current.contains(event.target as Node)) {
        setIsNotificationOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="flex items-center justify-between px-6 py-2">
        <div className="flex items-center">
          <h1 className="text-lg font-semibold text-gray-800">
            BI Dashboard Generator
          </h1>
        </div>

        <div className="flex items-center gap-3">
          {/* Export Queue */}
          <button 
            onClick={() => setIsExportQueueOpen(true)}
            className="p-1.5 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100 relative"
            title="Export Queue"
          >
            <ArrowDownTrayIcon className="w-5 h-5" />
            {activeCount > 0 && (
              <span className="absolute top-0.5 right-0.5 flex items-center justify-center w-4 h-4 text-xs font-bold text-white bg-blue-500 rounded-full">
                {activeCount}
              </span>
            )}
          </button>

          {/* Notifications */}
          <div className="relative" ref={notificationRef}>
            <button 
              onClick={() => setIsNotificationOpen(!isNotificationOpen)}
              className="p-1.5 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100 relative"
            >
              <BellIcon className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute top-0.5 right-0.5 flex items-center justify-center w-4 h-4 text-xs font-bold text-white bg-red-500 rounded-full">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>

            {/* Notification Dropdown */}
            {isNotificationOpen && (
              <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-lg ring-1 ring-black ring-opacity-5 z-50 max-h-96 overflow-hidden flex flex-col">
                <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-gray-900">Notifications</h3>
                  {notifications.length > 0 && (
                    <button
                      onClick={markAllAsRead}
                      className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                    >
                      Mark all read
                    </button>
                  )}
                </div>
                
                <div className="overflow-y-auto flex-1">
                  {notifications.length === 0 ? (
                    <div className="px-4 py-8 text-center text-gray-500 text-sm">
                      No notifications
                    </div>
                  ) : (
                    notifications.map((notification) => (
                      <div
                        key={notification.id}
                        className={`px-4 py-3 border-b border-gray-100 hover:bg-gray-50 ${
                          !notification.read ? 'bg-blue-50' : ''
                        }`}
                        onClick={() => !notification.read && markAsRead(notification.id)}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <p className="text-sm font-medium text-gray-900">
                                {notification.title}
                              </p>
                              {!notification.read && (
                                <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                              )}
                            </div>
                            <p className="text-xs text-gray-600 mt-1">
                              {notification.message}
                            </p>
                            <div className="flex items-center gap-2 mt-2">
                              <p className="text-xs text-gray-500">
                                {formatDistanceToNow(notification.timestamp, { addSuffix: true })}
                              </p>
                              {notification.downloadUrl && (
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleDownload(notification.downloadUrl!, `export.${notification.downloadUrl!.split('.').pop()}`);
                                  }}
                                  className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
                                >
                                  <ArrowDownTrayIcon className="w-3 h-3" />
                                  Download
                                </button>
                              )}
                            </div>
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              removeNotification(notification.id);
                            }}
                            className="ml-2 text-gray-400 hover:text-gray-600"
                          >
                            <XMarkIcon className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          {/* User Menu */}
          <div className="relative" ref={menuRef}>
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-gray-100"
            >
              <UserCircleIcon className="w-7 h-7 text-gray-600" />
              <div className="text-left">
                <p className="text-sm font-medium text-gray-900">
                  {user?.full_name || user?.email}
                </p>
                <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
              </div>
            </button>

            {/* Dropdown Menu */}
            {isMenuOpen && (
              <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg ring-1 ring-black ring-opacity-5 z-50">
                <div className="py-1">
                  <a
                    href="/settings"
                    className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    <Cog6ToothIcon className="w-5 h-5 mr-3" />
                    Settings
                  </a>
                  <button
                    onClick={() => {
                      setIsMenuOpen(false);
                      logout();
                    }}
                    className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <ArrowRightOnRectangleIcon className="w-5 h-5 mr-3" />
                    Logout
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Export Queue Modal */}
      <ExportQueueModal
        isOpen={isExportQueueOpen}
        onClose={() => setIsExportQueueOpen(false)}
      />
    </header>
  );
};