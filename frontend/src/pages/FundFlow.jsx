import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import ReactFlow, {
  Controls,
  Background,
  applyNodeChanges,
  applyEdgeChanges,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { caseApi, graphApi } from '../api/client';
import CaseNav from '../components/CaseNav';
import { GitBranch, RefreshCw, Layers, DollarSign, ArrowRight } from 'lucide-react';

export default function FundFlow() {
  const { id } = useParams();
  const [caseData, setCaseData] = useState(null);
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [rawEdges, setRawEdges] = useState([]);
  const [selectedEdgeData, setSelectedEdgeData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchGraph = async (refresh = false) => {
    setLoading(true);
    try {
      const [caseRes, graphRes] = await Promise.all([
        caseApi.get(id),
        graphApi.getFundFlow(id, refresh),
      ]);
      setCaseData(caseRes.data.data.case);

      const rawNodes = graphRes.data.data.nodes || [];
      const edgeList = graphRes.data.data.edges || [];
      setRawEdges(edgeList);

      // Arrange nodes in circle or grid layout
      const flowNodes = rawNodes.map((n, idx) => {
        const angle = (idx / Math.max(1, rawNodes.length)) * 2 * Math.PI;
        const radius = 280;
        const x = 450 + radius * Math.cos(angle);
        const y = 300 + radius * Math.sin(angle);

        return {
          id: n.id,
          data: { label: n.label || n.id },
          position: { x, y },
          style: {
            background: '#0f172a',
            color: '#f8fafc',
            border: '2px solid #22c55e',
            borderRadius: '12px',
            padding: '10px 14px',
            fontSize: '12px',
            fontWeight: '600',
            boxShadow: '0 4px 12px rgba(34, 197, 94, 0.1)',
            minWidth: '130px',
            textAlign: 'center',
          },
        };
      });

      const flowEdges = edgeList.map((e, idx) => ({
        id: `e-${idx}-${e.source}-${e.target}`,
        source: e.source,
        target: e.target,
        label: `₹${(e.total_amount || 0).toLocaleString('en-IN')}`,
        type: 'smoothstep',
        animated: true,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#10b981',
        },
        style: {
          stroke: '#10b981',
          strokeWidth: 2.5,
        },
        labelStyle: {
          fill: '#f8fafc',
          fontWeight: 700,
          fontSize: 10,
        },
        labelBgStyle: {
          fill: '#020617',
          fillOpacity: 0.9,
          rx: 4,
          stroke: '#334155',
          strokeWidth: 1,
        },
        data: e,
      }));

      setNodes(flowNodes);
      setEdges(flowEdges);
    } catch (e) {
      console.error('Failed to load fund flow graph', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraph();
  }, [id]);

  const onNodesChange = useCallback((changes) => setNodes((nds) => applyNodeChanges(changes, nds)), []);
  const onEdgesChange = useCallback((changes) => setEdges((eds) => applyEdgeChanges(changes, eds)), []);

  const onEdgeClick = (evt, edge) => {
    setSelectedEdgeData(edge.data);
  };

  if (!caseData) return <div className="text-center py-20 text-slate-400">Loading fund flow graph...</div>;

  return (
    <div>
      <CaseNav
        caseId={caseData.case_id}
        caseNumber={caseData.case_number}
        title={caseData.title}
        score={caseData.suspicion_score}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow">
          <div>
            <h1 className="text-xl font-extrabold text-white tracking-tight flex items-center gap-2">
              <GitBranch className="w-5 h-5 text-emerald-400" />
              Institutional & Counterparty Fund Flow Graph
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Interactive NetworkX graph representation. Click any edge to inspect transaction evidence.
            </p>
          </div>

          <button
            onClick={() => fetchGraph(true)}
            className="inline-flex items-center gap-2 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-lg text-xs border border-slate-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4 text-emerald-400" />
            <span>Recompute Graph</span>
          </button>
        </div>

        {/* React Flow Container */}
        <div className="relative bg-slate-950 border border-slate-800 rounded-xl h-[580px] overflow-hidden shadow-2xl">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onEdgeClick={onEdgeClick}
            fitView
          >
            <Background color="#1e293b" gap={20} />
            <Controls className="bg-slate-900 border border-slate-800 fill-slate-200" />
          </ReactFlow>

          {/* Edge Detail Drawer */}
          {selectedEdgeData && (
            <div className="absolute top-4 right-4 z-10 w-80 bg-slate-900/95 border border-slate-700 rounded-xl p-4 shadow-2xl backdrop-blur-md space-y-3 text-xs">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <span className="font-bold text-white uppercase tracking-wider text-[11px]">Edge Transaction Evidence</span>
                <button
                  onClick={() => setSelectedEdgeData(null)}
                  className="text-slate-400 hover:text-white font-bold"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-2 text-slate-200">
                  <span className="font-mono text-emerald-400 font-semibold">{selectedEdgeData.source}</span>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  <span className="font-mono text-cyan-400 font-semibold">{selectedEdgeData.target}</span>
                </div>

                <div className="flex justify-between">
                  <span className="text-slate-400">Total Transferred:</span>
                  <span className="font-mono font-bold text-white text-sm">
                    ₹{selectedEdgeData.total_amount?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                </div>

                <div className="flex justify-between">
                  <span className="text-slate-400">Transactions Count:</span>
                  <span className="font-mono font-bold text-slate-200">{selectedEdgeData.transaction_count}</span>
                </div>

                {selectedEdgeData.transaction_ids && (
                  <div>
                    <span className="text-slate-400 block mb-1">Underlying Transaction IDs:</span>
                    <div className="max-h-24 overflow-y-auto space-y-1 bg-slate-950 p-2 rounded border border-slate-800 font-mono text-[10px]">
                      {selectedEdgeData.transaction_ids.map((txId) => (
                        <div key={txId} className="text-emerald-400">
                          • {txId}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
