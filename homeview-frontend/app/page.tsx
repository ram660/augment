import Link from 'next/link';
import { Home, Hammer, HardHat, ArrowRight, Sparkles, Image, DollarSign, ShoppingCart } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Home className="w-8 h-8 text-primary" />
            <span className="text-2xl font-bold text-gray-900">HomeView AI</span>
          </div>
          <nav className="hidden md:flex gap-6">
            <a href="#features" className="text-gray-600 hover:text-primary">Features</a>
            <a href="#how-it-works" className="text-gray-600 hover:text-primary">How It Works</a>
            <a href="#pricing" className="text-gray-600 hover:text-primary">Pricing</a>
          </nav>
          <div className="flex gap-3">
            <Link href="/login" className="px-4 py-2 text-primary hover:bg-blue-50 rounded-lg transition">
              Login
            </Link>
            <Link href="/register" className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-700 transition">
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <div className="max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-100 text-primary rounded-full mb-6">
            <Sparkles className="w-4 h-4" />
            <span className="text-sm font-medium">AI-Powered Home Improvement</span>
          </div>
          
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
            Transform Your Home with
            <span className="text-primary"> AI Intelligence</span>
          </h1>
          
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Upload your floor plan and room photos. Get instant design transformations, 
            cost estimates, and personalized project plans—all powered by advanced AI.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Link 
              href="/register?type=homeowner" 
              className="px-8 py-4 bg-primary text-white rounded-lg hover:bg-primary-700 transition flex items-center justify-center gap-2 text-lg font-medium"
            >
              Start Your Project
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link 
              href="/demo" 
              className="px-8 py-4 border-2 border-primary text-primary rounded-lg hover:bg-blue-50 transition flex items-center justify-center gap-2 text-lg font-medium"
            >
              Watch Demo
            </Link>
          </div>

          {/* User Type Cards */}
          <div className="grid md:grid-cols-3 gap-6 mt-16">
            <Link href="/register?type=homeowner" className="p-6 bg-white rounded-xl shadow-lg hover:shadow-xl transition border-2 border-transparent hover:border-homeowner">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4 mx-auto">
                <Home className="w-6 h-6 text-homeowner" />
              </div>
              <h3 className="text-xl font-bold mb-2">Homeowners</h3>
              <p className="text-gray-600">Visualize designs, get cost estimates, and find contractors</p>
            </Link>

            <Link href="/register?type=diy" className="p-6 bg-white rounded-xl shadow-lg hover:shadow-xl transition border-2 border-transparent hover:border-diy">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mb-4 mx-auto">
                <Hammer className="w-6 h-6 text-diy" />
              </div>
              <h3 className="text-xl font-bold mb-2">DIY Workers</h3>
              <p className="text-gray-600">Get step-by-step guides, material lists, and tutorials</p>
            </Link>

            <Link href="/register?type=contractor" className="p-6 bg-white rounded-xl shadow-lg hover:shadow-xl transition border-2 border-transparent hover:border-contractor">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4 mx-auto">
                <HardHat className="w-6 h-6 text-contractor" />
              </div>
              <h3 className="text-xl font-bold mb-2">Contractors</h3>
              <p className="text-gray-600">Find projects, generate quotes, and manage clients</p>
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="bg-white py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Powerful AI Features</h2>
            <p className="text-xl text-gray-600">Everything you need to plan and execute your home improvement projects</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="p-6 rounded-xl border-2 border-gray-100 hover:border-primary transition">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <Image className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-bold mb-2">AI Design Studio</h3>
              <p className="text-gray-600">Transform room photos into 40+ design styles instantly with Gemini Imagen</p>
            </div>

            <div className="p-6 rounded-xl border-2 border-gray-100 hover:border-secondary transition">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                <DollarSign className="w-6 h-6 text-secondary" />
              </div>
              <h3 className="text-xl font-bold mb-2">Cost Estimation</h3>
              <p className="text-gray-600">Get accurate cost estimates with regional pricing and material databases</p>
            </div>

            <div className="p-6 rounded-xl border-2 border-gray-100 hover:border-accent transition">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mb-4">
                <ShoppingCart className="w-6 h-6 text-accent" />
              </div>
              <h3 className="text-xl font-bold mb-2">Product Matching</h3>
              <p className="text-gray-600">Find products that fit your space with dimension-aware AI matching</p>
            </div>

            <div className="p-6 rounded-xl border-2 border-gray-100 hover:border-primary transition">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                <Sparkles className="w-6 h-6 text-homeowner" />
              </div>
              <h3 className="text-xl font-bold mb-2">Smart Chat</h3>
              <p className="text-gray-600">Ask questions about your home and get AI-powered answers with full context</p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">How It Works</h2>
            <p className="text-xl text-gray-600">Get started in 3 simple steps</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            <div className="text-center">
              <div className="w-16 h-16 bg-primary text-white rounded-full flex items-center justify-center text-2xl font-bold mb-4 mx-auto">
                1
              </div>
              <h3 className="text-xl font-bold mb-2">Upload Your Home</h3>
              <p className="text-gray-600">Upload floor plans and room photos to create your digital twin</p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-primary text-white rounded-full flex items-center justify-center text-2xl font-bold mb-4 mx-auto">
                2
              </div>
              <h3 className="text-xl font-bold mb-2">Explore with AI</h3>
              <p className="text-gray-600">Chat with AI, transform designs, and get cost estimates</p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-primary text-white rounded-full flex items-center justify-center text-2xl font-bold mb-4 mx-auto">
                3
              </div>
              <h3 className="text-xl font-bold mb-2">Execute Your Plan</h3>
              <p className="text-gray-600">Choose DIY with step-by-step guides or hire contractors</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-primary py-20">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-4xl font-bold text-white mb-4">Ready to Transform Your Home?</h2>
          <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
            Join thousands of homeowners, DIY workers, and contractors using AI to make better home improvement decisions
          </p>
          <Link 
            href="/register" 
            className="inline-flex items-center gap-2 px-8 py-4 bg-white text-primary rounded-lg hover:bg-gray-100 transition text-lg font-medium"
          >
            Get Started Free
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Home className="w-6 h-6 text-primary" />
                <span className="text-xl font-bold text-white">HomeView AI</span>
              </div>
              <p className="text-sm">AI-powered home improvement platform for everyone</p>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4">Product</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-white">Features</a></li>
                <li><a href="#" className="hover:text-white">Pricing</a></li>
                <li><a href="#" className="hover:text-white">Demo</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4">Company</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-white">About</a></li>
                <li><a href="#" className="hover:text-white">Blog</a></li>
                <li><a href="#" className="hover:text-white">Careers</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4">Legal</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-white">Privacy</a></li>
                <li><a href="#" className="hover:text-white">Terms</a></li>
                <li><a href="#" className="hover:text-white">Security</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm">
            <p>&copy; 2025 HomeView AI. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

