import React from 'react';

interface OperationalLayoutProps {
  sidebar?: React.ReactNode;
  topBar: React.ReactNode;
  children: React.ReactNode;
  banner?: React.ReactNode;
}

export const OperationalLayout: React.FC<OperationalLayoutProps> = ({
  sidebar,
  topBar,
  children,
  banner,
}) => {
  return (
    <div className="flex h-screen max-h-screen w-full min-w-0 bg-[#08090B] text-white overflow-hidden font-sans select-none">
      {/* 1. Fixed Left Sidebar */}
      {sidebar}

      {/* 2. Main Operational Column */}
      <div className="flex-1 flex flex-col h-full min-h-0 min-w-0 overflow-hidden relative bg-[#08090B]">
        {/* Top Glassmorphic Search & Command Bar */}
        {topBar}

        {/* Optional Notification or Status Banner */}
        {banner}

        {/* Main Operational Viewport (Responsive Bento Layout) */}
        <main className="flex-1 flex flex-col min-h-0 min-w-0 overflow-hidden relative bg-[#08090B]">
          {children}
        </main>
      </div>
    </div>
  );
};

export default OperationalLayout;
