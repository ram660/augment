"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Message } from "@/lib/types/chat";
import { chatAPI } from "@/lib/api/chat";
import { useRouter } from "next/navigation";
import { ImageIcon, Layers, ShoppingCart, ReceiptText, ExternalLink, Download, Shuffle, Info, Maximize2, X, Loader2 } from "lucide-react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  ReactFlowProvider,
  addEdge,
  useEdgesState,
  useNodesState,
  type Node,
  type Edge,
  type Connection,
  type NodeProps,
} from "reactflow";
import "reactflow/dist/style.css";

export interface CanvasPanelProps {
  conversationId?: string | null;
  messages: Message[];
  className?: string;
}

type NodeKind = "image" | "design" | "product" | "estimate";

type CardData = {
  id: string;
  title: string;
  type: NodeKind;
  thumbnail?: string;
  payload?: any;
  busy?: boolean;
  onOpen?: (data: CardData) => void;
  onCompare?: (data: CardData) => void;
  onExport?: (data: CardData) => void;
  onDetails?: (data: CardData) => void;
  onLightbox?: (data: CardData) => void;
};

// Collect shallow URL-like fields from an object for quick linking in the details panel
function collectUrlPairs(obj: any): Array<{ key: string; url: string }> {
  try {
    if (!obj || typeof obj !== 'object') return [];
    const pairs: Array<{ key: string; url: string }> = [];
    for (const [k, v] of Object.entries(obj)) {
      if (typeof v === 'string' && /^https?:\/\//i.test(v)) {
        pairs.push({ key: k, url: v });
      }
      if (Array.isArray(v)) {
        for (const it of v) {
          if (typeof it === 'string' && /^https?:\/\//i.test(it)) {
            pairs.push({ key: k, url: it });
          }
        }
      }
    }
    // Deduplicate by url
    const seen = new Set<string>();
    return pairs.filter((p) => (seen.has(p.url) ? false : (seen.add(p.url), true)));
  } catch {
    return [];
  }
}

const iconFor = (t: NodeKind) =>
  t === "image" ? (
    <ImageIcon className="w-4 h-4" />
  ) : t === "design" ? (
    <Layers className="w-4 h-4" />
  ) : t === "product" ? (
    <ShoppingCart className="w-4 h-4" />
  ) : (
    <ReceiptText className="w-4 h-4" />
  );

const CardNode: React.FC<NodeProps<CardData>> = ({ data }) => {
  const [showInfo, setShowInfo] = React.useState(false);
  const links = React.useMemo(() => collectUrlPairs(data.payload), [data.payload]);
  return (
    <div className="relative rounded-lg border bg-white shadow-sm w-48 overflow-visible">
      <div className="flex items-center justify-between px-2 py-1.5 text-xs border-b bg-gray-50">
        <div className="flex items-center gap-1">
          {iconFor(data.type)}
          <span className="truncate" title={data.title}>
            {data.title}
          </span>
        </div>
        <div className="flex items-center gap-1">
          {data.busy ? <Loader2 className="w-3.5 h-3.5 animate-spin text-slate-500" /> : null}
          <button
            className="text-slate-500 hover:text-slate-800"
            onClick={() => setShowInfo((v) => !v)}
            title="Quick details"
          >
            <Info className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {showInfo && (
        <div className="absolute right-1 top-7 z-20 w-56 bg-white border shadow-lg rounded-md p-2 text-[11px]">
          {links.length ? (
            <div className="mb-2">
              <div className="text-gray-500 mb-1">Links</div>
              <ul className="space-y-1 max-h-24 overflow-auto">
                {links.slice(0, 4).map((l, idx) => (
                  <li key={idx} className="truncate">
                    <a href={l.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline" title={`${l.key}: ${l.url}`}>
                      {l.key}: {l.url}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="text-gray-500 mb-2">No links detected</div>
          )}
          <div className="flex justify-end gap-2">
            <button
              className="px-2 py-1 rounded border text-[11px]"
              onClick={() => {
                setShowInfo(false);
                data.onDetails && data.onDetails(data);
              }}
            >
              Details
            </button>
            <button
              className="px-2 py-1 rounded border text-[11px]"
              onClick={() => {
                setShowInfo(false);
                data.onOpen && data.onOpen(data);
              }}
              disabled={!!data.busy}
            >
              Open
            </button>
          </div>
        </div>
      )}

      {data.thumbnail ? (
        <div className="relative">
          <img
            src={data.thumbnail}
            alt={data.title}
            className="w-full h-28 object-cover cursor-zoom-in"
            onClick={() => data.onLightbox && data.onLightbox(data)}
          />
          <button
            className="absolute right-1 top-1 bg-black/40 text-white rounded p-0.5"
            onClick={() => data.onLightbox && data.onLightbox(data)}
            title="View larger"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
        </div>
      ) : (
        <div className="w-full h-28 flex items-center justify-center text-xs text-gray-500">No preview</div>
      )}
      <div className="flex items-center justify-between px-2 py-1.5 border-t bg-white">
        <button
          className="inline-flex items-center gap-1 text-[11px] text-indigo-600 hover:text-indigo-800 disabled:opacity-50"
          onClick={() => data.onOpen && data.onOpen(data)}
          title="Open in Studio"
          disabled={!!data.busy}
        >
          <ExternalLink className="w-3.5 h-3.5" /> Open
        </button>
        <button
          className="inline-flex items-center gap-1 text-[11px] text-slate-600 hover:text-slate-800 disabled:opacity-50"
          onClick={() => data.onCompare && data.onCompare(data)}
          title="Compare"
          disabled={!!data.busy}
        >
          <Shuffle className="w-3.5 h-3.5" /> Compare
        </button>
        <button
          className="inline-flex items-center gap-1 text-[11px] text-slate-600 hover:text-slate-800 disabled:opacity-50"
          onClick={() => data.onExport && data.onExport(data)}
          title="Export PDF"
          disabled={!!data.busy}
        >
          <Download className="w-3.5 h-3.5" /> PDF
        </button>
      </div>
    </div>
  );
};

const nodeTypes = { cardNode: CardNode } as const;

export default function ReactFlowCanvasPanel({ conversationId, messages, className }: CanvasPanelProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([] as Node<CardData>[]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([] as Edge[]);
  const viewportRef = useRef<{ x: number; y: number; zoom: number } | null>(null);
  const saveTimer = useRef<number | null>(null);

  const router = useRouter();
  const [selected, setSelected] = useState<CardData | null>(null);
  const [lightboxUrl, setLightboxUrl] = useState<string | null>(null);
  const [busyNodeId, setBusyNodeId] = useState<string | null>(null);

  // Build items from assistant messages
  const items = useMemo(() => {
    const acc: Array<{
      id: string;
      type: NodeKind;
      title: string;
      thumbnail?: string;
      payload?: any;
    }> = [];
    for (const m of messages) {
      if (m.role !== "assistant") continue;
      const md = (m.metadata || {}) as any;
      const baseId = m.id.slice(0, 8);
      (md.images || []).forEach((url: string, idx: number) =>
        acc.push({ id: `${baseId}-img-${idx}`, type: "image", title: `Image ${idx + 1}`, thumbnail: url, payload: { url } })
      );
      (md.designs || []).forEach((d: any, idx: number) =>
        acc.push({ id: `${baseId}-des-${idx}`, type: "design", title: d?.title || `Design ${idx + 1}`, thumbnail: d?.thumbnail_url || d?.image_url, payload: d })
      );
      (md.products || []).forEach((p: any, idx: number) =>
        acc.push({ id: `${baseId}-prd-${idx}`, type: "product", title: p?.name || `Product ${idx + 1}`, thumbnail: p?.image || p?.image_url, payload: p })
      );
      if (Array.isArray(md.cost_estimates) && md.cost_estimates.length) {
        acc.push({ id: `${baseId}-est-0`, type: "estimate", title: md.cost_estimates[0]?.title || "Estimate", payload: md.cost_estimates[0] });
      }
    }
    return acc;
  }, [messages]);

  // Merge new items into nodes if not already present (assign simple grid positions)
  useEffect(() => {
    if (!items.length) return;
    setNodes((prev) => {
      const existingIds = new Set(prev.map((n) => n.id));
      const next: Node<CardData>[] = [...prev];
      let i = prev.length;
      for (const it of items) {
        if (existingIds.has(it.id)) continue;
        const col = i % 2;
        const row = Math.floor(i / 2);
        next.push({
          id: it.id,
          type: "cardNode",
          position: { x: 24 + col * 220, y: 24 + row * 200 },
          data: {
            id: it.id,
            type: it.type,
            title: it.title,
            thumbnail: it.thumbnail,
            payload: it.payload,
            onOpen: handleOpen,
            onCompare: handleCompare,
            onExport: handleExport,
            onDetails: handleDetails,
            onLightbox: handleLightbox,
          },
        });
        i++;
      }
      return next;
    });
  }, [items]);

  // Load saved canvas state from backend if available
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        if (!conversationId) return;
        const saved = await chatAPI.getCanvasState(conversationId);
        if (cancelled || !saved || (!saved.nodes && !saved.edges)) return;

        const savedNodes: Node<CardData>[] = (saved.nodes || []).map((n: any) => ({
          id: n.id,
          type: "cardNode",
          position: n.position || { x: 0, y: 0 },
          data: {
            id: n.data?.id || n.id,
            type: (n.data?.type || n.type || "image") as NodeKind,
            title: n.data?.title || n.label || "Item",
            thumbnail: n.data?.thumbnail,
            payload: n.data?.payload,
            onOpen: handleOpen,
            onCompare: handleCompare,
            onExport: handleExport,
            onDetails: handleDetails,
            onLightbox: handleLightbox,
          },
        }));
        const savedEdges: Edge[] = saved.edges || [];
        setNodes(savedNodes);
        setEdges(savedEdges);
        if (saved.viewport) viewportRef.current = saved.viewport;
      } catch (e) {
        // Ignore load errors for anonymous/first-run
        console.debug("Canvas load skipped:", e);
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId]);

  const handleOpen = useCallback(
    async (data: CardData) => {
      try {
        if (!conversationId) return;
        setBusyNodeId(data.id);
        const resp = await chatAPI.executeAction({
          conversation_id: conversationId,
          action: { type: "open_design_studio", node: { id: data.id, kind: data.type, title: data.title } },
        });
        const meta: any = (resp as any)?.metadata || {};
        const route = meta.navigate_to || meta.navigate_url || meta.studio_url || meta.url || (meta.route ? (meta.route.startsWith('/') ? meta.route : `/${meta.route}`) : null);
        if (route) router.push(route);
      } catch (e) {
        console.error("Open in Studio failed:", e);
      } finally {
        setBusyNodeId(null);
      }
    },
    [conversationId]
  );

  const handleCompare = useCallback(
    async (data: CardData) => {
      try {
        if (!conversationId) return;
        setBusyNodeId(data.id);
        await chatAPI.executeAction({
          conversation_id: conversationId,
          action: { type: "compare_variations", node: { id: data.id, kind: data.type } },
        });
      } catch (e) {
        console.error("Compare failed:", e);
      } finally {
        setBusyNodeId(null);
      }
    },
    [conversationId]
  );

  const handleExport = useCallback(
    async (data: CardData) => {
      try {
        if (!conversationId) return;
        setBusyNodeId(data.id);
        await chatAPI.executeAction({
          conversation_id: conversationId,
          action: { type: "export_pdf", node: { id: data.id, kind: data.type, title: data.title } },
        });
      } catch (e) {
        console.error("Export PDF failed:", e);
      } finally {
        setBusyNodeId(null);
      }
    },
    [conversationId]
  );
  const handleDetails = useCallback((data: CardData) => {
    setSelected(data);
  }, []);

  const handleLightbox = useCallback((data: CardData) => {
    const u = data.thumbnail || (data.payload && (data.payload.url || data.payload.image_url));
    if (u) setLightboxUrl(u);
  }, []);

  const closeLightbox = useCallback(() => setLightboxUrl(null), []);
  const closeDetails = useCallback(() => setSelected(null), []);


  // Save canvas state to backend (debounced)
  const scheduleSave = useCallback(() => {
    if (!conversationId) return;
    if (saveTimer.current) window.clearTimeout(saveTimer.current);
    saveTimer.current = window.setTimeout(async () => {
      try {
        const payload = {
          nodes: nodes.map((n) => ({ id: n.id, type: (n.data as any)?.type || n.type, position: n.position, data: { id: (n.data as any)?.id || n.id, title: (n.data as any)?.title, type: (n.data as any)?.type, thumbnail: (n.data as any)?.thumbnail, payload: (n.data as any)?.payload } })),
          edges,

          viewport: viewportRef.current || undefined,
        };
        await chatAPI.saveCanvasState(conversationId, payload);
      } catch (e) {
        console.debug("Canvas save skipped:", e);
      }
    }, 600) as unknown as number;
  }, [conversationId, nodes, edges]);

  const onConnect = useCallback((params: Edge | Connection) => {
    setEdges((eds) => addEdge(params, eds));
  }, []);

  const onMoveEnd = useCallback((_: any, viewport: { x: number; y: number; zoom: number }) => {
    viewportRef.current = viewport;
    scheduleSave();
  }, [scheduleSave]);

  useEffect(() => {
    // Save when nodes/edges change
    scheduleSave();
  }, [nodes, edges, scheduleSave]);

  // Close overlays with Escape key
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (lightboxUrl) setLightboxUrl(null);
        if (selected) setSelected(null);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [lightboxUrl, selected]);

  // Derive edges: link images to designs when payload indicates a source image
  useEffect(() => {
    try {
      const imgNodes = nodes.filter((n) => (n.data as any)?.type === 'image');
      const designNodes = nodes.filter((n) => (n.data as any)?.type === 'design');
      if (!imgNodes.length || !designNodes.length) return;

      const urlToImageIds = new Map<string, string[]>();
      for (const n of imgNodes) {
        const d: any = n.data || {};
        const url = d?.payload?.url || d?.thumbnail;
        if (!url) continue;
        const arr = urlToImageIds.get(url) || [];
        arr.push(n.id);
        urlToImageIds.set(url, arr);
      }

      const existing = new Set(edges.map((e) => `${e.source}->${e.target}`));
      const add: Edge[] = [];

      for (const dnode of designNodes) {
        const dp: any = (dnode.data as any)?.payload || {};
        const candidates = [dp.source_image_url, dp.input_image_url, dp.original_image_url, dp.image_input_url].filter(Boolean) as string[];
        for (const u of candidates) {
          const ids = urlToImageIds.get(u);
          if (!ids || !ids.length) continue;
          for (const imgId of ids) {
            const key = `${imgId}->${dnode.id}`;
            if (!existing.has(key)) {
              add.push({ id: `e-${imgId}-${dnode.id}`, source: imgId, target: dnode.id, type: 'smoothstep', label: 'derived from' });
              existing.add(key);
            }
          }
          break; // only link first match
        }
      }

      if (add.length) setEdges((prev) => [...prev, ...add]);
    } catch (e) {
      console.debug('derive edges skipped:', e);
    }
  }, [nodes, edges]);

  // Reflect busy node id into node data (not persisted)
  useEffect(() => {
    setNodes((prev) => prev.map((n) => ({ ...n, data: { ...(n.data as any), busy: n.id === busyNodeId } })));
  }, [busyNodeId]);

  return (
    <div className={"relative h-full w-full border-l border-gray-200 bg-gray-50 " + (className || "") }>
      <div className="px-3 py-2 text-xs text-gray-600 flex items-center gap-2">
        <span className="font-medium">Canvas</span>
        <span className="text-gray-400">(pan, zoom, drag; connect nodes)</span>
        {conversationId ? <span className="ml-auto text-gray-400">{conversationId.slice(0, 8)}</span> : null}
      </div>
      <ReactFlowProvider>
        <div className="h-[calc(100%-32px)]">
          <ReactFlow
            nodeTypes={nodeTypes}
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onMoveEnd={onMoveEnd}
            fitView
            defaultViewport={viewportRef.current || undefined as any}
          >
            <Background gap={16} size={1} color="#e5e7eb" />
            <MiniMap pannable zoomable />
            <Controls position="bottom-right" showInteractive={true} />
          </ReactFlow>
        </div>
      </ReactFlowProvider>
        {lightboxUrl && (
          <div
            className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4"
            onClick={closeLightbox}
          >
            <button
              className="absolute top-4 right-4 text-white"
              onClick={(e) => {
                e.stopPropagation();
                closeLightbox();
              }}
            >
              <X className="w-6 h-6" />
            </button>
            <img
              src={lightboxUrl}
              alt="Full size"
              className="max-w-full max-h-full object-contain"
              onClick={(e) => e.stopPropagation()}
            />
          </div>
        )}

        {selected && (
          <div className="absolute right-0 top-8 bottom-0 w-80 bg-white border-l shadow-lg z-10 overflow-y-auto">
            <div className="p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="text-sm font-semibold truncate">{selected.title}</div>
                <button onClick={closeDetails} className="p-1 rounded hover:bg-gray-100" title="Close">
                  <X className="w-4 h-4" />
                </button>
              </div>
              {selected.thumbnail ? (
                <img src={selected.thumbnail} alt={selected.title} className="w-full h-32 object-cover rounded mb-3" />
              ) : null}
              <div className="text-xs text-gray-500 mb-1">Type</div>
              <div className="text-sm mb-3">{selected.type}</div>
              {selected.payload ? (
                <div>
                  {/* Links extracted from payload */}
                  {(() => {
                    const links = collectUrlPairs(selected.payload);
                    return links.length ? (
                      <div className="mb-3">
                        <div className="text-xs text-gray-500 mb-1">Links</div>
                        <ul className="space-y-1">
                          {links.map((l, idx) => (
                            <li key={idx} className="text-[12px] truncate">
                              <a href={l.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline" title={`${l.key}: ${l.url}`}>
                                {l.key}: {l.url}
                              </a>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ) : null;
                  })()}

                  <div className="text-xs text-gray-500 mb-1">Details</div>
                  <pre className="text-[11px] bg-gray-50 p-2 rounded max-h-72 overflow-auto">{JSON.stringify(selected.payload, null, 2)}</pre>
                </div>
              ) : (
                <div className="text-xs text-gray-400">No extra details</div>
              )}
            </div>
          </div>
        )}

    </div>
  );

}

