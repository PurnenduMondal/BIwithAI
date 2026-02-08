import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/common/Button';
import { Input } from '@/components/common/Input';
import { useUploadCSV, useCreateDataSource } from '@/hooks/useDataSource';
import { useDropzone } from 'react-dropzone';
import { CloudArrowUpIcon } from '@heroicons/react/24/outline';

export const DataSourceCreate = () => {
  const navigate = useNavigate();
  const uploadCSV = useUploadCSV();
  const createDataSource = useCreateDataSource();
  
  const [dataSourceType, setDataSourceType] = useState<'csv' | 'database'>('csv');
  const [name, setName] = useState('');
  const [file, setFile] = useState<File | null>(null);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'text/csv': ['.csv'],
    },
    maxFiles: 1,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setFile(acceptedFiles[0]);
        if (!name) {
          setName(acceptedFiles[0].name.replace('.csv', ''));
        }
      }
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (dataSourceType === 'csv' && file) {
      uploadCSV.mutate({ file, name });
    }
  };

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Add Data Source</h1>
        <p className="text-gray-600 mt-1">
          Connect your data to start creating dashboards
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Data Source Type Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Data Source Type
            </label>
            <div className="grid grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => setDataSourceType('csv')}
                className={`p-4 border-2 rounded-lg text-left transition ${
                  dataSourceType === 'csv'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <h3 className="font-medium text-gray-900">CSV File</h3>
                <p className="text-sm text-gray-600 mt-1">Upload a CSV file</p>
              </button>
              <button
                type="button"
                onClick={() => setDataSourceType('database')}
                className={`p-4 border-2 rounded-lg text-left transition ${
                  dataSourceType === 'database'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <h3 className="font-medium text-gray-900">Database</h3>
                <p className="text-sm text-gray-600 mt-1">Connect to a database</p>
              </button>
            </div>
          </div>

          {/* CSV Upload */}
          {dataSourceType === 'csv' && (
            <>
              <Input
                label="Data Source Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="My Sales Data"
                required
              />

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload CSV File
                </label>
                <div
                  {...getRootProps()}
                  className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition ${
                    isDragActive
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-300 hover:border-gray-400'
                  }`}
                >
                  <input {...getInputProps()} />
                  <CloudArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
                  {file ? (
                    <p className="mt-2 text-sm text-gray-900 font-medium">{file.name}</p>
                  ) : (
                    <>
                      <p className="mt-2 text-sm text-gray-900">
                        {isDragActive ? 'Drop the file here' : 'Drag & drop a CSV file here'}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">or click to browse</p>
                    </>
                  )}
                </div>
              </div>
            </>
          )}

          {/* Database Connection (placeholder) */}
          {dataSourceType === 'database' && (
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800">
                Database connections are coming soon. For now, please use CSV upload.
              </p>
            </div>
          )}

          <div className="flex items-center gap-3">
            <Button
              type="submit"
              disabled={dataSourceType === 'csv' && (!file || !name)}
              isLoading={uploadCSV.isPending}
            >
              Add Data Source
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/data-sources')}
            >
              Cancel
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};