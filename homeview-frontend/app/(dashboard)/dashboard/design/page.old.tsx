'use client';

import { Suspense, useState, useEffect, useRef } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Sparkles, Image as ImageIcon, DollarSign, Calendar, Lightbulb, Upload, Loader2, Save } from 'lucide-react';
import { designAPI } from '@/lib/api/design';
import { projectsAPI } from '@/lib/api/projects';

// Import new components
import DesignWorkflowWizard from '@/components/studio/DesignWorkflowWizard';
import StyleLibrary from '@/components/studio/StyleLibrary';
import BudgetEstimator from '@/components/studio/BudgetEstimator';
import BeforeAfterSlider from '@/components/studio/BeforeAfterSlider';
import AIDesignAssistant from '@/components/studio/AIDesignAssistant';
import ProjectTimeline from '@/components/studio/ProjectTimeline';

// Local storage key for persistence
const STORAGE_KEY = 'homeview_design_studio_state';

interface DesignState {
  activeTab: string;
  currentWorkflowStep: string;
  selectedImage: string | null;
  resultImages: string[];
  summary: any | null;
  budget: number;
  completedSteps: string[];
}

function DesignStudioEnhancedContent() {
  const [activeTab, setActiveTab] = useState('design');
  const [currentWorkflowStep, setCurrentWorkflowStep] = useState('room-selection');
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [resultImages, setResultImages] = useState<string[]>([]);
  const [showAIAssistant, setShowAIAssistant] = useState(true);
  const [isTransforming, setIsTransforming] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [summary, setSummary] = useState<any | null>(null);
  const [budget, setBudget] = useState<number>(0);
  const [completedSteps, setCompletedSteps] = useState<string[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load saved state from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const state: DesignState = JSON.parse(saved);
        setActiveTab(state.activeTab || 'design');
        setCurrentWorkflowStep(state.currentWorkflowStep || 'room-selection');
        setSelectedImage(state.selectedImage);
        setResultImages(state.resultImages || []);
        setSummary(state.summary);
        setBudget(state.budget || 0);
        setCompletedSteps(state.completedSteps || []);
      }
    } catch (error) {
      console.error('Failed to load saved state:', error);
    }
  }, []);

  // Save state to localStorage whenever it changes
  useEffect(() => {
    try {
      const state: DesignState = {
        activeTab,
        currentWorkflowStep,
        selectedImage,
        resultImages,
        summary,
        budget,
        completedSteps,
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (error) {
      console.error('Failed to save state:', error);
    }
  }, [activeTab, currentWorkflowStep, selectedImage, resultImages, summary, budget, completedSteps]);

  // Helper function to compress images for faster upload
  const compressImage = (file: File, maxWidth: number, quality: number): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
          const canvas = document.createElement('canvas');
          let width = img.width;
          let height = img.height;

          if (width > maxWidth) {
            height = (height * maxWidth) / width;
            width = maxWidth;
          }

          canvas.width = width;
          canvas.height = height;
          const ctx = canvas.getContext('2d');
          if (!ctx) {
            reject(new Error('Failed to get canvas context'));
            return;
          }

          ctx.drawImage(img, 0, 0, width, height);
          resolve(canvas.toDataURL('image/jpeg', quality));
        };
        img.onerror = reject;
        img.src = e.target?.result as string;
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  // Handle image upload
  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      // Compress image before upload for faster processing
      const compressedDataUrl = await compressImage(file, 1920, 0.85);
      setSelectedImage(compressedDataUrl);
      setCurrentWorkflowStep('measurements');
      markStepCompleted('room-selection');
    } catch (error) {
      console.error('Failed to upload image:', error);
      alert('Failed to upload image. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  // Handle style selection and transformation
  const handleStyleSelect = async (style: any) => {
    if (!selectedImage) {
      alert('Please upload an image first');
      return;
    }

    setIsTransforming(true);
    setCurrentWorkflowStep('design-generation');
    markStepCompleted('style-exploration');

    try {
      // Call the API to transform the image (optimized for speed)
      const response = await designAPI.transformPromptedUpload(
        selectedImage,
        style.prompt,
        { numVariations: 2, enableGrounding: false }  // Reduced to 2 for faster results
      );

      if (response.result_urls && response.result_urls.length > 0) {
        setResultImages(response.result_urls);
        setSummary(response.summary || null);
        setActiveTab('compare');
        markStepCompleted('design-generation');
      }
    } catch (error) {
      console.error('Failed to transform image:', error);
      alert('Failed to generate design. Please try again.');
    } finally {
      setIsTransforming(false);
    }
  };

  const handleWorkflowStepSelect = (stepId: string) => {
    setCurrentWorkflowStep(stepId);

    // Navigate to appropriate tab based on step
    if (stepId === 'style-exploration') {
      setActiveTab('design');
    } else if (stepId === 'budget-planning') {
      setActiveTab('budget');
    } else if (stepId === 'timeline') {
      setActiveTab('timeline');
    } else if (stepId === 'ai-assistant') {
      setShowAIAssistant(true);
    } else if (stepId === 'skip-to-design') {
      setActiveTab('design');
      setCurrentWorkflowStep('style-exploration');
    }
  };

  const markStepCompleted = (stepId: string) => {
    if (!completedSteps.includes(stepId)) {
      setCompletedSteps([...completedSteps, stepId]);
    }
  };

  const handleBudgetUpdate = (total: number) => {
    setBudget(total);
    markStepCompleted('budget-planning');
  };

  const handleSaveProject = async () => {
    if (!selectedImage || resultImages.length === 0) {
      alert('Please generate a design first');
      return;
    }

    setIsSaving(true);
    try {
      const projectData = {
        name: `${summary?.room_type || 'Room'} Design - ${new Date().toLocaleDateString()}`,
        description: `${summary?.current_style || 'Custom'} style transformation`,
        room_type: summary?.room_type,
        style: summary?.current_style,
        original_image_url: selectedImage,
        result_images: resultImages,
        summary: summary,
        budget: budget,
        timeline_data: null,
      };

      if (currentProjectId) {
        await projectsAPI.updateProject(currentProjectId, projectData);
        alert('Project updated successfully!');
      } else {
        const response = await projectsAPI.saveProject(projectData);
        setCurrentProjectId(response.project_id);
        alert('Project saved successfully!');
      }
    } catch (error) {
      console.error('Failed to save project:', error);
      alert('Failed to save project. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Design Studio</h1>
              <p className="text-gray-600 mt-1">Your complete home improvement journey</p>
            </div>
            <div className="flex gap-2">
              {resultImages.length > 0 && (
                <Button
                  variant="outline"
                  onClick={handleSaveProject}
                  disabled={isSaving}
                >
                  <Save className="w-4 h-4 mr-2" />
                  {isSaving ? 'Saving...' : currentProjectId ? 'Update' : 'Save'}
                </Button>
              )}
              <Button
                variant="outline"
                onClick={() => setShowAIAssistant(!showAIAssistant)}
              >
                <Lightbulb className="w-4 h-4 mr-2" />
                {showAIAssistant ? 'Hide' : 'Show'} AI Assistant
              </Button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Sidebar - Workflow Wizard */}
          <div className="lg:col-span-3">
            <DesignWorkflowWizard 
              onStepSelect={handleWorkflowStepSelect}
              currentStep={currentWorkflowStep}
            />
          </div>

          {/* Main Content Area */}
          <div className="lg:col-span-6">
            <Card className="shadow-lg">
              <CardContent className="p-6">
                <Tabs value={activeTab} onValueChange={setActiveTab}>
                  <TabsList className="grid w-full grid-cols-4 mb-6">
                    <TabsTrigger value="design" className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4" />
                      <span className="hidden sm:inline">Design</span>
                    </TabsTrigger>
                    <TabsTrigger value="compare" className="flex items-center gap-2">
                      <ImageIcon className="w-4 h-4" />
                      <span className="hidden sm:inline">Compare</span>
                    </TabsTrigger>
                    <TabsTrigger value="budget" className="flex items-center gap-2">
                      <DollarSign className="w-4 h-4" />
                      <span className="hidden sm:inline">Budget</span>
                    </TabsTrigger>
                    <TabsTrigger value="timeline" className="flex items-center gap-2">
                      <Calendar className="w-4 h-4" />
                      <span className="hidden sm:inline">Timeline</span>
                    </TabsTrigger>
                  </TabsList>

                  {/* Design Tab */}
                  <TabsContent value="design" className="space-y-6">
                    <div>
                      <h2 className="text-xl font-bold text-gray-800 mb-4">Choose Your Style</h2>
                      <StyleLibrary onStyleSelect={handleStyleSelect} />
                    </div>

                    {/* Upload Section */}
                    <div className="mt-8">
                      <h3 className="text-lg font-bold text-gray-800 mb-4">Or Upload Your Room</h3>
                      <div
                        className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-purple-500 transition-colors cursor-pointer"
                        onClick={() => fileInputRef.current?.click()}
                      >
                        {isUploading ? (
                          <>
                            <Loader2 className="w-12 h-12 mx-auto text-purple-500 mb-4 animate-spin" />
                            <p className="text-gray-600 mb-2">Uploading...</p>
                          </>
                        ) : selectedImage ? (
                          <>
                            <div className="relative w-full max-w-md mx-auto mb-4">
                              <img
                                src={selectedImage}
                                alt="Uploaded room"
                                className="w-full h-auto rounded-lg"
                              />
                            </div>
                            <p className="text-green-600 font-medium mb-2">✓ Image uploaded successfully</p>
                            <Button
                              variant="outline"
                              onClick={(e) => {
                                e.stopPropagation();
                                fileInputRef.current?.click();
                              }}
                            >
                              Change Image
                            </Button>
                          </>
                        ) : (
                          <>
                            <ImageIcon className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                            <p className="text-gray-600 mb-2">Drag & drop your room image here</p>
                            <p className="text-sm text-gray-500">or click to browse</p>
                            <Button className="mt-4 bg-gradient-to-r from-purple-500 to-pink-500">
                              <Upload className="w-4 h-4 mr-2" />
                              Upload Image
                            </Button>
                          </>
                        )}
                      </div>
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={handleImageUpload}
                      />
                    </div>

                    {/* Transformation Status */}
                    {isTransforming && (
                      <div className="mt-6 p-4 bg-purple-50 border border-purple-200 rounded-lg">
                        <div className="flex items-center gap-3">
                          <Loader2 className="w-5 h-5 text-purple-600 animate-spin" />
                          <div>
                            <p className="font-medium text-purple-900">Generating your design...</p>
                            <p className="text-sm text-purple-700">This may take 30-60 seconds</p>
                          </div>
                        </div>
                      </div>
                    )}
                  </TabsContent>

                  {/* Compare Tab */}
                  <TabsContent value="compare">
                    {selectedImage && resultImages.length > 0 ? (
                      <BeforeAfterSlider
                        beforeImage={selectedImage}
                        afterImage={resultImages[0]}
                        beforeLabel="Original"
                        afterLabel="Transformed"
                      />
                    ) : (
                      <div className="text-center py-12">
                        <ImageIcon className="w-16 h-16 mx-auto text-gray-300 mb-4" />
                        <p className="text-gray-600 mb-2">No designs to compare yet</p>
                        <p className="text-sm text-gray-500">Upload an image and select a style to get started</p>
                        <Button
                          className="mt-4 bg-gradient-to-r from-purple-500 to-pink-500"
                          onClick={() => setActiveTab('design')}
                        >
                          Start Designing
                        </Button>
                      </div>
                    )}
                  </TabsContent>

                  {/* Budget Tab */}
                  <TabsContent value="budget">
                    {summary?.spatial_analysis ? (
                      <BudgetEstimator
                        spatialAnalysis={summary.spatial_analysis}
                        onBudgetUpdate={handleBudgetUpdate}
                      />
                    ) : (
                      <div className="text-center py-12">
                        <DollarSign className="w-16 h-16 mx-auto text-gray-300 mb-4" />
                        <p className="text-gray-600 mb-2">No budget data available yet</p>
                        <p className="text-sm text-gray-500">Generate a design first to see cost estimates</p>
                        <Button
                          className="mt-4 bg-gradient-to-r from-purple-500 to-pink-500"
                          onClick={() => setActiveTab('design')}
                        >
                          Generate Design
                        </Button>
                      </div>
                    )}
                  </TabsContent>

                  {/* Timeline Tab */}
                  <TabsContent value="timeline">
                    <ProjectTimeline 
                      projectType="Living Room Renovation"
                      onTaskSelect={(taskId) => console.log('Task selected:', taskId)}
                    />
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>

            {/* Quick Stats */}
            <div className="grid grid-cols-3 gap-4 mt-6">
              <Card className="bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-200">
                <CardContent className="p-4 text-center">
                  <div className="text-2xl font-bold text-blue-700">{completedSteps.length}/7</div>
                  <div className="text-xs text-gray-600 mt-1">Steps Completed</div>
                </CardContent>
              </Card>
              <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
                <CardContent className="p-4 text-center">
                  <div className="text-2xl font-bold text-green-700">
                    {budget > 0 ? `$${budget.toLocaleString()}` : '--'}
                  </div>
                  <div className="text-xs text-gray-600 mt-1">Estimated Budget</div>
                </CardContent>
              </Card>
              <Card className="bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200">
                <CardContent className="p-4 text-center">
                  <div className="text-2xl font-bold text-purple-700">
                    {resultImages.length > 0 ? `${resultImages.length}` : '--'}
                  </div>
                  <div className="text-xs text-gray-600 mt-1">Design Variations</div>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Right Sidebar - AI Assistant */}
          {showAIAssistant && (
            <div className="lg:col-span-3">
              <AIDesignAssistant
                context={{
                  roomType: summary?.room_type || 'Room',
                  currentStyle: summary?.current_style || undefined,
                  budget: budget || 0,
                  spatialData: summary?.spatial_analysis,
                }}
                onSuggestionApply={(suggestionId) => console.log('Suggestion applied:', suggestionId)}
              />

              {/* Additional Info Cards */}
              <Card className="mt-4 bg-gradient-to-br from-amber-50 to-orange-50 border-amber-200">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-2xl">💡</span>
                    <h4 className="font-bold text-gray-800">Pro Tip</h4>
                  </div>
                  <p className="text-sm text-gray-700">
                    {selectedImage
                      ? 'Start with a style template to save time, then customize colors and materials to match your vision.'
                      : 'Upload a room image to get started with AI-powered design suggestions.'}
                  </p>
                </CardContent>
              </Card>

              <Card className="mt-4 bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-2xl">🎯</span>
                    <h4 className="font-bold text-gray-800">Your Progress</h4>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Completion</span>
                      <span className="font-bold text-green-700">
                        {Math.round((completedSteps.length / 7) * 100)}%
                      </span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-green-500 to-emerald-500 transition-all duration-500"
                        style={{ width: `${(completedSteps.length / 7) * 100}%` }}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>

        {/* Bottom CTA */}
        <Card className="mt-6 bg-gradient-to-r from-purple-500 to-pink-500 text-white">
          <CardContent className="p-6 text-center">
            <h3 className="text-xl font-bold mb-2">Ready to Transform Your Space?</h3>
            <p className="text-white/90 mb-4">
              Get started with our guided workflow and bring your vision to life
            </p>
            <div className="flex gap-3 justify-center">
              <Button variant="outline" className="bg-white text-purple-600 hover:bg-gray-100">
                Watch Tutorial
              </Button>
              <Button variant="outline" className="bg-white/20 text-white hover:bg-white/30 border-white">
                View Examples
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function DesignStudioEnhancedPage() {
  return (
    <Suspense fallback={<div className="p-6">Loading Design Studio...</div>}>
      <DesignStudioEnhancedContent />
    </Suspense>
  );
}

