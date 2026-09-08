import React, { useEffect, useState } from 'react';
import { Database, RefreshCw } from 'lucide-react';

type DataSource = {
  name: string;
  endpoint: string;
};

type DataSourceStatus = DataSource & {
  status: string;
  authority?: string;
  lastChecked?: string;
};

const DATA_SOURCES: DataSource[] = [
  { name: 'Hydrology/CWC', endpoint: '/api/hydrology/status' },
  { name: 'Roads/OSM', endpoint: '/api/roads/status' },
  { name: 'Shelters/USDMA', endpoint: '/api/shelters/status' },
  { name: 'Alerts', endpoint: '/api/alerts/status' },
  { name: 'IMD Warnings', endpoint: '/api/imd/status' },
];

const getStatusClasses = (status: string) => {
  const normalizedStatus = status.toUpperCase();
  if (normalizedStatus.includes('UNAVAILABLE') || normalizedStatus.includes('STATIC')) {
    return 'bg-white/5 text-gray-400 border-white/15';
  }
  if (
    normalizedStatus.includes('LIVE') ||
    normalizedStatus.includes('REAL_LIVE') ||
    normalizedStatus.includes('LIVE_OFFICIAL') ||
    normalizedStatus.includes('READY')
  ) {
    return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
  }
  if (normalizedStatus.includes('CACHED')) {
    return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
  }
  if (normalizedStatus === 'UNAVAILABLE') {
    return 'bg-white/5 text-gray-400 border-white/15';
  }
  return 'bg-red-500/15 text-red-400 border-red-500/30';
};

const getStatusLabel = (status: string) => {
  const normalizedStatus = status.toUpperCase();
  if (normalizedStatus.includes('UNAVAILABLE')) return 'NO LIVE CREDENTIALS';
  if (normalizedStatus.includes('REAL_STATIC') || normalizedStatus.includes('STATIC')) return 'STATIC/VERIFIED';
  if (normalizedStatus.includes('CACHED')) return 'CACHED';
  if (normalizedStatus.includes('REAL_LIVE') || normalizedStatus.includes('LIVE_OFFICIAL')) return 'LIVE';
  return status;
};

const formatLastChecked = (value: unknown): string | undefined => {
  if (typeof value !== 'string' && typeof value !== 'number') return undefined;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString();
};

const getResponseValue = (data: Record<string, unknown>, keys: string[]) => {
  for (const key of keys) {
    if (data[key] != null) return data[key];
  }
  return undefined;
};

export const DataSourcesPanel: React.FC = () => {
  const [sources, setSources] = useState<DataSourceStatus[]>([]);

  useEffect(() => {
    let isMounted = true;

    Promise.allSettled(
      DATA_SOURCES.map(async (source): Promise<DataSourceStatus> => {
        const response = await fetch(source.endpoint);
        if (!response.ok) throw new Error(`Failed to fetch ${source.name}`);

        const data = (await response.json()) as Record<string, unknown>;
        const status = getResponseValue(data, ['status', 'state', 'data_state', 'official_live_status']);
        const authority = getResponseValue(data, ['authority', 'source', 'provider']);
        const lastChecked = getResponseValue(data, ['last_checked', 'lastChecked', 'checked_at', 'updated_at']);

        return {
          ...source,
          status: typeof status === 'string' ? status : 'UNAVAILABLE',
          authority: typeof authority === 'string' ? authority : undefined,
          lastChecked: formatLastChecked(lastChecked),
        };
      })
    ).then((results) => {
      if (!isMounted) return;
      setSources(
        results.map((result, index) =>
          result.status === 'fulfilled'
            ? result.value
            : { ...DATA_SOURCES[index], status: 'OFFLINE' }
        )
      );
    });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <section className="flex-1 overflow-y-auto bg-[#08090B] p-4 lg:p-6 font-sans">
      <div className="max-w-7xl mx-auto space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Database className="w-5 h-5 text-[#FF7A18]" />
              <h1 className="text-lg font-black text-white tracking-wider font-mono">DATA SOURCES</h1>
            </div>
            <p className="text-xs text-gray-400 mt-1">Live provenance and status of all integrated data feeds.</p>
          </div>
          <RefreshCw className="w-4 h-4 text-gray-500 mt-1" />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-3">
          {DATA_SOURCES.map((source, index) => {
            const sourceStatus = sources[index];
            const status = sourceStatus?.status || 'CHECKING...';
            const statusLabel = getStatusLabel(status);

            return (
              <div key={source.endpoint} className="bento-card bg-[#14181D] border border-white/10 p-4 space-y-4 min-h-40">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <span className="text-xs text-white font-bold font-mono leading-tight min-w-0 flex-1">{source.name}</span>
                  <span className={`max-w-full whitespace-normal break-words text-center text-[9px] font-black font-mono px-2 py-1 rounded-lg border ${getStatusClasses(status)}`}>
                    {statusLabel}
                  </span>
                </div>
                <div className="space-y-2 text-[11px] font-mono">
                  {sourceStatus?.authority && (
                    <div>
                      <span className="text-gray-500 block">AUTHORITY</span>
                      <span className="text-gray-300">{sourceStatus.authority}</span>
                    </div>
                  )}
                  {sourceStatus?.lastChecked && (
                    <div>
                      <span className="text-gray-500 block">LAST CHECKED</span>
                      <span className="text-gray-300">{sourceStatus.lastChecked}</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default DataSourcesPanel;
