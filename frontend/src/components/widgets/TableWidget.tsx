import { type Widget } from '../../types';
import { useQuery } from '@tanstack/react-query';
import { widgetApi } from '../../api/widgets';
import { Loader } from '../common/Loader';
import { DataGrid, type GridColDef } from '@mui/x-data-grid';

interface TableWidgetProps {
  widget: Widget;
}

export const TableWidget = ({ widget }: TableWidgetProps) => {
  const { data, isLoading } = useQuery({
    queryKey: ['widgetData', widget.id],
    queryFn: () => widgetApi.getData(widget.id),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader />
      </div>
    );
  }

  const rows = data?.data || [];
  const columns: GridColDef[] = (widget.config?.columns || []).map((col: string) => ({
    field: col,
    headerName: col,
    flex: 1,
    minWidth: 150,
  }));

  return (
    <div className="h-full w-full">
      <DataGrid
        rows={rows}
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