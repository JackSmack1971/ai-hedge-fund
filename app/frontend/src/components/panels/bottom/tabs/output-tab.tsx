import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useFlowContext } from '@/contexts/flow-context';
import { useFlowConnectionState } from '@/hooks/use-flow-connection';
import { useNodeContext } from '@/contexts/node-context';
import { cn } from '@/lib/utils';
import { BacktestOutput } from './backtest-output';
import { sortAgents } from './output-tab-utils';
import { RegularOutput } from './regular-output';

interface OutputTabProps {
  className?: string;
}

export function OutputTab({ className }: OutputTabProps) {
  const { currentFlowId } = useFlowContext();
  const { getAgentNodeDataForFlow, getOutputNodeDataForFlow } = useNodeContext();
  const connection = useFlowConnectionState(currentFlowId?.toString() || null);

  // Get current flow data
  const agentData = getAgentNodeDataForFlow(currentFlowId?.toString() || null);
  const outputData = getOutputNodeDataForFlow(currentFlowId?.toString() || null);
  
  // Detect if this is a backtest run
  const isBacktestRun = agentData && agentData['backtest'];
  const connectionMessage = connection?.state === 'error' || connection?.state === 'completed-with-warning'
    ? connection.error
    : null;
  
  // Sort agents for display (exclude backtest agent from regular agent list)
  const sortedAgents = sortAgents(Object.entries(agentData).filter(([agentId]) => agentId !== 'backtest'));
  
  return (
    <div className={cn("h-full overflow-y-auto font-mono text-sm", className)}>
      {connectionMessage && !outputData && (
        <Card className={cn(
          "mb-4",
          connection?.state === 'error'
            ? "border-destructive/40 bg-destructive/5"
            : "border-amber-500/40 bg-amber-500/5"
        )}>
          <CardHeader>
            <CardTitle className="text-lg">
              {connection?.state === 'error' ? 'Run failed' : 'Run completed with warning'}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            {connectionMessage}
          </CardContent>
        </Card>
      )}

      {/* Render backtest output if this is a backtest run */}
      {isBacktestRun && (
        <BacktestOutput agentData={agentData} outputData={outputData} />
      )}
      
      {/* Render regular output if not a backtest run */}
      {!isBacktestRun && (
        <RegularOutput sortedAgents={sortedAgents} outputData={outputData} />
      )}
      
      {/* Empty State */}
      {!outputData && sortedAgents.length === 0 && !isBacktestRun && !connectionMessage && (
        <div className="text-center py-8 text-muted-foreground">
          No output to display. Run an analysis to see progress and results.
        </div>
      )}
    </div>
  );
}
