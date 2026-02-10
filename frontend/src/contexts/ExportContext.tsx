import { createContext, useContext, useState, useCallback, ReactNode } from 'react';

export interface ExportJob {
  jobId: string;
  dashboardId: string;
  dashboardName: string;
  format: string;
  progress: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  message: string;
  downloadUrl?: string;
  error?: string;
  createdAt: Date;
}

interface ExportContextType {
  exports: ExportJob[];
  addExport: (job: Omit<ExportJob, 'createdAt'>) => void;
  updateExport: (jobId: string, updates: Partial<ExportJob>) => void;
  removeExport: (jobId: string) => void;
  clearCompleted: () => void;
  activeCount: number;
}

const ExportContext = createContext<ExportContextType | undefined>(undefined);

export const ExportProvider = ({ children }: { children: ReactNode }) => {
  const [exports, setExports] = useState<ExportJob[]>([]);

  const addExport = useCallback((job: Omit<ExportJob, 'createdAt'>) => {
    setExports((prev) => [
      { ...job, createdAt: new Date() },
      ...prev,
    ]);
  }, []);

  const updateExport = useCallback((jobId: string, updates: Partial<ExportJob>) => {
    setExports((prev) =>
      prev.map((exp) =>
        exp.jobId === jobId ? { ...exp, ...updates } : exp
      )
    );
  }, []);

  const removeExport = useCallback((jobId: string) => {
    setExports((prev) => prev.filter((exp) => exp.jobId !== jobId));
  }, []);

  const clearCompleted = useCallback(() => {
    setExports((prev) =>
      prev.filter((exp) => exp.status !== 'completed' && exp.status !== 'failed')
    );
  }, []);

  const activeCount = exports.filter(
    (exp) => exp.status === 'pending' || exp.status === 'processing'
  ).length;

  return (
    <ExportContext.Provider
      value={{
        exports,
        addExport,
        updateExport,
        removeExport,
        clearCompleted,
        activeCount,
      }}
    >
      {children}
    </ExportContext.Provider>
  );
};

export const useExports = () => {
  const context = useContext(ExportContext);
  if (!context) {
    throw new Error('useExports must be used within ExportProvider');
  }
  return context;
};
