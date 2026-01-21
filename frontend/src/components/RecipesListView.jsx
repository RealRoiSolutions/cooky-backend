import React, { useEffect, useState } from 'react';
import { getRecipes } from '../services/api';
import { Loader, UtensilsCrossed, Clock, Users, Flame } from 'lucide-react';
import ExpiringRecommendations from './ExpiringRecommendations';

export default function RecipesListView({ onSelectRecipe }) {
    const [recipes, setRecipes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchRecipes = async () => {
        try {
            setError(null);
            const res = await getRecipes({ skip: 0, limit: 50, use_user_profile: true });
            setRecipes(res.data.recipes || []);
        } catch (err) {
            console.error("Error fetching recipes:", err);
            setError("No se pudieron cargar las recetas. Verifica la conexión.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchRecipes();
    }, []);

    // Helper to extract kcal from nutrition object
    const getKcal = (nutrition) => {
        if (!nutrition) return null;
        return nutrition.calories || nutrition.kcal || null;
    };

    const getProtein = (nutrition) => {
        if (!nutrition) return null;
        return nutrition.protein || null;
    };

    return (
        <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
            {/* Header */}
            <nav className="bg-white shadow-sm border-b border-slate-100 sticky top-0 z-10">
                <div className="max-w-3xl mx-auto px-4 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="bg-rose-500 p-2 rounded-lg text-white">
                            <UtensilsCrossed size={20} />
                        </div>
                        <h1 className="font-bold text-xl tracking-tight">Cooky<span className="text-rose-500">Recetas</span></h1>
                    </div>
                </div>
            </nav>

            <main className="max-w-3xl mx-auto px-4 py-8">
                {/* Expiring Recommendations Section */}
                <ExpiringRecommendations onSelectRecipe={onSelectRecipe} limit={4} />

                <h2 className="text-lg font-semibold text-slate-700 mb-6">Explora Recetas</h2>

                {loading ? (
                    <div className="flex justify-center p-10">
                        <Loader className="animate-spin text-slate-400" />
                    </div>
                ) : error ? (
                    <div className="text-center py-20 bg-white rounded-2xl border border-dashed border-red-200">
                        <div className="bg-red-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                            <UtensilsCrossed className="text-red-300" size={32} />
                        </div>
                        <h3 className="text-lg font-semibold text-red-700">Error</h3>
                        <p className="text-red-500 mb-4">{error}</p>
                        <button
                            onClick={() => { setLoading(true); fetchRecipes(); }}
                            className="text-rose-600 font-medium hover:underline"
                        >
                            Reintentar
                        </button>
                    </div>
                ) : recipes.length === 0 ? (
                    <div className="text-center py-20 bg-white rounded-2xl border border-dashed border-slate-200">
                        <div className="bg-slate-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                            <UtensilsCrossed className="text-slate-300" size={32} />
                        </div>
                        <h3 className="text-lg font-semibold text-slate-700">No hay recetas</h3>
                        <p className="text-slate-500">Aún no se han importado recetas al sistema.</p>
                    </div>
                ) : (
                    <div className="grid gap-4 sm:grid-cols-2">
                        {recipes.map(recipe => (
                            <div
                                key={recipe.id}
                                onClick={() => onSelectRecipe(recipe.id)}
                                className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden cursor-pointer hover:shadow-md hover:border-rose-100 transition-all group"
                            >
                                {/* Image */}
                                {recipe.image_url ? (
                                    <div className="h-40 overflow-hidden">
                                        <img
                                            src={recipe.image_url}
                                            alt={recipe.title}
                                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                                        />
                                    </div>
                                ) : (
                                    <div className="h-40 bg-gradient-to-br from-rose-100 to-orange-100 flex items-center justify-center">
                                        <UtensilsCrossed className="text-rose-300" size={48} />
                                    </div>
                                )}

                                {/* Content */}
                                <div className="p-4">
                                    <h3 className="font-semibold text-slate-800 text-lg mb-2 line-clamp-2 group-hover:text-rose-600 transition-colors">
                                        {recipe.title}
                                    </h3>

                                    <div className="flex items-center gap-4 text-sm text-slate-500">
                                        {recipe.servings && (
                                            <span className="flex items-center gap-1">
                                                <Users size={14} />
                                                {recipe.servings} rac.
                                            </span>
                                        )}
                                        {getKcal(recipe.nutrition_totals_per_serving) && (
                                            <span className="flex items-center gap-1">
                                                <Flame size={14} className="text-orange-400" />
                                                {Math.round(getKcal(recipe.nutrition_totals_per_serving))} kcal
                                            </span>
                                        )}
                                        {getProtein(recipe.nutrition_totals_per_serving) && (
                                            <span className="flex items-center gap-1 text-emerald-600">
                                                {Math.round(getProtein(recipe.nutrition_totals_per_serving))}g prot
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}
