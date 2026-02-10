import { type Widget } from '../../types';
import { useQuery } from '@tanstack/react-query';
import { widgetApi } from '../../api/widgets';
import { Loader } from '../common/Loader';
import { DataGrid, type GridColDef } from '@mui/x-data-grid';

interface TableWidgetProps {
  widget: Widget;
  data?: any[]; // Optional data for preview mode (chat)
}

export const TableWidget = ({ widget, data: previewData }: TableWidgetProps) => {
  const { data: fetchedData, isLoading } = useQuery({
    queryKey: ['widgetData', widget.id],
    queryFn: () => widgetApi.getData(widget.id),
    enabled: !previewData, // Skip query if preview data provided
    staleTime: 0, // Always consider data stale
    refetchOnMount: true, // Refetch when component mounts
  });

  if (!previewData && isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader />
      </div>
    );
  }

  const rows = previewData || fetchedData?.data || [];
  const chartConfig = widget.chart_config || {};
  
  // Add unique id to each row for DataGrid
  const rowsWithId = rows.map((row: any, index: number) => ({
    id: index,
    ...row,
  }));
  
  // If columns are specified in config, use them; otherwise, auto-detect from first row
  let columnList: string[] = chartConfig?.columns || [];
  if (columnList.length === 0 && rows.length > 0) {
    columnList = Object.keys(rows[0]);
  }
  
  const columns: GridColDef[] = columnList.map((col: string) => ({
    field: col,
    headerName: col.replace(/_/g, ' ').replace(/([A-Z])/g, ' $1').trim(),
    flex: 1,
    minWidth: 150,
  }));

  return (
    <div className="h-full w-full">
      <DataGrid
        rows={rowsWithId}
        columns={columns}
        initialState={{
          pagination: {
            paginationModel: { pageSize: 10, page: 0 },
          },
        }}
        pageSizeOptions={[10, 25, 50]}
        disableRowSelectionOnClick
        sx={{
          border: 'none',
          '& .MuiDataGrid-cell': {
            borderBottom: '1px solid #f3f4f6',
          },
        }}
      />
    </div>
  );
};