import React, { useEffect, useState } from 'react';
import { getExpiringRecommendations } from '../services/api';
import { Loader, AlertTriangle, Clock, UtensilsCrossed, ChevronRight } from 'lucide-react';

export default function ExpiringRecommendations({ onSelectRecipe, limit = 5 }) {
    const [recipes, setRecipes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchRecommendations = async () => {
        try {
            setError(null);
            const res = await getExpiringRecommendations({ days: 5, limit });
            setRecipes(res.data || []);
        } catch (err) {
            console.error("Error fetching expiring recommendations:", err);
            setError("No se pudieron cargar las recomendaciones");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchRecommendations();
    }, []);

    if (loading) {
        return (
            <div className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl p-4 border border-amber-200">
                <div className="flex items-center gap-2 mb-3">
                    <AlertTriangle className="text-amber-600" size={20} />
                    <h3 className="font-semibold text-amber-800">Aprovecha lo que caduca pronto</h3>
                </div>
                <div className="flex justify-center py-4">
                    <Loader className="animate-spin text-amber-400" size={24} />
                </div>
            </div>
        );
    }

    if (error || recipes.length === 0) {
        return null; // No mostrar nada si no hay recomendaciones
    }

    return (
        <div className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl p-4 border border-amber-200 mb-6">
            <div className="flex items-center gap-2 mb-4">
                <div className="bg-amber-500 p-1.5 rounded-lg">
                    <AlertTriangle className="text-white" size={18} />
                </div>
                <div>
                    <h3 className="font-semibold text-amber-800">Aprovecha lo que caduca pronto</h3>
                    <p className="text-xs text-amber-600">Recetas que usan ingredientes próximos a caducar</p>
                </div>
            </div>

            <div className="space-y-3">
                {recipes.map(recipe => (
                    <div
                        key={recipe.id}
                        onClick={() => onSelectRecipe && onSelectRecipe(recipe.id)}
                        className="bg-white rounded-lg p-3 border border-amber-100 shadow-sm cursor-pointer hover:shadow-md hover:border-amber-200 transition-all group"
                    >
                        <div className="flex items-start gap-3">
                            {/* Image */}
                            {recipe.image_url ? (
                                <img
                                    src={recipe.image_url}
                                    alt={recipe.title}
                                    className="w-16 h-16 rounded-lg object-cover flex-shrink-0"
                                />
                            ) : (
                                <div className="w-16 h-16 rounded-lg bg-amber-100 flex items-center justify-center flex-shrink-0">
                                    <UtensilsCrossed className="text-amber-400" size={24} />
                                </div>
                            )}

                            {/* Content */}
                            <div className="flex-1 min-w-0">
                                <h4 className="font-medium text-slate-800 text-sm line-clamp-1 group-hover:text-amber-700 transition-colors">
                                    {recipe.title}
                                </h4>

                                {/* Expiring ingredients badges */}
                                <div className="flex flex-wrap gap-1 mt-1.5">
                                    {recipe.expiring_ingredients.slice(0, 3).map((ing, idx) => (
                                        <span
                                            key={idx}
                                            className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full ${ing.days_until_expiry === 0 ? 'bg-red-100 text-red-700' :
                                                    ing.days_until_expiry <= 2 ? 'bg-orange-100 text-orange-700' :
                                                        'bg-amber-100 text-amber-700'
                                                }`}
                                        >
                                            <Clock size={10} />
                                            {ing.ingredient_name_es}
                                            <span className="font-semibold">
                                                {ing.days_until_expiry === 0 ? 'HOY' : `${ing.days_until_expiry}d`}
                                            </span>
                                        </span>
                                    ))}
                                    {recipe.expiring_ingredients.length > 3 && (
                                        <span className="text-xs text-amber-600">
                                            +{recipe.expiring_ingredients.length - 3} más
                                        </span>
                                    )}
                                </div>

                                {/* Stats */}
                                <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                                    <span>
                                        Usa {recipe.expiring_ingredients_count} de {recipe.total_ingredients_count} ingredientes
                                    </span>
                                </div>
                            </div>

                            {/* Arrow */}
                            <ChevronRight className="text-slate-300 group-hover:text-amber-500 transition-colors flex-shrink-0" size={20} />
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
