'use client';
import api from '@/lib/api';
import { useAuthStore } from '@/store/authStore';
import clsx from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';
import {
    Award,
    BarChart2,
    Bell,
    BookOpen,
    Brain,
    Briefcase,
    Calendar, FileText,
    LayoutDashboard,
    LogOut,
    Menu,
    MessageSquare,
    Moon,
    Settings,
    Sun,
    Trophy,
    Users,
    Video,
    X
} from 'lucide-react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useState } from 'react';
import toast from 'react-hot-toast';
import { useQuery } from 'react-query';

const studentNav = [
  { href: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { href: '/courses', icon: BookOpen, label: 'Courses' },
  { href: '/ai-guide', icon: Brain, label: 'AI Guide' },
  { href: '/live-classes', icon: Video, label: 'Live Classes' },
  { href: '/chat', icon: MessageSquare, label: 'Messages' },
  { href: '/quizzes', icon: FileText, label: 'Quizzes' },
  { href: '/study-plan', icon: Calendar, label: 'Study Plan' },
  { href: '/certificates', icon: Award, label: 'Certificates' },
  { href: '/leaderboard', icon: Trophy, label: 'Leaderboard' },
  { href: '/career', icon: Briefcase, label: 'Career Portal' },
  { href: '/analytics', icon: BarChart2, label: 'Analytics' }
];

const facultyNav = [
  { href: '/faculty', icon: LayoutDashboard, label: 'Dashboard' },
  { href: '/faculty/courses', icon: BookOpen, label: 'My Courses' },
  { href: '/faculty/live', icon: Video, label: 'Live Classes' },
  { href: '/faculty/assignments', icon: FileText, label: 'Assignments' },
  { href: '/chat', icon: MessageSquare, label: 'Messages' },
  { href: '/faculty/analytics', icon: BarChart2, label: 'Analytics' }
];

const adminNav = [
  { href: '/admin', icon: LayoutDashboard, label: 'Dashboard' },
  { href: '/admin/users', icon: Users, label: 'Users' },
  { href: '/admin/courses', icon: BookOpen, label: 'Courses' },
  { href: '/admin/analytics', icon: BarChart2, label: 'Analytics' },
  { href: '/admin/career', icon: Briefcase, label: 'Career Portal' }
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [darkMode, setDarkMode] = useState(false);
  const { user, logout } = useAuthStore();
  const pathname = usePathname();
  const router = useRouter();

  const navItems = user?.role === 'admin' ? adminNav : user?.role === 'faculty' ? facultyNav : studentNav;

  const { data: notifications } = useQuery('notifications', () =>
    api.get('/notifications').then(r => r.data), { refetchInterval: 30000 }
  );
  const unreadCount = notifications?.filter((n: any) => !n.is_read).length || 0;

  const handleLogout = async () => {
    await logout();
    toast.success('Logged out');
    router.push('/login');
  };

  return (
    <div className={clsx('flex h-screen overflow-hidden', darkMode && 'dark')}>
      {/* Sidebar */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.aside initial={{ x: -280 }} animate={{ x: 0 }} exit={{ x: -280 }} transition={{ type: 'spring', damping: 25 }}
            className="w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex flex-col z-30 fixed h-full lg:relative">
            {/* Logo */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-800">
              <div className="flex items-center gap-2">
                <BookOpen className="text-blue-600" size={24} />
                <span className="font-bold text-lg">EduAI</span>
              </div>
            </div>

            {/* User info */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-800">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-semibold text-sm">
                  {user?.name?.[0]?.toUpperCase()}
                </div>
                <div className="min-w-0">
                  <div className="font-medium text-sm truncate">{user?.name}</div>
                  <div className="text-xs text-gray-500 capitalize">{user?.role}</div>
                </div>
              </div>
            </div>

            {/* Nav */}
            <nav className="flex-1 overflow-y-auto p-3 space-y-1">
              {navItems.map((item) => (
                <Link key={item.href} href={item.href}
                  className={clsx(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all',
                    pathname === item.href
                      ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                  )}>
                  <item.icon size={18} />
                  {item.label}
                </Link>
              ))}
            </nav>

            {/* Bottom */}
            <div className="p-3 border-t border-gray-200 dark:border-gray-800 space-y-1">
              <Link href="/settings" className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800">
                <Settings size={18} /> Settings
              </Link>
              <button onClick={handleLogout} className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20">
                <LogOut size={18} /> Logout
              </button>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Main */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-4 py-3 flex items-center gap-4">
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>

          <div className="flex-1" />

          <button onClick={() => setDarkMode(!darkMode)} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
            {darkMode ? <Sun size={20} /> : <Moon size={20} />}
          </button>

          <Link href="/notifications" className="relative text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
            <Bell size={20} />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </Link>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-6 bg-gray-50 dark:bg-gray-950">
          {children}
        </main>
      </div>
    </div>
  );
}
