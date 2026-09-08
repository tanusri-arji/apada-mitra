import React from 'react';

interface OperationalLayoutProps {
  sidebar?: React.ReactNode;
  topBar: React.ReactNode;
  children: React.ReactNode;
  banner?: React.ReactNode;
  isDesktopSidebarOpen?: boolean;
  isMobileSidebarOpen?: boolean;
  onCloseMobileSidebar?: () => void;
}

export const OperationalLayout: React.FC<OperationalLayoutProps> = ({
  sidebar,
  topBar,
  children,
  banner,
  isDesktopSidebarOpen = true,
  isMobileSidebarOpen = false,
  onCloseMobileSidebar,
}) => {
  return (
    <div className="flex h-screen max-h-screen w-full min-w-0 bg-[#08090B] text-white overflow-hidden overflow-x-hidden font-sans select-none relative">
      {/* 1. Desktop Fixed Left Sidebar (Collapsible) */}
      {isDesktopSidebarOpen && (
        <div className="hidden lg:flex flex-shrink-0 h-full transition-all duration-300">
          {sidebar}
        </div>
      )}

      {/* 2. Mobile Drawer Overlay */}
      {isMobileSidebarOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/80 backdrop-blur-sm transition-opacity"
            onClick={onCloseMobileSidebar}
            aria-hidden="true"
          />
          {/* Slide-out Drawer Panel */}
          <div className="relative z-50 w-[285px] max-w-[85vw] h-full shadow-2xl flex flex-col bg-[#0E1115] border-r border-white/10">
            {sidebar}
          </div>
        </div>
      )}

      {/* 3. Main Operational Column */}
      <div className="flex-1 flex flex-col h-full min-h-0 min-w-0 overflow-hidden overflow-x-hidden relative bg-[#08090B] w-full">
        {/* Top Glassmorphic Search & Command Bar */}
        {topBar}

        {/* Optional Notification or Status Banner */}
        {banner}

        {/* Main Operational Viewport (Responsive Bento Layout) */}
        <main className="flex-1 flex flex-col min-h-0 min-w-0 overflow-hidden overflow-x-hidden relative bg-[#08090B] w-full">
          {children}
        </main>
      </div>
    </div>
  );
};

export default OperationalLayout;
