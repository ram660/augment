"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Sparkles, Wand2, MessageSquare } from "lucide-react";
import { ChatInterface } from "@/components/chat/ChatInterface";
import DesignStudioPage from "../design/page";
import { useQuery } from "@tanstack/react-query";
import { homesAPI } from "@/lib/api/homes";

export default function AssistantPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<"chat" | "transform">("chat");
  const [useDigitalTwin, setUseDigitalTwin] = useState<boolean>(true);
  const [selectedHomeId, setSelectedHomeId] = useState<string | undefined>(undefined);

  const { data: homes = [] } = useQuery({
    queryKey: ["homes"],
    queryFn: homesAPI.getAllHomes,
  });

  // Only show homes that are "Digital Twin ready" (have floor plan/images or non-zero completeness)
  const readyHomes = (homes || []).filter((h: any) => {
    const comp = h?.digital_twin_completeness ?? 0;
    const totalRooms = h?.total_rooms ?? 0;
    const totalImages = h?.total_images ?? 0;
    const hasFloorPlan = Boolean(h?.floor_plan_url);
    return comp > 0 || totalRooms > 0 || totalImages > 0 || hasFloorPlan;
  });

  useEffect(() => {
    const savedHomeId = typeof window !== 'undefined' ? localStorage.getItem('hv_selected_home_id') : null;
    const savedDT = typeof window !== 'undefined' ? localStorage.getItem('hv_use_digital_twin') : null;
    if (savedHomeId) setSelectedHomeId(savedHomeId);
    if (savedDT !== null) setUseDigitalTwin(savedDT === 'true');
  }, []);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      if (selectedHomeId) {
        localStorage.setItem('hv_selected_home_id', selectedHomeId);
      }
      localStorage.setItem('hv_use_digital_twin', String(useDigitalTwin));
    }
  }, [selectedHomeId, useDigitalTwin]);

  // If no saved selection, pick the first "ready" home by default
  useEffect(() => {
    if (!selectedHomeId && readyHomes && readyHomes.length > 0) {
      setSelectedHomeId(readyHomes[0].id as string);
    }
  }, [readyHomes, selectedHomeId]);


  const [persona, setPersona] = useState<'homeowner' | 'diy_worker' | 'contractor'>('homeowner');


  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-green-500 rounded-lg flex items-center justify-center">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">HomeView Assistant</h1>
            <p className="text-sm text-gray-600">Chat-first experience with quick access to AI transformations</p>
          </div>
        </div>
        <Link href="/dashboard/design" className="text-sm text-primary hover:underline">
          Open full Design Studio →
        </Link>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 bg-white p-1 rounded-xl border border-gray-200 w-fit">
        <button
          onClick={() => setActiveTab("chat")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === "chat" ? "bg-primary text-white shadow-sm" : "text-gray-700 hover:bg-gray-50"
          }`}
        >
          <MessageSquare className="w-4 h-4" /> Chat
        </button>
        <button
          onClick={() => setActiveTab("transform")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === "transform" ? "bg-primary text-white shadow-sm" : "text-gray-700 hover:bg-gray-50"
          }`}
        >
          <Wand2 className="w-4 h-4" /> Transformations
        </button>
      </div>

      {/* Digital Twin Controls (applies to Chat + Transformations) */}
      <div className="flex items-center gap-3 bg-white p-2 rounded-xl border border-gray-200 w-fit">
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={useDigitalTwin}
            onChange={(e) => setUseDigitalTwin(e.target.checked)}
            className="w-4 h-4"
          />
          <span>Digital Twin</span>
        </label>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-600">Home:</span>
          <select
            className="text-sm border rounded px-2 py-1"
            value={selectedHomeId || ''}
            onChange={(e) => setSelectedHomeId(e.target.value || undefined)}
            disabled={(readyHomes || []).length === 0}
          >
            <option value="">{(readyHomes || []).length === 0 ? 'No ready homes' : 'Select a home…'}</option>
            {(readyHomes || []).map((h: any) => (
              <option key={h.id} value={h.id}>{h.name}</option>
            ))}
          </select>
        </div>
        {useDigitalTwin && selectedHomeId && (
          <span className="text-xs px-2 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
            Using: {homes.find((h: any) => h.id === selectedHomeId)?.name}
          </span>
        )}
      </div>

      {/* Persona Toggle (applies to Chat) */}
      {activeTab === 'chat' && (
        <div className="flex items-center gap-2 bg-white p-1 rounded-xl border border-gray-200 w-fit">

          <button
            onClick={() => setPersona('homeowner')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              persona === 'homeowner' ? 'bg-blue-600 text-white shadow-sm' : 'text-gray-700 hover:bg-gray-50'
            }`}
          >
            Homeowner
          </button>
          <button
            onClick={() => setPersona('diy_worker')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              persona === 'diy_worker' ? 'bg-blue-600 text-white shadow-sm' : 'text-gray-700 hover:bg-gray-50'
            }`}
          >
            DIY Worker
          </button>
          <button
            onClick={() => setPersona('contractor')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              persona === 'contractor' ? 'bg-blue-600 text-white shadow-sm' : 'text-gray-700 hover:bg-gray-50'
            }`}
          >
            Contractor
          </button>
        </div>
      )}

      {/* Content */}
      <div className="min-h-[70vh]">
        {activeTab === "chat" ? (
          <div className="h-[70vh]">
            <ChatInterface persona={persona} homeId={useDigitalTwin ? selectedHomeId : undefined} />
          </div>
        ) : (
          <div className="space-y-6">
            <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 text-sm text-blue-900">
              Tip: Use the Chat tab to describe what you want changed. Then switch here to generate visual transformations.
            </div>
            {/* Reuse the existing Design Studio page content inline */}
            <DesignStudioPage />
          </div>
        )}
      </div>
    </div>
  );
}

