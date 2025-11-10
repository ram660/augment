"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import type { Message } from "@/lib/types/chat";
import { ImageIcon, Layers, ShoppingCart, ReceiptText } from "lucide-react";

export interface CanvasPanelProps {
  conversationId?: string | null;
  messages: Message[];
  className?: string;
}

// A minimal, dependency-free draggable canvas for result "nodes"
export default function CanvasPanel({ conversationId, messages, className }: CanvasPanelProps) {
  // Extract nodes from assistant message metadata
  const nodes = useMemo(() => {
    const items: Array<{
      id: string;
      type: "image" | "design" | "product" | "estimate";
      title: string;
      thumbnail?: string;
      payload?: any;
    }> = [];
    for (const m of messages) {
      if (m.role !== "assistant") continue;
      const md = (m.metadata || {}) as any;
      const baseId = m.id.slice(0, 8);
      (md.images || []).forEach((url: string, idx: number) => {
        items.push({ id: `${baseId}-img-${idx}`,
          type: "image", title: `Image ${idx + 1}`, thumbnail: url, payload: { url } });
      });
      (md.designs || []).forEach((d: any, idx: number) => {
        items.push({ id: `${baseId}-des-${idx}`,
          type: "design", title: d?.title || `Design ${idx + 1}`,
          thumbnail: d?.thumbnail_url || d?.image_url, payload: d });
      });
      (md.products || []).forEach((p: any, idx: number) => {
        items.push({ id: `${baseId}-prd-${idx}`,
          type: "product", title: p?.name || `Product ${idx + 1}`,
          thumbnail: p?.image || p?.image_url, payload: p });
      });
      if (Array.isArray(md.cost_estimates) && md.cost_estimates.length) {
        items.push({ id: `${baseId}-est-0`, type: "estimate", title: md.cost_estimates[0]?.title || "Estimate", payload: md.cost_estimates[0] });
      }
    }
    return items;
  }, [messages]);

  // Persist positions in localStorage per conversation
  const storageKey = conversationId ? `hv-canvas-pos-${conversationId}` : undefined;
  const [positions, setPositions] = useState<Record<string, { x: number; y: number }>>({});

  useEffect(() => {
    if (!storageKey) return;
    try {
      const raw = localStorage.getItem(storageKey);
      if (raw) setPositions(JSON.parse(raw));
    } catch {}
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [storageKey]);

  useEffect(() => {
    if (!storageKey) return;
    try {
      localStorage.setItem(storageKey, JSON.stringify(positions));
    } catch {}
  }, [positions, storageKey]);

  // Arrange new nodes in a simple grid if they don't have positions yet
  useEffect(() => {
    if (!nodes.length) return;
    setPositions((prev) => {
      const next = { ...prev };
      let i = 0;
      for (const n of nodes) {
        if (!next[n.id]) {
          const col = i % 2;
          const row = Math.floor(i / 2);
          next[n.id] = { x: 24 + col * 180, y: 24 + row * 160 };
          i++;
        }
      }
      return next;
    });
  }, [nodes]);

  // Drag logic
  const containerRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<{ id: string; offsetX: number; offsetY: number } | null>(null);

  const onMouseDown = (e: React.MouseEvent, id: string) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const pos = positions[id] || { x: 0, y: 0 };
    dragRef.current = {
      id,
      offsetX: e.clientX - (rect.left + pos.x),
      offsetY: e.clientY - (rect.top + pos.y),
    };
  };

  const onMouseMove = (e: React.MouseEvent) => {
    if (!dragRef.current) return;
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const { id, offsetX, offsetY } = dragRef.current;
    const x = Math.max(0, e.clientX - rect.left - offsetX);
    const y = Math.max(0, e.clientY - rect.top - offsetY);
    setPositions((prev) => ({ ...prev, [id]: { x, y } }));
  };

  const onMouseUp = () => {
    dragRef.current = null;
  };

  const NodeCard: React.FC<{ n: { id: string; type: string; title: string; thumbnail?: string; payload?: any } }> = ({ n }) => {
    const pos = positions[n.id] || { x: 0, y: 0 };
    const icon =
      n.type === "image" ? <ImageIcon className="w-4 h-4" /> :
      n.type === "design" ? <Layers className="w-4 h-4" /> :
      n.type === "product" ? <ShoppingCart className="w-4 h-4" /> :
      <ReceiptText className="w-4 h-4" />;

    return (
      <div
        className="absolute w-40 select-none cursor-grab active:cursor-grabbing"
        style={{ transform: `translate(${pos.x}px, ${pos.y}px)` }}
        onMouseDown={(e) => onMouseDown(e, n.id)}
      >
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
          <div className="flex items-center gap-1 px-2 py-1.5 text-xs border-b bg-gray-50">
            {icon}
            <span className="truncate" title={n.title}>{n.title}</span>
          </div>
          {n.thumbnail ? (
            <img src={n.thumbnail} alt={n.title} className="w-full h-24 object-cover" />
          ) : (
            <div className="w-full h-24 flex items-center justify-center text-xs text-gray-500">No preview</div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className={"h-full w-full border-l border-gray-200 bg-gray-50 " + (className || "")}
         onMouseMove={onMouseMove}
         onMouseUp={onMouseUp}
    >
      <div className="px-3 py-2 text-xs text-gray-600 flex items-center gap-2">
        <span className="font-medium">Canvas</span>
        <span className="text-gray-400">(drag cards to arrange)</span>
        {conversationId ? <span className="ml-auto text-gray-400">{conversationId.slice(0, 8)}</span> : null}
      </div>
      <div ref={containerRef} className="relative h-[calc(100%-32px)] overflow-hidden">
        {nodes.map((n) => (
          <NodeCard key={n.id} n={n} />
        ))}
        {!nodes.length && (
          <div className="absolute inset-0 flex items-center justify-center text-gray-400 text-sm">
            Results from chat will appear here
          </div>
        )}
      </div>
    </div>
  );
}

