'use client';

import { User, Bot } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Message } from '@/lib/types/chat';
import { useState } from 'react';
import { MessageFeedback, type FeedbackData } from './MessageFeedback';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';


interface MessageBubbleProps {
  message: Message;
  onQuestionClick?: (question: string) => void;
  onActionClick?: (action: any) => void;
}

export function MessageBubble({ message, onQuestionClick, onActionClick }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const [showAllProducts, setShowAllProducts] = useState(false);
  const [productModal, setProductModal] = useState<any | null>(null);

  const isAssistant = message.role === 'assistant';

  // Handle feedback submission
  const handleFeedbackSubmit = async (feedback: FeedbackData) => {
    try {
      const response = await fetch('/api/v1/chat/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(feedback),
      });

      if (!response.ok) {
        console.error('Failed to submit feedback:', await response.text());
      } else {
        const result = await response.json();
        console.log('Feedback submitted successfully:', result);
      }
    } catch (error) {
      console.error('Error submitting feedback:', error);
    }
  };

  // Helpers
  const fmtCAD = (n?: number) =>
    typeof n === 'number'
      ? new Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD' }).format(n)
      : undefined;

  return (
    <div className={cn('flex gap-3', isUser && 'flex-row-reverse')}>
      {/* Avatar */}
      <div
        className={cn(
          'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
          isUser ? 'bg-primary' : 'bg-green-500'
        )}
      >
        {isUser ? (
          <User className="w-5 h-5 text-white" />
        ) : (
          <Bot className="w-5 h-5 text-white" />
        )}
      </div>

      {/* Message Content */}
      <div className={cn('flex flex-col gap-2 max-w-[70%]', isUser && 'items-end')}>
        {/* Message Bubble */}
        <div
          className={cn(
            'px-4 py-3 rounded-2xl',
            isUser
              ? 'bg-primary text-white rounded-tr-sm'
              : 'bg-white border border-gray-200 rounded-tl-sm'
          )}
        >
          {isUser ? (
            <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>
          ) : (
            <div className="text-sm prose prose-sm max-w-none prose-headings:mt-3 prose-headings:mb-2 prose-p:my-2 prose-ul:my-2 prose-ol:my-2 prose-li:my-0.5">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Metadata - Images */}
        {message.metadata?.images && message.metadata.images.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {message.metadata.images.map((imageUrl, index) => (
              <div key={index} className="w-32 h-32 rounded-lg overflow-hidden border border-gray-200">
                <img
                  src={imageUrl}
                  alt={`Attachment ${index + 1}`}
                  className="w-full h-full object-cover"
                />
              </div>
            ))}
          </div>
        )}

        {/* Metadata - Attachments (PDFs / files) */}
        {message.metadata?.attachments && message.metadata.attachments.length > 0 && (
          <div className="flex flex-col gap-2 w-full">
            {message.metadata.attachments
              .filter((att) => att.type === 'pdf' || (att.content_type && att.content_type.includes('pdf')) || att.type === 'file')
              .map((att, idx) => (
                <a
                  key={idx}
                  href={att.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-sm text-blue-600 hover:underline bg-blue-50 border border-blue-200 rounded-md px-3 py-2 w-fit"
                >
                  <span>📄 {att.filename || 'Attachment'}</span>
                </a>
              ))}
          </div>
        )}

        {/* Metadata - Design Studio Navigation */}
        {message.metadata?.navigate_to && typeof message.metadata.navigate_to === 'string' && message.metadata.navigate_to.includes('/design') && (
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-3 text-sm w-full">
            <p className="font-medium text-purple-900">🎨 Design Studio</p>
            <a
              href={message.metadata.navigate_to}
              className="mt-2 inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
            >
              Open Design Studio
            </a>
          </div>
        )}

        {/* Metadata - Designs */}
        {message.metadata?.designs && message.metadata.designs.length > 0 && (
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-3 text-sm">
            <p className="font-medium text-purple-900">🎨 Design Suggestions</p>
            <p className="text-purple-700 mt-1">{message.metadata.designs.length} designs available</p>
          </div>
        )}

        {/* Metadata - Products (detailed cards with View All + modal) */}
        {message.metadata?.products && message.metadata.products.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm w-full">
            {(() => {
              const products: any[] = (message.metadata as any).products || [];
              const showing: any[] = showAllProducts ? products : products.slice(0, 3);
              return (
                <>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-blue-900">🛒 Product Recommendations</p>
                      <p className="text-blue-700">{products.length} products found</p>
                    </div>
                    {products.length > 3 && (
                      <button
                        className="text-xs px-2 py-1 border rounded bg-white hover:bg-gray-50"
                        onClick={() => setShowAllProducts((v) => !v)}
                      >
                        {showAllProducts ? 'Collapse' : `View all (${products.length})`}
                      </button>
                    )}
                  </div>

                  <div className="mt-2 grid grid-cols-1 gap-2">
                    {showing.map((p: any, idx: number) => {
                      const name = p?.product_name || p?.name || `Product ${idx + 1}`;
                      const fitScore = typeof p?.fit_score === 'number' ? p.fit_score : undefined;
                      const styleScore = typeof p?.style_score === 'number' ? p.style_score : undefined;
                      const overall = typeof p?.overall_score === 'number' ? p.overall_score : undefined;
                      const overallPct = typeof overall === 'number' ? Math.round((overall <= 1 ? overall * 100 : overall)) : undefined;
                      const isRec = !!p?.is_recommended;
                      const willFit = !!p?.will_fit;
                      const reason = p?.recommendation_reason || p?.brief_reason;
                      const href = p?.url as string | undefined;
                      let domain = '';
                      try { if (href) domain = new URL(href).hostname.replace(/^www\./,''); } catch {}
                      return (
                        <div key={idx} className="bg-white border rounded-md p-2 flex flex-col gap-1">
                          <div className="flex items-center justify-between">
                            <p className="text-gray-900 font-medium truncate" title={name}>{name}</p>
                            {typeof overallPct === 'number' && (
                              <span className="text-[11px] px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">Score {overallPct}%</span>
                            )}
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {isRec && <span className="text-[10px] px-2 py-0.5 rounded-full bg-green-100 text-green-700">Recommended</span>}
                            {willFit && <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">Will fit</span>}
                            {typeof fitScore === 'number' && (
                              <span className="text-[10px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">Fit {(fitScore <= 1 ? Math.round(fitScore * 100) : Math.round(fitScore))}%</span>
                            )}
                            {typeof styleScore === 'number' && (
                              <span className="text-[10px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">Style {(styleScore <= 1 ? Math.round(styleScore * 100) : Math.round(styleScore))}%</span>
                            )}
                          </div>
                          {reason && <p className="text-[12px] text-gray-600 mt-1 line-clamp-3">{reason}</p>}
                          <div className="flex items-center justify-between mt-1">
                            {href ? (
                              <a href={href} target="_blank" rel="noreferrer" className="text-[12px] text-blue-600 hover:underline">{domain || 'View product'}</a>
                            ) : (<span />)}
                            <button
                              className="text-[12px] px-2 py-0.5 border rounded bg-white hover:bg-gray-50"
                              onClick={() => setProductModal(p)}
                            >Details</button>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {productModal && (
                    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" onClick={() => setProductModal(null)}>
                      <div className="bg-white rounded-lg shadow-lg max-w-lg w-full p-4" onClick={(e) => e.stopPropagation()}>
                        {(() => {
                          const p: any = productModal;
                          const name = p?.product_name || p?.name || 'Product';
                          const href = p?.url as string | undefined;
                          let domain = '';
                          try { if (href) domain = new URL(href).hostname.replace(/^www\./,''); } catch {}
                          return (
                            <div>
                              <div className="flex items-start justify-between">
                                <div>
                                  <div className="text-base font-semibold text-gray-900">{name}</div>
                                  {href && (
                                    <a href={href} target="_blank" rel="noreferrer" className="text-xs text-blue-600 hover:underline">{domain || href}</a>
                                  )}
                                </div>
                                <button className="text-sm px-2 py-1 border rounded" onClick={() => setProductModal(null)}>Close</button>
                              </div>
                              {p?.image_url && (
                                <div className="mt-2 rounded overflow-hidden border">
                                  <img src={p.image_url} alt={name} className="w-full object-cover" />
                                </div>
                              )}
                              <div className="mt-3 grid grid-cols-2 gap-2 text-[12px] text-gray-700">
                                {typeof p?.overall_score === 'number' && (
                                  <div><span className="font-medium">Overall:</span> {Math.round((p.overall_score <= 1 ? p.overall_score * 100 : p.overall_score))}%</div>
                                )}
                                {typeof p?.fit_score === 'number' && (
                                  <div><span className="font-medium">Fit:</span> {Math.round((p.fit_score <= 1 ? p.fit_score * 100 : p.fit_score))}%</div>
                                )}
                                {typeof p?.style_score === 'number' && (
                                  <div><span className="font-medium">Style:</span> {Math.round((p.style_score <= 1 ? p.style_score * 100 : p.style_score))}%</div>
                                )}
                                {p?.price_estimate && (
                                  <div><span className="font-medium">Price:</span> {String(p.price_estimate)}</div>
                                )}
                              </div>
                              {p?.recommendation_reason && (
                                <div className="mt-2 text-[12px] text-gray-700"><span className="font-medium">Why:</span> {p.recommendation_reason}</div>
                              )}
                              {p?.dimensions && (
                                <div className="mt-2 text-[12px] text-gray-700"><span className="font-medium">Dimensions:</span> {String(p.dimensions)}</div>
                              )}
                            </div>
                          );
                        })()}
                      </div>
                    </div>
                  )}
                </>
              );
            })()}
          </div>
        )}

        {/* Metadata - Cost Estimates (card) */}
        {message.metadata?.cost_estimates && message.metadata.cost_estimates.length > 0 && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-sm w-full">
            <p className="font-medium text-green-900">💰 Cost Estimate</p>
            {(message.metadata.cost_estimates || []).slice(0, 1).map((ce: any, idx: number) => {
              const room = ce?.room_name || ce?.room_id;
              const scope = ce?.renovation_scope;
              const ceData = ce?.cost_estimate || ce?.estimate || {};
              const range = ceData?.total_range || ceData?.total || {};
              const low = typeof range?.low === 'number' ? range.low : undefined;
              const high = typeof range?.high === 'number' ? range.high : undefined;
              const totalLabel = typeof low === 'number' && typeof high === 'number' ? `${fmtCAD(low)} - ${fmtCAD(high)}` : undefined;
              const breakdown = Array.isArray(ceData?.breakdown) ? ceData.breakdown : (Array.isArray(ceData?.items) ? ceData.items : []);
              return (
                <div key={idx} className="mt-2 bg-white border rounded-md p-2">
                  <div className="flex flex-wrap items-center gap-2 justify-between">
                    <div className="text-gray-900 font-medium">
                      {room && <span className="mr-2">Room: {room}</span>}
                      {scope && <span className="text-gray-600">Scope: {scope}</span>}
                    </div>
                    {totalLabel && (
                      <span className="text-[12px] px-2 py-0.5 rounded-full bg-green-100 text-green-800">Total {totalLabel}</span>
                    )}
                  </div>
                  {breakdown && breakdown.length > 0 && (
                    <div className="mt-2">
                      <div className="grid grid-cols-1 gap-1">
                        {breakdown.slice(0, 4).map((item: any, i: number) => {
                          const label = item?.label || item?.name || `Item ${i + 1}`;
                          const cost = typeof item?.cost === 'number' ? item.cost : (typeof item?.amount === 'number' ? item.amount : undefined);
                          return (
                            <div key={i} className="flex items-center justify-between text-[13px] py-0.5">
                              <span className="text-gray-700">• {label}</span>
                              {typeof cost === 'number' && <span className="text-gray-900 font-medium">{fmtCAD(cost)}</span>}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
        {/* Metadata - DIY Plan (card) */}
        {/* Metadata - Shopping List (card) */}
        {(message.metadata as any)?.shopping_list && (
          <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3 text-sm w-full">
            <p className="font-medium text-emerald-900">🧰 Shopping List</p>
            {(() => {
              const sl: any = (message.metadata as any).shopping_list || {};
              const materials: any[] = Array.isArray(sl.materials) ? sl.materials : [];
              const tools: any[] = Array.isArray(sl.tools) ? sl.tools : [];
              const itemLabel = (it: any) => (typeof it === 'string' ? it : (it?.name || 'Item'));
              const qty = (it: any) => (typeof it?.quantity === 'number' ? it.quantity : undefined);
              const opt = (it: any) => (it?.optional === true);
              const note = (it: any) => (it?.notes ? String(it.notes) : undefined);
              return (
                <div className="mt-2 bg-white border rounded-md p-2">
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <p className="text-xs font-medium text-gray-700 mb-1">Materials</p>
                      <div className="space-y-1">
                        {materials.slice(0, 10).map((m: any, i: number) => (
                          <div key={i} className="flex items-start gap-2 text-[13px] text-gray-800">
                            <input type="checkbox" className="mt-0.5" disabled />
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <span>• {itemLabel(m)}</span>
                                {typeof qty(m) === 'number' && (
                                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-700">x{qty(m)}</span>
                                )}
                              </div>
                              {note(m) && <div className="text-[11px] text-gray-500">{note(m)}</div>}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-gray-700 mb-1">Tools</p>
                      <div className="space-y-1">
                        {tools.slice(0, 10).map((t: any, i: number) => (
                          <div key={i} className="flex items-start gap-2 text-[13px] text-gray-800">
                            <input type="checkbox" className="mt-0.5" disabled />
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <span>• {itemLabel(t)}</span>
                                {opt(t) && (
                                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700">Optional</span>
                                )}
                              </div>
                              {note(t) && <div className="text-[11px] text-gray-500">{note(t)}</div>}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })()}
          </div>
        )}

        {message.metadata?.diy_plan && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm w-full">
            <p className="font-medium text-amber-900">🔨 DIY Project Plan</p>
            {(() => {
              const plan: any = message.metadata?.diy_plan || {};
              const title = plan?.title || plan?.scope || 'DIY Plan';
              const scope = plan?.scope || plan?.project_scope;
              const diff = plan?.difficulty || plan?.difficulty_level;
              const days = plan?.duration_days;
              const steps: any[] = Array.isArray(plan?.steps) ? plan.steps : [];
              const tools: any[] = Array.isArray(plan?.tools) ? plan.tools : [];
              const materials: any[] = Array.isArray(plan?.materials) ? plan.materials : [];
              const safety: any[] = Array.isArray(plan?.safety_tips) ? plan.safety_tips : [];

              return (
                <div className="mt-2 bg-white border rounded-md p-2">
                  <div className="flex flex-wrap items-center gap-2 justify-between mb-2">
                    <div className="text-gray-900 font-medium">
                      <span className="mr-2">{title}</span>
                      {scope && <span className="text-gray-600">• {scope}</span>}
                    </div>
                    <div className="flex gap-1">
                      {typeof days === 'number' && (
                        <span className="text-[11px] px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">~{days} day(s)</span>
                      )}
                      {diff && (
                        <span className="text-[11px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">{String(diff).toUpperCase()}</span>
                      )}
                    </div>
                  </div>

                  {/* Steps */}
                  {steps.length > 0 && (
                    <div className="mb-2">
                      <p className="text-xs font-medium text-gray-700 mb-1">Steps:</p>
                      <div className="space-y-1">
                        {steps.slice(0, 6).map((s: any, i: number) => (
                          <div key={i} className="text-[13px] text-gray-700">
                            <span className="font-medium">{s?.step || i + 1}.</span> {s?.title || s?.details || 'Step'}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Tools & Materials */}
                  <div className="grid grid-cols-2 gap-2 mb-2">
                    {tools.length > 0 && (
                      <div>
                        <p className="text-xs font-medium text-gray-700 mb-1">Tools:</p>
                        <div className="text-[12px] text-gray-600">
                          {tools.slice(0, 4).map((t: any, i: number) => (
                            <div key={i}>• {typeof t === 'string' ? t : (t?.name || 'Tool')}</div>
                          ))}
                        </div>
                      </div>
                    )}
                    {materials.length > 0 && (
                      <div>
                        <p className="text-xs font-medium text-gray-700 mb-1">Materials:</p>
                        <div className="text-[12px] text-gray-600">
                          {materials.slice(0, 4).map((m: any, i: number) => (
                            <div key={i}>• {typeof m === 'string' ? m : (m?.name || 'Material')}</div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Safety Tips */}
                  {safety.length > 0 && (
                    <div className="bg-red-50 border border-red-200 rounded p-2">
                      <p className="text-xs font-medium text-red-900 mb-1">⚠️ Safety:</p>
                      <div className="text-[12px] text-red-800">
                        {safety.slice(0, 3).map((tip: any, i: number) => (
                          <div key={i}>• {typeof tip === 'string' ? tip : String(tip)}</div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })()}
          </div>
        )}


        {/* Web Search Results (Google Grounding) */}
        {isAssistant && message.metadata?.web_search_results && message.metadata.web_search_results.length > 0 && (
          <div className="mt-3 space-y-2">
            <h4 className="text-xs font-semibold text-gray-700 flex items-center gap-1">
              <span>🔍</span> Product Recommendations
            </h4>
            <div className="space-y-2">
              {message.metadata.web_search_results.slice(0, 5).map((product: any, idx: number) => (
                <a
                  key={idx}
                  href={product.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block p-2 rounded-lg border border-gray-200 hover:border-primary hover:bg-primary/5 transition-colors"
                >
                  <div className="flex items-start gap-2">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{product.name || product.title}</p>
                      {product.price && (
                        <p className="text-xs text-green-600 font-semibold mt-0.5">{product.price}</p>
                      )}
                      {product.description && (
                        <p className="text-xs text-gray-600 mt-1 line-clamp-2">{product.description}</p>
                      )}
                      {product.vendor && (
                        <p className="text-xs text-gray-500 mt-1">
                          {product.vendor}
                          {product.url?.includes('.ca') && <span className="ml-1 text-blue-600">🇨🇦</span>}
                        </p>
                      )}
                    </div>
                    <svg className="w-4 h-4 text-gray-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </div>
                </a>
              ))}
            </div>
            {message.metadata.web_sources && message.metadata.web_sources.length > 0 && (
              <p className="text-xs text-gray-500 mt-2">
                Sources: {message.metadata.web_sources.length} web pages
              </p>
            )}
          </div>
        )}

        {/* YouTube Tutorial Videos */}
        {isAssistant && message.metadata?.youtube_videos && message.metadata.youtube_videos.length > 0 && (
          <div className="mt-3 space-y-2">
            <h4 className="text-xs font-semibold text-gray-700 flex items-center gap-1">
              <span>📺</span> Tutorial Videos
            </h4>
            <div className="space-y-2">
              {message.metadata.youtube_videos.map((video: any, idx: number) => (
                <a
                  key={idx}
                  href={video.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block rounded-lg border border-gray-200 hover:border-red-500 hover:shadow-md transition-all overflow-hidden"
                >
                  <div className="flex gap-3 p-2">
                    {/* Thumbnail */}
                    <div className="relative w-32 h-20 flex-shrink-0 bg-gray-100 rounded overflow-hidden">
                      {video.thumbnail ? (
                        <img
                          src={video.thumbnail}
                          alt={video.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-gray-400">
                          <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" />
                          </svg>
                        </div>
                      )}
                      {video.duration && (
                        <div className="absolute bottom-1 right-1 bg-black/80 text-white text-xs px-1 rounded">
                          {video.duration}
                        </div>
                      )}
                    </div>

                    {/* Video Info */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 line-clamp-2">{video.title}</p>
                      <p className="text-xs text-gray-600 mt-1">{video.channel}</p>
                      {video.is_trusted_channel && (
                        <span className="inline-block mt-1 text-xs text-blue-600 font-medium">✓ Trusted</span>
                      )}
                      {video.views && (
                        <p className="text-xs text-gray-500 mt-1">
                          {video.views.toLocaleString()} views
                        </p>
                      )}
                    </div>
                  </div>
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Contractors (Google Maps) */}
        {isAssistant && message.metadata?.contractors && message.metadata.contractors.length > 0 && (
          <div className="mt-3 space-y-2">
            <h4 className="text-xs font-semibold text-gray-700 flex items-center gap-1">
              <span>🔨</span> Recommended Contractors (Vancouver Area)
            </h4>
            <div className="space-y-2">
              {message.metadata.contractors.map((contractor: any, idx: number) => (
                <a
                  key={idx}
                  href={contractor.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block p-3 rounded-lg border border-gray-200 hover:border-blue-500 hover:bg-blue-50 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    {/* Icon */}
                    <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-lg">🏗️</span>
                    </div>

                    {/* Contractor Info */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-900">{contractor.name}</p>
                      <p className="text-xs text-gray-600 mt-0.5">{contractor.type}</p>
                      {contractor.location && (
                        <p className="text-xs text-gray-500 mt-0.5 flex items-center gap-1">
                          <span>📍</span> {contractor.location}
                        </p>
                      )}
                      {contractor.rating && (
                        <p className="text-xs text-yellow-600 mt-1 flex items-center gap-1">
                          <span>⭐</span> {contractor.rating} {contractor.reviews && `(${contractor.reviews} reviews)`}
                        </p>
                      )}
                      {contractor.phone && (
                        <p className="text-xs text-blue-600 mt-1">
                          📞 {contractor.phone}
                        </p>
                      )}
                    </div>

                    {/* External link icon */}
                    <div className="flex-shrink-0">
                      <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </div>
                  </div>
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Generated Images */}
        {isAssistant && message.metadata?.generated_images && message.metadata.generated_images.length > 0 && (
          <div className="mt-3 space-y-2">
            <h4 className="text-xs font-semibold text-gray-700 flex items-center gap-1">
              <span>🎨</span> Visual Aids
            </h4>
            <div className="grid grid-cols-2 gap-2">
              {message.metadata.generated_images.map((img: string, idx: number) => (
                <div key={idx} className="relative rounded-lg overflow-hidden border border-gray-200 hover:border-primary transition-colors">
                  <img
                    src={img.startsWith('data:') ? img : `data:image/png;base64,${img}`}
                    alt={`Generated visual ${idx + 1}`}
                    className="w-full h-auto"
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Suggested Actions */}
        {isAssistant && message.metadata?.suggested_actions && message.metadata.suggested_actions.length > 0 && (
          <div className="flex flex-col gap-2 w-full mt-1">
            <p className="text-xs text-gray-500 px-2">Suggested actions:</p>
            <div className="flex flex-wrap gap-2">
              {message.metadata.suggested_actions.map((action: any, idx: number) => (
                <button
                  key={idx}
                  onClick={() => onActionClick?.(action)}
                  className="px-3 py-1.5 rounded-full text-xs border border-gray-300 text-gray-700 hover:border-primary hover:text-primary hover:bg-primary/5 transition-colors text-left"
                  title={action.description || action.label}
                >
                  {action.label || action.action}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Suggested Follow-up Questions */}
        {isAssistant && message.metadata?.suggested_questions && message.metadata.suggested_questions.length > 0 && (
          <div className="flex flex-wrap gap-2 w-full mt-2">
            {message.metadata.suggested_questions.map((question, idx) => (
              <button
                key={idx}
                onClick={() => onQuestionClick?.(question)}
                className="px-3 py-1.5 rounded-full text-xs border border-gray-300 text-gray-700 hover:border-primary hover:text-primary hover:bg-primary/5 transition-colors text-left"
              >
                {question}
              </button>
            ))}
          </div>
        )}

        {/* Feedback (only for assistant messages) */}
        {isAssistant && message.id && (
          <div className="px-2">
            <MessageFeedback
              messageId={message.id}
              onFeedbackSubmit={handleFeedbackSubmit}
            />
          </div>
        )}

        {/* Timestamp */}
        <p className="text-xs text-gray-500 px-2">
          {new Date(message.created_at).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
      </div>
    </div>
  );
}

