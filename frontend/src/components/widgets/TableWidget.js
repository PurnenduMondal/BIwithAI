import { jsx as _jsx } from "react/jsx-runtime";
import {} from '@/types';
import { useQuery } from '@tanstack/react-query';
import { widgetApi } from '@/api/widgets';
import { Loader } from '@/components/common/Loader';
import { DataGrid } from '@mui/x-data-grid';
export const TableWidget = ({ widget }) => {
    const { data, isLoading } = useQuery({
        queryKey: ['widgetData', widget.id],
        queryFn: () => widgetApi.getData(widget.id),
    });
    if (isLoading) {
        return (_jsx("div", { className: "flex items-center justify-center h-full", children: _jsx(Loader, {}) }));
    }
    const rows = data?.data || [];
    const columns = (widget.config?.columns || []).map((col) => ({
        field: col,
        headerName: col,
        flex: 1,
        minWidth: 150,
    }));
    return (_jsx("div", { className: "h-full w-full", children: _jsx(DataGrid, { rows: rows, columns: columns, initialState: {
                pagination: {
                    paginationModel: { pageSize: 10, page: 0 },
                },
            }, pageSizeOptions: [10, 25, 50], disableRowSelectionOnClick: true, sx: {
                border: 'none',
                '& .MuiDataGrid-cell': {
                    borderBottom: '1px solid #f3f4f6',
                },
            } }) }));
};
