import React, { useState } from 'react';
import PantryView from './components/PantryView';
import ShoppingListView from './components/ShoppingListView';
import RecipesListView from './components/RecipesListView';
import RecipeDetailView from './components/RecipeDetailView';
import FoodLogView from './components/FoodLogView';
import ProfileView from './components/ProfileView';
import { ChefHat, ShoppingCart, UtensilsCrossed, Calendar, User } from 'lucide-react';

function App() {
  const [activeView, setActiveView] = useState('recipes');
  const [selectedRecipeId, setSelectedRecipeId] = useState(null);

  const handleSelectRecipe = (id) => {
    setSelectedRecipeId(id);
  };

  const handleBackToRecipes = () => {
    setSelectedRecipeId(null);
  };

  const renderContent = () => {
    if (activeView === 'recipes') {
      if (selectedRecipeId) {
        return <RecipeDetailView recipeId={selectedRecipeId} onBack={handleBackToRecipes} />;
      }
      return <RecipesListView onSelectRecipe={handleSelectRecipe} />;
    }
    if (activeView === 'pantry') {
      return <PantryView onSelectRecipe={(id) => { setActiveView('recipes'); handleSelectRecipe(id); }} />;
    }
    if (activeView === 'shopping') {
      return <ShoppingListView />;
    }
    if (activeView === 'foodlog') {
      return <FoodLogView />;
    }
    if (activeView === 'profile') {
      return <ProfileView />;
    }
    return null;
  };

  // Hide bottom nav when viewing recipe detail
  const showBottomNav = !(activeView === 'recipes' && selectedRecipeId);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Main Content with bottom padding for tab bar */}
      <div className={showBottomNav ? 'pb-20' : ''}>
        {renderContent()}
      </div>

      {/* Bottom Tab Navigation */}
      {showBottomNav && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 z-50 shadow-lg">
          <div className="max-w-3xl mx-auto flex">
            <button
              onClick={() => { setActiveView('recipes'); setSelectedRecipeId(null); }}
              className={`flex-1 py-4 flex flex-col items-center gap-1 transition-colors ${activeView === 'recipes'
                ? 'text-rose-500'
                : 'text-slate-400 hover:text-slate-600'
                }`}
            >
              <UtensilsCrossed size={22} />
              <span className="text-xs font-medium">Recetas</span>
            </button>
            <button
              onClick={() => setActiveView('pantry')}
              className={`flex-1 py-4 flex flex-col items-center gap-1 transition-colors ${activeView === 'pantry'
                ? 'text-orange-500'
                : 'text-slate-400 hover:text-slate-600'
                }`}
            >
              <ChefHat size={22} />
              <span className="text-xs font-medium">Despensa</span>
            </button>
            <button
              onClick={() => setActiveView('shopping')}
              className={`flex-1 py-4 flex flex-col items-center gap-1 transition-colors ${activeView === 'shopping'
                ? 'text-emerald-500'
                : 'text-slate-400 hover:text-slate-600'
                }`}
            >
              <ShoppingCart size={22} />
              <span className="text-xs font-medium">Lista</span>
            </button>
            <button
              onClick={() => setActiveView('foodlog')}
              className={`flex-1 py-4 flex flex-col items-center gap-1 transition-colors ${activeView === 'foodlog'
                ? 'text-indigo-500'
                : 'text-slate-400 hover:text-slate-600'
                }`}
            >
              <Calendar size={22} />
              <span className="text-xs font-medium">Diario</span>
            </button>
            <button
              onClick={() => setActiveView('profile')}
              className={`flex-1 py-4 flex flex-col items-center gap-1 transition-colors ${activeView === 'profile'
                ? 'text-violet-500'
                : 'text-slate-400 hover:text-slate-600'
                }`}
            >
              <User size={22} />
              <span className="text-xs font-medium">Perfil</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;


