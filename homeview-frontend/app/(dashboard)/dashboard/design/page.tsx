'use client';

import { useMemo, useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Palette, Upload, Sparkles, Image as ImageIcon, ArrowRight } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { designAPI } from '@/lib/api/design';
import { homesAPI } from '@/lib/api/homes';

import { useSearchParams } from 'next/navigation';


export default function DesignStudioPage({ homeId, useDigitalTwin = false }: { homeId?: string; useDigitalTwin?: boolean; }) {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [selectedRoomImageId, setSelectedRoomImageId] = useState<string | null>(null);
  const [customPrompt, setCustomPrompt] = useState<string>('');
  const [isTransforming, setIsTransforming] = useState(false);
  const [resultUrls, setResultUrls] = useState<string[]>([]);
  const [useGrounding, setUseGrounding] = useState<boolean>(true);
  const [summary, setSummary] = useState<any | null>(null);
  const [products, setProducts] = useState<Array<any>>([]);
  const [sources, setSources] = useState<string[]>([]);

  const [groundingUnavailable, setGroundingUnavailable] = useState<boolean>(false);
  const [groundingNotice, setGroundingNotice] = useState<string | undefined>(undefined);
  // Preload from querystring (image or image_url) when arriving from chat
  const searchParams = useSearchParams();
  useEffect(() => {
    try {
      const imgUrl = searchParams.get('image_url');
      const imgId = searchParams.get('image');
      if (imgUrl) {
        setSelectedImage(imgUrl);
        setSelectedRoomImageId(null);
      }
      if (imgId) {
        setSelectedRoomImageId(imgId);
      }
    } catch {}
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);



  const [selectedVariationIndex, setSelectedVariationIndex] = useState<number>(0);
  useEffect(() => { setSelectedVariationIndex(0); }, [resultUrls]);

  // Angle range and lightbox
  const [anglePreset, setAnglePreset] = useState<'subtle'|'medium'>('subtle');
  const [lightboxUrl, setLightboxUrl] = useState<string | null>(null);
  const fetchToDataUrl = async (url: string): Promise<string> => {
    const res = await fetch(url);
    const blob = await res.blob();
    return await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  };

  // Stacking edits on current result + segmentation base tracking
  const [stackOnResult, setStackOnResult] = useState<boolean>(false);
  const [segBaseDataUrl, setSegBaseDataUrl] = useState<string | null>(null);


  // Helpers for product shelf UI
  const getDomainFromUrl = (u: string): string => {
    try {
      const host = new URL(u).hostname || '';
      return host.replace(/^www\./, '');
    } catch {
      return '';
    }
  };
  const isCADomain = (u: string): boolean => {
    try {
      const host = new URL(u).hostname.toLowerCase();
      return host.endsWith('.ca');
    } catch {
      return false;
    }
  };
  const getFaviconUrl = (u: string): string => {
    const d = getDomainFromUrl(u);
    return d ? `https://www.google.com/s2/favicons?domain=${encodeURIComponent(d)}&sz=64` : '';
  };

  // A–D tools state (Virtual Staging, Unstaging, Masked Edit, Segmentation)
  const [vsStylePreset, setVsStylePreset] = useState<string>('modern');
  const [vsStylePrompt, setVsStylePrompt] = useState<string>('');
  const [vsDensity, setVsDensity] = useState<'light'|'medium'|'heavy'>('medium');
  const [vsLockEnvelope, setVsLockEnvelope] = useState<boolean>(true);
  const [unstageStrength, setUnstageStrength] = useState<'light'|'medium'|'full'>('medium');
  const [maskDataUrl, setMaskDataUrl] = useState<string | null>(null);
  const [segmentClass, setSegmentClass] = useState<string>('floors');
  const [replacePrompt, setReplacePrompt] = useState<string>('');

  const [ideas, setIdeas] = useState<string[]>([]);
  const [ideasByTheme, setIdeasByTheme] = useState<Record<string, string[]>>({});
  const [styleTransformations, setStyleTransformations] = useState<Array<{ label: string; prompt: string }>>([]);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const analysisCacheRef = useRef<Record<string, { summary: any; ideas: string[]; ideasByTheme?: Record<string, string[]>; styleTransformations?: Array<{ label: string; prompt: string }> }>>({});

  // Auto-analyze selected Digital Twin image to personalize idea chips (with simple cache)
  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      if (!selectedRoomImageId) {
        setIdeas([]);
        setIdeasByTheme({});
        setSummary(null);
        return;
      }

      // Cache hit
      const cached = analysisCacheRef.current[selectedRoomImageId];
      if (cached) {
        setSummary(cached.summary || null);
        setIdeas(cached.ideas || []);
        setIdeasByTheme(cached.ideasByTheme || {});
        setStyleTransformations(cached.styleTransformations || []);
        return;
      }

      try {
        setIsAnalyzing(true);
        const resp = await designAPI.analyzeImage(selectedRoomImageId, 5);
        if (!cancelled) {
          setSummary(resp.summary || null);
          setIdeas(resp.ideas || []);
          const normalizedThemes: Record<string, string[]> = Object.fromEntries(
            Object.entries(resp.ideas_by_theme ?? {}).map(([k, v]) => [k, Array.isArray(v) ? v : []])
          );
          setIdeasByTheme(normalizedThemes);
          setStyleTransformations(resp.style_transformations || []);
          analysisCacheRef.current[selectedRoomImageId] = {
            summary: resp.summary || null,
            ideas: resp.ideas || [],
            ideasByTheme: normalizedThemes,
            styleTransformations: resp.style_transformations || [],
          };
        }
      } catch (e) {
        if (!cancelled) {
          setIdeas([]);
          setIdeasByTheme({});
        }
      } finally {
        if (!cancelled) setIsAnalyzing(false);
      }
    };
    run();
    return () => { cancelled = true; };
  }, [selectedRoomImageId]);

  // When user uploads an image (no Digital Twin), auto-analyze to suggest idea chips
  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      if (!selectedImage || selectedRoomImageId) return;
      try {
        setIsAnalyzing(true);
        setIdeas([]);
        setIdeasByTheme({});
        const resp = await designAPI.analyzeUploadedImage(selectedImage, 5);
        if (cancelled) return;
        setSummary(resp.summary || null);
        setIdeas(resp.ideas || []);
        const normalizedThemes: Record<string, string[]> = Object.fromEntries(
          Object.entries(resp.ideas_by_theme ?? {}).map(([k, v]) => [k, Array.isArray(v) ? v : []])
        );
        setIdeasByTheme(normalizedThemes);
        setStyleTransformations(resp.style_transformations || []);
      } catch (e) {
        if (!cancelled) {
          setIdeas([]);
          setIdeasByTheme({});
        }
      } finally {
        if (!cancelled) setIsAnalyzing(false);
      }
    };
    run();
    return () => { cancelled = true; };
  }, [selectedImage, selectedRoomImageId]);



  // Fetch user's transformations
  const { data: transformations = [], isLoading } = useQuery({
    queryKey: ['transformations'],
    queryFn: designAPI.getAllTransformations,
  });

  // If Digital Twin is enabled and a home is selected, fetch it for display context
  const { data: selectedHome } = useQuery({
    queryKey: ['home', homeId],
    queryFn: () => homesAPI.getHome(homeId!),
    enabled: !!homeId && !!useDigitalTwin,
  });

  const dbImages = useMemo(() => {
    if (!(useDigitalTwin && selectedHome)) return [] as Array<{ url: string; roomName?: string; id?: string }>;
    const rooms = (selectedHome as any)?.rooms || [];
    const images = rooms.flatMap((r: any) => (r.images || [])
      .filter((img: any) => img.image_type === 'original')
      .map((img: any) => ({ url: img.image_url as string, roomName: r?.name as string, id: img?.id as string }))
    );
    return images as Array<{ url: string; roomName?: string; id?: string }>;

  }, [useDigitalTwin, selectedHome]);
  const [roomFilter, setRoomFilter] = useState<string>('all');
  const [page, setPage] = useState<number>(1);
  const pageSize = 9;

  const roomGroups = useMemo(() => {
    const map = new Map<string, number>();
    for (const img of dbImages) {
      const key = img.roomName || 'Unknown';
      map.set(key, (map.get(key) ?? 0) + 1);
    }

    return Array.from(map.entries()).map(([name, count]) => ({ name, count }));

  }, [dbImages]);

  const filteredImages = useMemo(() => {
    if (roomFilter === 'all') return dbImages;
    return dbImages.filter((img) => (img.roomName || 'Unknown') === roomFilter);
  }, [dbImages, roomFilter]);

  const totalPages = Math.max(1, Math.ceil(filteredImages.length / pageSize));
  const pagedImages = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredImages.slice(start, start + pageSize);

  }, [filteredImages, page]);


  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setSelectedImage(reader.result as string);
        setSelectedRoomImageId(null); // uploads not yet supported by backend transformations
        setResultUrls([]);
      };

      reader.readAsDataURL(file);
    }
  };

  const handleTransform = async () => {
    if (!selectedImage) return;
    if (!customPrompt.trim()) return;

    setIsTransforming(true);
    setResultUrls([]);
    setSummary(null);
    setProducts([]);
    setSources([]);
    setGroundingUnavailable(false);
    setGroundingNotice(undefined);
    try {
      const prompt = customPrompt.trim();

      let resp;
      if (stackOnResult && resultUrls.length > 0) {
        const dataUrl = await fetchToDataUrl(resultUrls[selectedVariationIndex]);
        resp = await designAPI.transformPromptedUpload(dataUrl, prompt, { numVariations: 4, enableGrounding: useGrounding });
      } else {
        resp = selectedRoomImageId
          ? await designAPI.transformPrompted(selectedRoomImageId, prompt, { numVariations: 4, enableGrounding: useGrounding })
          : await designAPI.transformPromptedUpload(selectedImage as string, prompt, { numVariations: 4, enableGrounding: useGrounding });
      }

      const images = (resp as any).image_urls ?? [];
      setResultUrls(images);
      setSummary((resp as any).summary || null);
      setProducts(((resp as any).products || []) as any[]);
      setSources(((resp as any).sources || []) as string[]);
      setGroundingUnavailable(Boolean((resp as any).grounding_unavailable));
      setGroundingNotice((resp as any).grounding_notice);
    } catch (err) {
      console.error('Transformation error:', err);
      alert('Failed to transform image');
    } finally {
      setIsTransforming(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        {useDigitalTwin && homeId && selectedHome && (
          <div className="mt-2 flex items-center gap-2">
            <span className="text-xs px-2 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
              Digital Twin: Using {(selectedHome as any)?.name}
            </span>
            {(((selectedHome as any)?.total_images ?? 0) > 0) && (
              <span className="text-xs text-gray-500">
                {((selectedHome as any)?.total_images ?? 0)} images · {((selectedHome as any)?.total_rooms ?? 0)} rooms
              </span>
            )}
          </div>
        )}

        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
            <Palette className="w-6 h-6 text-white" />
          </div>
          AI Design Studio
        </h1>
        <p className="text-gray-600 mt-2">
          Transform your rooms with AI-powered design in 40+ styles
        </p>
      </div>

      {/* Main Design Interface */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Panel - Upload & Original */}
        <Card>
          <CardHeader>
            <CardTitle>Original Image</CardTitle>
            <CardDescription>Upload a photo of your room</CardDescription>
          </CardHeader>

          <CardContent>
            {selectedImage ? (
              <div className="space-y-4">
                <div className="relative aspect-video bg-gray-100 rounded-lg overflow-hidden">
                  <img
                    src={selectedImage}
                    alt="Original room"

                    className="w-full h-full object-cover"
                  />
                </div>
                {/* Chat-style composer below the image */}
                <div className="space-y-3">
                  {styleTransformations.length > 0 && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-[11px] text-gray-500 w-16">Styles</span>
                        {styleTransformations.map((st) => (
                          <button
                            key={`style-${st.label}`}
                            type="button"
                            className="text-xs px-3 py-1.5 rounded-full border bg-amber-50 hover:bg-amber-100"
                            onClick={() => setCustomPrompt(st.prompt)}
                            title={st.prompt}
                          >
                            {st.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {Object.values(ideasByTheme || {}).some((arr) => (arr?.length ?? 0) > 0) ? (
                    <div className="space-y-2">
                      {['color','flooring','lighting','decor','other'].map((cat) => {
                        const items = (ideasByTheme?.[cat] || []) as string[];
                        if (!items.length) return null;
                        const label = cat.charAt(0).toUpperCase() + cat.slice(1);
                        return (
                          <div key={cat} className="flex items-center gap-2 flex-wrap">
                            <span className="text-[11px] text-gray-500 w-16">{label}</span>
                            {items.map((idea) => (
                              <button
                                key={`${cat}-${idea}`}
                                type="button"
                                className="text-xs px-2.5 py-1 rounded-full border bg-white hover:bg-gray-50"
                                onClick={() => setCustomPrompt((prev) => (prev ? `${prev}\n${idea}` : idea))}
                              >
                                {idea}
                              </button>

                            ))}
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="flex flex-wrap items-center gap-2">
                      {isAnalyzing && (
                        <span className="text-[11px] text-gray-500">Analyzing image for suggestions…</span>
                      )}
                      {(ideas.length ? ideas : [
                        'Change walls to soft sage green',
                        'Replace with light oak hardwood',
                        'Add matte-black pendant lights',
                        'Warm neutral palette',
                      ]).map((idea) => (
                        <button
                          key={idea}
                          type="button"
                          className="text-xs px-2.5 py-1 rounded-full border bg-white hover:bg-gray-50"
                          onClick={() => setCustomPrompt((prev) => (prev ? `${prev}\n${idea}` : idea))}
                        >
                          {idea}
                        </button>
                      ))}
                    </div>
                  )}
                  <div className="flex items-center gap-2">
                    <input
                      id="use-grounding"
                      type="checkbox"
                      className="h-4 w-4"
                      checked={useGrounding}
                      onChange={(e) => setUseGrounding(e.target.checked)}
                    />
                    <label htmlFor="use-grounding" className="text-xs text-gray-600">
                      Use Google Search grounding to suggest products
                    </label>
                  </div>
                </div>
                <div className="mt-3">
                  <label className="block text-xs text-gray-600 mb-1">Describe your changes</label>
                  <textarea
                    className="w-full border rounded p-2 text-sm min-h-[80px]"
                    value={customPrompt}
                    onChange={(e) => setCustomPrompt(e.target.value)}
                    placeholder="e.g., Paint walls soft sage, add matte black pendant, light oak flooring"
                  />
                </div>

                <div className="mt-3 flex items-center gap-2">
                  <Button
                    onClick={handleTransform}
                    disabled={isTransforming || !customPrompt.trim() || (!selectedImage && !(stackOnResult && resultUrls.length > 0))}
                  >
                    <Sparkles className="w-4 h-4 mr-2" />
                    Transform
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setSelectedImage(null)}
                  >
                    Change Image
                  </Button>
                </div>
                <div className="mt-2 flex items-center gap-2">
                  <label className="flex items-center gap-2 text-xs">
                    <input
                      type="checkbox"
                      checked={stackOnResult}
                      onChange={(e) => setStackOnResult(e.target.checked)}
                      disabled={resultUrls.length === 0}
                    />
                    Stack edits on current result
                  </label>
                  {stackOnResult && (
                    <span className="text-[11px] text-gray-500">Uses the active variation as the base for the next tools.</span>
                  )}
                </div>
                {/* Angles & Quality */}
                <div className="mt-6 rounded border p-3">
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-medium">Angles & Quality</div>
                    <div className="flex items-center gap-2">
                      <label className="text-xs text-gray-600">Range</label>
                      <select
                        className="text-xs border rounded px-1.5 py-1"
                        value={anglePreset}
                        onChange={(e) => setAnglePreset(e.target.value as 'subtle'|'medium')}
                      >
                        <option value="subtle">Subtle (±6°)</option>
                        <option value="medium">Medium (±12°)</option>
                      </select>
                    </div>
                  </div>
                  <p className="text-xs text-gray-600 mt-1 mb-2">Generate small viewpoint shifts or enhance a blurry upload before transforming.</p>
                  <div className="flex flex-wrap items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={!selectedImage || isTransforming}
                      onClick={async () => {
                        if (!selectedImage) return;
                        try {
                          setIsTransforming(true);
                          const yawDegrees = anglePreset === 'subtle' ? 6 : 12;
                          const pitchDegrees = anglePreset === 'subtle' ? 4 : 8;
                          const numAngles = anglePreset === 'subtle' ? 3 : 4;
                          const resp = await designAPI.multiAngleUpload(selectedImage, { numAngles, yawDegrees, pitchDegrees });
                          setResultUrls((resp as any).image_urls ?? []);
                        } catch (e) {
                          alert('Failed to generate angles');
                        } finally {
                          setIsTransforming(false);
                        }
                      }}
                    >Generate multi-angles</Button>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={resultUrls.length === 0 || isTransforming}
                      onClick={async () => {
                        try {
                          setIsTransforming(true);
                          const yawDegrees = anglePreset === 'subtle' ? 6 : 12;
                          const pitchDegrees = anglePreset === 'subtle' ? 4 : 8;
                          const numAngles = anglePreset === 'subtle' ? 3 : 4;
                          const dataUrl = await fetchToDataUrl(resultUrls[selectedVariationIndex]);
                          const resp = await designAPI.multiAngleUpload(dataUrl, { numAngles, yawDegrees, pitchDegrees });
                          setResultUrls((resp as any).image_urls ?? []);
                        } catch (e) {
                          alert('Failed to generate angles from current result');
                        } finally {
                          setIsTransforming(false);
                        }
                      }}
                    >Angles from this result</Button>
                    <Button
                      size="sm"
                      disabled={!selectedImage || isTransforming}
                      onClick={async () => {
                        if (!selectedImage) return;
                        try {
                          setIsTransforming(true);
                          const resp = await designAPI.enhanceUpload(selectedImage, { upscale2x: true });
                          const first = (resp as any).image_urls?.[0];
                          if (first) {
                            setSelectedImage(first);
                            setResultUrls([]);
                            alert('Image enhanced. Using enhanced copy for next transforms.');
                          }
                        } catch (e) {
                          alert('Failed to enhance image');
                        } finally {
                          setIsTransforming(false);
                        }
                      }}
                    >Enhance quality</Button>
                  </div>
                </div>

                {/* Studio Tools (beta): Virtual Staging, Unstaging, Segmentation, Masked Edit */}
                <div className="mt-6 border-t pt-4">
                  <div className="text-[11px] text-gray-500 uppercase tracking-wide mb-2">Studio Tools (beta)</div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Virtual Staging */}
                    <div className="rounded border p-3">
                      <div className="text-sm font-medium mb-2">Virtual Staging</div>
                      <div className="flex items-center gap-2">
                        <select
                          className="text-xs border rounded px-1.5 py-1"
                          value={vsStylePreset}
                          onChange={(e) => setVsStylePreset(e.target.value)}
                        >
                          <option value="modern">Modern</option>
                          <option value="minimalist">Minimalist</option>
                          <option value="traditional">Traditional</option>
                          <option value="scandinavian">Scandinavian</option>
                          <option value="bohemian">Bohemian</option>
                        </select>
                        <select
                          className="text-xs border rounded px-1.5 py-1"
                          value={vsDensity}
                          onChange={(e) => setVsDensity(e.target.value as any)}
                        >
                          <option value="light">Light</option>
                          <option value="medium">Medium</option>
                          <option value="heavy">Heavy</option>
                        </select>
                        <label className="flex items-center gap-1 text-xs">
                          <input type="checkbox" checked={vsLockEnvelope} onChange={(e) => setVsLockEnvelope(e.target.checked)} />
                          Lock envelope
                        </label>
                      </div>
                      <input
                        className="mt-2 w-full border rounded px-2 py-1 text-xs"
                        placeholder="Optional: add style prompt (e.g., coastal, mid-century sofa)"
                        value={vsStylePrompt}
                        onChange={(e) => setVsStylePrompt(e.target.value)}
                      />
                      <div className="mt-2">
                        <Button
                          size="sm"
                          onClick={async () => {
                            if (!selectedImage) return;
                            try {
                              setIsTransforming(true);
                              let resp;
                              if (stackOnResult && resultUrls.length > 0) {
                                const base = await fetchToDataUrl(resultUrls[selectedVariationIndex]);
                                resp = await designAPI.virtualStagingUpload(base, {
                                  style_preset: vsStylePreset,
                                  style_prompt: vsStylePrompt || undefined,
                                  furniture_density: vsDensity,
                                  lock_envelope: vsLockEnvelope,
                                  num_variations: 3,
                                  enableGrounding: useGrounding,
                                });
                              } else {
                                resp = selectedRoomImageId
                                  ? await designAPI.virtualStaging(selectedRoomImageId, {
                                      style_preset: vsStylePreset,
                                      style_prompt: vsStylePrompt || undefined,
                                      furniture_density: vsDensity,
                                      lock_envelope: vsLockEnvelope,
                                      num_variations: 3,
                                    })
                                  : await designAPI.virtualStagingUpload(selectedImage as string, {
                                      style_preset: vsStylePreset,
                                      style_prompt: vsStylePrompt || undefined,
                                      furniture_density: vsDensity,
                                      lock_envelope: vsLockEnvelope,
                                      num_variations: 3,
                                      enableGrounding: useGrounding,
                                    });
                              }
                              setResultUrls((resp as any).image_urls ?? []);
                              setSummary((resp as any).summary || null);
                              setProducts(((resp as any).products || []) as any[]);
                              setSources(((resp as any).sources || []) as string[]);
                              setGroundingUnavailable(Boolean((resp as any).grounding_unavailable));
                              setGroundingNotice((resp as any).grounding_notice);
                            } catch (e) {
                              alert('Virtual staging failed');
                            } finally {
                              setIsTransforming(false);
                            }
                          }}
                          disabled={isTransforming || (!selectedImage && !(stackOnResult && resultUrls.length > 0))}
                        >Run Staging</Button>
                      </div>
                    </div>

                    {/* Unstaging */}
                    <div className="rounded border p-3">
                      <div className="text-sm font-medium mb-2">Unstaging</div>
                      <div className="flex items-center gap-2">
                        <label className="text-xs text-gray-600">Strength</label>
                        <select
                          className="text-xs border rounded px-1.5 py-1"
                          value={unstageStrength}
                          onChange={(e) => setUnstageStrength(e.target.value as any)}
                        >
                          <option value="light">Light</option>
                          <option value="medium">Medium</option>
                          <option value="full">Full</option>
                        </select>
                      </div>
                      <div className="mt-2">
                        <Button
                          size="sm"
                          onClick={async () => {
                            if (!selectedImage) return;
                            try {
                              setIsTransforming(true);
                              let resp;
                              if (stackOnResult && resultUrls.length > 0) {
                                const base = await fetchToDataUrl(resultUrls[selectedVariationIndex]);
                                resp = await designAPI.unstageUpload(base, {
                                  strength: unstageStrength,
                                  num_variations: 3,
                                });
                              } else {
                                resp = selectedRoomImageId
                                  ? await designAPI.unstage(selectedRoomImageId, {
                                      strength: unstageStrength,
                                      num_variations: 3,
                                    })
                                  : await designAPI.unstageUpload(selectedImage as string, {
                                      strength: unstageStrength,
                                      num_variations: 3,
                                    });
                              }
                              setResultUrls((resp as any).image_urls ?? []);
                            } catch (e) {
                              alert('Unstaging failed');
                            } finally {
                              setIsTransforming(false);
                            }
                          }}
                          disabled={isTransforming || (!selectedImage && !(stackOnResult && resultUrls.length > 0))}
                        >Run Unstaging</Button>
                      </div>
                    </div>

                    {/* Segmentation + Masked Edit */}
                    <div className="rounded border p-3 md:col-span-2">
                      <div className="text-sm font-medium mb-2">Segmentation + Masked Edit</div>
                      <div className="flex flex-wrap items-center gap-2">
                        <label className="text-xs text-gray-600">Target</label>
                        <select
                          className="text-xs border rounded px-1.5 py-1"
                          value={segmentClass}
                          onChange={(e) => setSegmentClass(e.target.value)}
                        >
                          <option value="floors">Floors</option>
                          <option value="walls">Walls</option>
                          <option value="cabinets">Cabinets</option>
                          <option value="countertops">Countertops</option>
                          <option value="backsplash">Backsplash</option>
                          <option value="windows">Windows</option>
                          <option value="doors">Doors</option>
                          <option value="furniture">Furniture</option>
                          <option value="decor">Decor</option>
                          <option value="appliances">Appliances</option>
                          <option value="other">Other</option>
                        </select>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={async () => {
                            if (!selectedImage && !(stackOnResult && resultUrls.length > 0)) return;
                            try {
                              let seg;
                              if (stackOnResult && resultUrls.length > 0) {
                                const base = await fetchToDataUrl(resultUrls[selectedVariationIndex]);
                                setSegBaseDataUrl(base);
                                seg = await designAPI.segmentUpload(base, { segment_class: segmentClass, num_masks: 1 });
                              } else {
                                seg = selectedRoomImageId
                                  ? await designAPI.segment(selectedRoomImageId, { segment_class: segmentClass, num_masks: 1 })
                                  : await designAPI.segmentUpload(selectedImage as string, { segment_class: segmentClass, num_masks: 1 });
                                setSegBaseDataUrl(selectedImage as string);
                              }
                              const first = seg.mask_data_urls?.[0] || null;
                              setMaskDataUrl(first);
                            } catch (e) {
                              alert('Segmentation failed');
                            }
                          }}
                          disabled={!selectedImage && !(stackOnResult && resultUrls.length > 0)}
                        >AI Segment</Button>
                      </div>

                      {maskDataUrl && (
                        <div className="mt-3">
                          <div className="text-[11px] text-gray-500 mb-1">Mask preview</div>
                          <div className="flex items-start gap-3">
                            <div className="w-1/2">
                              <img src={(segBaseDataUrl || selectedImage) || ''} alt="original" className="w-full rounded border" />
                            </div>
                            <div className="w-1/2">
                              <img src={maskDataUrl} alt="mask" className="w-full rounded border" />
                            </div>
                          </div>
                          <div className="mt-3 flex items-center gap-2">
                            <select
                              className="text-xs border rounded px-1.5 py-1"
                              value={replacePrompt ? 'replace' : 'remove'}
                              onChange={(e) => { if (e.target.value === 'replace') { setReplacePrompt(replacePrompt || 'new item'); } else { setReplacePrompt(''); } }}
                            >
                              <option value="remove">Remove within mask</option>
                              <option value="replace">Replace within mask</option>
                            </select>
                            {replacePrompt !== '' && (
                              <input
                                className="flex-1 border rounded px-2 py-1 text-xs"
                                placeholder="Describe replacement (e.g., matte black pull handles)"
                                value={replacePrompt}
                                onChange={(e) => setReplacePrompt(e.target.value)}
                              />
                            )}
                            <Button
                              size="sm"
                              onClick={async () => {
                                if (!selectedImage || !maskDataUrl) return;
                                try {
                                  setIsTransforming(true);
                                      let baseImage: string | null = null;
                                  if (segBaseDataUrl) {
                                    baseImage = segBaseDataUrl;
                                  } else if (stackOnResult && resultUrls.length > 0) {
                                    baseImage = await fetchToDataUrl(resultUrls[selectedVariationIndex]);
                                  } else {
                                    baseImage = selectedImage as string;
                                  }
                                  const useUpload = stackOnResult || !!segBaseDataUrl || !selectedRoomImageId;
                                  const resp = useUpload
                                    ? await designAPI.editWithMaskUpload(baseImage as string, maskDataUrl, {
                                        operation: replacePrompt ? 'replace' : 'remove',
                                        replacement_prompt: replacePrompt || undefined,
                                        num_variations: 3,
                                      })
                                    : await designAPI.editWithMask(selectedRoomImageId as string, maskDataUrl, {
                                        operation: replacePrompt ? 'replace' : 'remove',
                                        replacement_prompt: replacePrompt || undefined,
                                        num_variations: 3,
                                      });
                                  setResultUrls((resp as any).image_urls ?? []);
                                } catch (e) {
                                  alert('Masked edit failed');

                                } finally {
                                  setIsTransforming(false);
                                }
                              }}
                              disabled={(isTransforming || !maskDataUrl) || (!selectedImage && !(stackOnResult && resultUrls.length > 0))}
                            >Apply Mask Edit</Button>
                          </div>



                        </div>
                      )}
                    </div>
                  </div>
                </div>




              </div>
            ) : (<>
              <label className="block">
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="hidden"
                />
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center cursor-pointer hover:border-primary hover:bg-blue-50 transition-colors">
                  <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-700 font-medium mb-1">
                    Click to upload room photo
                  </p>
                  <p className="text-sm text-gray-500">
                    PNG, JPG up to 10MB
                  </p>
                </div>
              </label>
              {useDigitalTwin && dbImages.length > 0 && (
                <div className="mt-6">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-xs text-gray-600">Or pick a room photo from your home</div>
                    <div className="flex items-center gap-2">
                      <label className="text-xs text-gray-500">Room</label>
                      <select
                        className="text-xs border rounded px-1.5 py-1"
                        value={roomFilter}
                        onChange={(e) => { setRoomFilter(e.target.value); setPage(1); }}
                      >
                        <option value="all">All ({dbImages.length})</option>
                        {roomGroups.map((g) => (
                          <option key={g.name} value={g.name}>
                            {g.name} ({g.count})

                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {pagedImages.map((img) => (
                      <button
                        key={img.id || img.url}
                        className="relative aspect-video rounded-md overflow-hidden border hover:ring-2 hover:ring-primary"
                        onClick={() => { setSelectedImage(img.url); setSelectedRoomImageId(img.id || null); setResultUrls([]); }}
                      >
                        <img src={img.url} alt={img.roomName || 'Room'} className="w-full h-full object-cover" />
                        {img.roomName && (
                          <span className="absolute bottom-1 left-1 text-[10px] bg-black/60 text-white px-1.5 py-0.5 rounded">
                            {img.roomName}
                          </span>
                        )}
                      </button>
                    ))}
                  </div>
                  {totalPages > 1 && (
                    <div className="mt-3 flex items-center justify-between">
                      <span className="text-[11px] text-gray-500">
                        Showing {((page - 1) * pageSize) + 1}-{Math.min(page * pageSize, filteredImages.length)} of {filteredImages.length}
                      </span>
                      <div className="flex items-center gap-2">
                        <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))}>Prev</Button>
                        <span className="text-xs">{page}/{totalPages}</span>
                        <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => Math.min(totalPages, p + 1))}>Next</Button>
                      </div>
                    </div>
                  )}

                </div>
              )}

              </>

            )}
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={resultUrls.length === 0 || isTransforming}
                    onClick={async () => {
                      try {
                        const dataUrl = await fetchToDataUrl(resultUrls[selectedVariationIndex]);
                        setSelectedImage(dataUrl);
                        setSelectedRoomImageId(null);
                        setResultUrls([]);
                        setStackOnResult(false);
                        alert('Using this result as the starting point for next edits.');
                      } catch (e) {
                        alert('Failed to load result as input');
                      }
                    }}
                  >Use this result for next edit</Button>
                </div>

          </CardContent>
        </Card>

        {/* Right Panel - Transformed */}
        <Card>
          <CardHeader>
            <CardTitle>AI Transformation</CardTitle>
            <CardDescription>See your room in a new style</CardDescription>
          </CardHeader>
          <CardContent>
            {isTransforming ? (
              <div className="aspect-video bg-gradient-to-br from-purple-100 to-pink-100 rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <Sparkles className="w-12 h-12 text-purple-600 mx-auto mb-4 animate-pulse" />
                  <p className="text-purple-900 font-medium">Transforming your room...</p>
                  <p className="text-sm text-purple-700 mt-1">This may take a few moments</p>
                </div>
              </div>
            ) : resultUrls.length > 0 ? (
              <div className="space-y-4">
                <div className="aspect-video bg-gray-100 rounded-lg overflow-hidden cursor-zoom-in" onClick={() => setLightboxUrl(resultUrls[selectedVariationIndex])}>
                  <img src={resultUrls[selectedVariationIndex]} alt={`Transformed ${selectedVariationIndex+1}`} className="w-full h-full object-cover" />
                </div>
                {resultUrls.length > 1 && (
                  <div className="grid grid-cols-4 gap-2">
                    {resultUrls.map((u, idx) => (
                      <button
                        key={u}
                        onClick={() => setSelectedVariationIndex(idx)}
                        className={`relative rounded overflow-hidden border ${idx === selectedVariationIndex ? 'ring-2 ring-primary' : 'hover:ring-2 hover:ring-gray-300'}`}
                        title={`View variation ${idx+1}`}
                      >
                        <img src={u} alt={`Variation ${idx+1}`} className="w-full h-20 object-cover" />
                        {idx === selectedVariationIndex && (
                          <span className="absolute top-1 right-1 text-[10px] bg-primary text-white px-1.5 py-0.5 rounded">Active</span>
                        )}
                      </button>
                    ))}
                  </div>
                )}
                {summary && (
                  <div className="rounded-lg border p-3">
                    <div className="text-sm font-medium">Design summary</div>
                    {summary.description && (
                      <p className="text-sm text-gray-600 mt-1">{summary.description}</p>
                    )}
                    {Array.isArray(summary.colors) && summary.colors.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {summary.colors.map((c: any, idx: number) => (
                          <span key={idx} className="inline-flex items-center gap-2 text-xs px-2 py-1 border rounded">
                            <span className="inline-block w-3 h-3 rounded" style={{ backgroundColor: c.hex || '#ddd' }} />
                            {c.name || c.hex}
                          </span>
                        ))}
                      </div>
                    )}
                    {Array.isArray(summary.materials) && summary.materials.length > 0 && (
                      <div className="mt-2 text-xs text-gray-700">
                        <span className="font-medium">Materials:</span> {summary.materials.join(', ')}
                      </div>
                    )}
                    {Array.isArray(summary.styles) && summary.styles.length > 0 && (
                      <div className="mt-1 text-xs text-gray-700">
                        <span className="font-medium">Styles:</span> {summary.styles.join(', ')}
                      </div>
                    )}
                  </div>
                )}
                {groundingUnavailable && (
                  <div className="rounded-md border border-amber-200 bg-amber-50 text-amber-800 text-xs px-2 py-1">
                    {groundingNotice || 'Google Search grounding is unavailable; showing AI suggestions without live web sources.'}
                  </div>
                )}
                {products.length > 0 && (
                  <div className="rounded-lg border p-3">
                    <div className="text-sm font-medium mb-2">Shop these items</div>
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                      {products.map((p: any, i: number) => {
                        const href = (p.url as string) || '#';
                        const domain = getDomainFromUrl(href);
                        const isCA = isCADomain(href);
                        const thumb = (p.image_url as string) || getFaviconUrl(href);
                        return (
                          <a key={i} href={href} target="_blank" rel="noreferrer" className="group block border rounded-md overflow-hidden hover:shadow-sm transition">
                            <div className="aspect-[4/3] bg-gray-100 flex items-center justify-center">
                              {thumb ? (
                                <img src={thumb} alt={p.name} className="h-full w-full object-cover" />
                              ) : (
                                <div className="text-xs text-gray-400 p-2 text-center">No image</div>
                              )}
                            </div>
                            <div className="p-2">
                              <div className="text-xs font-medium line-clamp-2">{p.name}</div>
                              <div className="mt-1 flex items-center gap-1 flex-wrap">
                                {p.price_estimate && (
                                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                                    {p.price_estimate}
                                  </span>
                                )}
                                {isCA && (
                                  <span className="text-[10px] px-1 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">CAD</span>
                                )}
                                {isCA && (
                                  <span className="text-[10px] px-1 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">.ca</span>
                                )}
                                {p.category && (
                                  <span className="text-[10px] px-1 py-0.5 rounded bg-gray-50 text-gray-600 border border-gray-200">{p.category}</span>
                                )}
                              </div>
                              <div className="mt-1 text-[10px] text-gray-500">{domain}</div>
                            </div>
                          </a>
                        );
                      })}
                    </div>
                    {sources.length > 0 && (
                      <div className="text-[11px] text-gray-500 mt-2">Sources: {sources.slice(0, 3).join(', ')}</div>
                    )}
                  </div>
                )}

                {false && (
                  <div className="rounded-lg border p-3">
                    <div className="text-sm font-medium">Product suggestions</div>
                    <ul className="list-disc pl-5 text-sm mt-1 space-y-1">
                      {products.map((p: any, i: number) => (
                        <li key={i}>
                          <a href={p.url} target="_blank" rel="noreferrer" className="text-primary hover:underline">{p.name}</a>
                          {p.category ? ` · ${p.category}` : ''}
                          {p.brief_reason ? ` — ${p.brief_reason}` : ''}
                        </li>
                      ))}
                    </ul>
                    {sources.length > 0 && (
                      <div className="text-[11px] text-gray-500 mt-2">Sources: {sources.slice(0, 3).join(', ')}</div>
                    )}
                  </div>
                )}

              </div>
            ) : selectedImage && customPrompt.trim() ? (
              <div className="space-y-4">
                <div className="aspect-video bg-gray-100 rounded-lg flex items-center justify-center">
                  <div className="text-center text-gray-500">
                    <ImageIcon className="w-12 h-12 mx-auto mb-2" />
                    <p className="text-sm">Click "Transform" to see the result</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="aspect-video bg-gray-50 rounded-lg flex items-center justify-center">
                <div className="text-center text-gray-400">
                  <ArrowRight className="w-12 h-12 mx-auto mb-2" />
                  <p className="text-sm">
                    Upload an image, pick a room photo, and describe your changes
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>



      {/* Recent Transformations */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Recent Transformations</h2>
        {isLoading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          </div>
        ) : transformations.length === 0 ? (
          <Card>
            <CardContent className="py-12">
              <div className="text-center text-gray-500">
                <Palette className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                <p>No transformations yet</p>
                <p className="text-sm mt-1">Upload an image to get started</p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {transformations.slice(0, 6).map((transformation) => (
              <Card key={transformation.id} className="overflow-hidden hover:shadow-lg transition-shadow cursor-pointer">
                <div className="aspect-video bg-gray-200">
                  <img
                    src={transformation.transformed_image_url}
                    alt={`${transformation.style} transformation`}
                    className="w-full h-full object-cover"
                  />
                </div>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium capitalize">{transformation.style}</span>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      transformation.status === 'completed'
                        ? 'bg-green-100 text-green-700'
                        : transformation.status === 'processing'
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      {transformation.status}
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Lightbox */}
      {lightboxUrl && (
        <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center" onClick={() => setLightboxUrl(null)}>
          <button
            className="absolute top-4 right-4 text-white text-2xl"
            onClick={(e) => { e.stopPropagation(); setLightboxUrl(null); }}
            aria-label="Close"
          >
            ×
          </button>
          <img
            src={lightboxUrl}
            alt="Full screen preview"
            className="max-w-[90vw] max-h-[90vh] object-contain"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}

    </div>
  );
}

