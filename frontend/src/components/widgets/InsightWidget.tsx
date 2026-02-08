import { type Widget } from '@/types';
import { useQuery } from '@tanstack/react-query';
import { insightApi } from '@/api/insights';
import { Loader } from '@/components/common/Loader';
import { LightBulbIcon } from '@heroicons/react/24/solid';

interface InsightWidgetProps {
  widget: Widget;
}

export const InsightWidget = ({ widget }: InsightWidgetProps) => {
  const { data: insights, isLoading } = useQuery({
    queryKey: ['insights', widget.dashboard_id],
    queryFn: () => insightApi.list(widget.dashboard_id),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader />
      </div>
    );
  }

  return (
    <div className="space-y-3 h-full overflow-y-auto">
      {insights?.slice(0, 5).map((insight) => (
        <div
          key={insight.id}
          className="p-3 bg-blue-50 border border-blue-200 rounded-lg"
        >
          <div className="flex items-start gap-2">
            <LightBulbIcon className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">
                {insight.insight_type.replace('_', ' ').toUpperCase()}
              </p>
              <p className="text-sm text-gray-700 mt-1">{insight.content}</p>
              <div className="flex items-center gap-2 mt-2">
                <span className="text-xs text-gray-500">
                  Confidence: {(insight.confidence_score * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>
        </div>
      ))}

      {(!insights || insights.length === 0) && (
        <div className="flex flex-col items-center justify-center h-full text-gray-400">
          <LightBulbIcon className="w-12 h-12 mb-2" />
          <p className="text-sm">No insights available yet</p>
        </div>
      )}
    </div>
  );
};